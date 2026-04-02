from fastapi import APIRouter, Depends, HTTPException, Query
from typing import List, Optional
from ..schemas import (
    ProductCreate,
    ProductUpdate,
    ProductResponse,
    ProductListResponse,
)
from ..utils.auth import get_current_user
from ..utils.odoo_client import get_odoo_client, OdooClient
import logging

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/products", tags=["Productos"])


def _odoo_str(value) -> str | None:
    """Odoo devuelve False en campos Char/Text vacíos — convertir a None."""
    return value if isinstance(value, str) else None


def _map_product_to_response(product: dict) -> dict:
    return {
        'id': product.get('id'),
        'name': product.get('name'),
        'default_code': _odoo_str(product.get('default_code')),
        'description': _odoo_str(product.get('description')),
        'type': product.get('type', 'product'),
        'list_price': product.get('list_price', 0),
        'standard_price': product.get('standard_price', 0),
        'weight': product.get('weight', 0),
        'barcode': _odoo_str(product.get('barcode')),
        'active': product.get('active', True),
        'categ_id': product.get('categ_id', [0])[0] if product.get('categ_id') else None,
        'qty_available': product.get('qty_available', 0),
        'virtual_available': product.get('virtual_available', 0),
        'categ_name': product.get('categ_id', [''])[1] if product.get('categ_id') else None,
        'create_date': _odoo_str(product.get('create_date')),
        'write_date': _odoo_str(product.get('write_date')),
    }


@router.get("", response_model=ProductListResponse)
async def list_products(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    search: Optional[str] = None,
    category_id: Optional[int] = None,
    active: Optional[bool] = True,
    current_user: dict = Depends(get_current_user),
    odoo: OdooClient = Depends(get_odoo_client),
):
    domain = [('type', '!=', 'service')]
    
    if active is not None:
        domain.append(('active', '=', active))
    
    if search:
        domain.append('|')
        domain.append(('name', 'ilike', search))
        domain.append(('default_code', 'ilike', search))
    
    if category_id:
        domain.append(('categ_id', '=', category_id))
    
    total = odoo.search_count('product.product', domain)
    
    offset = (page - 1) * page_size
    products = odoo.search_read(
        'product.product',
        domain=domain,
        fields=[
            'id', 'name', 'default_code', 'description', 'type',
            'list_price', 'standard_price', 'weight', 'barcode',
            'active', 'categ_id', 'qty_available', 'virtual_available',
            'create_date', 'write_date'
        ],
        limit=page_size,
        offset=offset,
        order='name ASC'
    )
    
    items = [_map_product_to_response(p) for p in products]
    pages = (total + page_size - 1) // page_size if page_size > 0 else 0
    
    return ProductListResponse(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
        pages=pages,
    )


@router.get("/{product_id}", response_model=ProductResponse)
async def get_product(
    product_id: int,
    current_user: dict = Depends(get_current_user),
    odoo: OdooClient = Depends(get_odoo_client),
):
    products = odoo.read('product.product', [product_id])
    
    if not products:
        raise HTTPException(status_code=404, detail="Producto no encontrado")
    
    return _map_product_to_response(products[0])


@router.post("", response_model=ProductResponse, status_code=201)
async def create_product(
    product: ProductCreate,
    current_user: dict = Depends(get_current_user),
    odoo: OdooClient = Depends(get_odoo_client),
):
    values = {
        'name': product.name,
        'default_code': product.default_code,
        'description': product.description,
        'type': product.type.value,
        'list_price': product.list_price,
        'standard_price': product.standard_price,
        'weight': product.weight,
        'barcode': product.barcode,
        'active': product.active,
    }
    
    if product.categ_id:
        values['categ_id'] = product.categ_id
    
    try:
        product_id = odoo.create('product.product', values)
        products = odoo.read('product.product', [product_id])
        
        logger.info(f"Producto creado: {product_id}")
        return _map_product_to_response(products[0])
        
    except Exception as e:
        logger.error(f"Error al crear producto: {e}")
        raise HTTPException(status_code=400, detail=str(e))


@router.put("/{product_id}", response_model=ProductResponse)
async def update_product(
    product_id: int,
    product: ProductUpdate,
    current_user: dict = Depends(get_current_user),
    odoo: OdooClient = Depends(get_odoo_client),
):
    existing = odoo.read('product.product', [product_id])
    if not existing:
        raise HTTPException(status_code=404, detail="Producto no encontrado")
    
    values = {k: v for k, v in product.model_dump().items() if v is not None}
    
    if 'type' in values:
        values['type'] = values['type'].value if hasattr(values['type'], 'value') else values['type']
    
    if values:
        try:
            odoo.write('product.product', [product_id], values)
            logger.info(f"Producto actualizado: {product_id}")
        except Exception as e:
            logger.error(f"Error al actualizar producto: {e}")
            raise HTTPException(status_code=400, detail=str(e))
    
    products = odoo.read('product.product', [product_id])
    return _map_product_to_response(products[0])


@router.delete("/{product_id}", status_code=204)
async def delete_product(
    product_id: int,
    current_user: dict = Depends(get_current_user),
    odoo: OdooClient = Depends(get_odoo_client),
):
    existing = odoo.read('product.product', [product_id])
    if not existing:
        raise HTTPException(status_code=404, detail="Producto no encontrado")
    
    try:
        odoo.write('product.product', [product_id], {'active': False})
        logger.info(f"Producto desactivado: {product_id}")
    except Exception as e:
        logger.error(f"Error al eliminar producto: {e}")
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/search/low-stock")
async def get_low_stock_products(
    limit: int = Query(10, ge=1, le=100),
    current_user: dict = Depends(get_current_user),
    odoo: OdooClient = Depends(get_odoo_client),
):
    domain = [
        ('type', '=', 'product'),
        ('active', '=', True),
        ('qty_available', '<=', 10),
    ]
    
    products = odoo.search_read(
        'product.product',
        domain=domain,
        fields=['id', 'name', 'default_code', 'qty_available', 'min_stock_level'],
        limit=limit,
        order='qty_available ASC'
    )
    
    return [p for p in products]
