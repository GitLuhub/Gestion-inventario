from fastapi import APIRouter, Depends, HTTPException, Query
from typing import List, Optional
from collections import defaultdict
from ..schemas import (
    InventoryAdjustmentCreate,
    InventoryAdjustmentResponse,
    StockQuantResponse,
    StockByLocationResponse,
    DashboardStats,
    LowStockProduct,
    CategoryStats,
    ReportSummaryResponse,
)
from ..utils.auth import get_current_user
from ..utils.odoo_client import get_odoo_client, OdooClient
from datetime import datetime
import logging

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/inventory", tags=["Inventario"])


@router.post("/adjustments", response_model=InventoryAdjustmentResponse, status_code=201)
async def create_adjustment(
    adjustment: InventoryAdjustmentCreate,
    current_user: dict = Depends(get_current_user),
    odoo: OdooClient = Depends(get_odoo_client),
):
    try:
        location_ids = list(set([line.location_id for line in adjustment.lines]))
        inventory_vals = {
            'name': adjustment.name,
            'adjustment_type': 'partial',
            'location_ids': [(6, 0, location_ids)],
        }

        inventory_id = odoo.create('stock.inventory.adjustment', inventory_vals)
        odoo.call_method('stock.inventory.adjustment', 'action_start', [inventory_id])

        for line in adjustment.lines:
            line_vals = {
                'adjustment_id': inventory_id,
                'product_id': line.product_id,
                'location_id': line.location_id,
                'expected_qty': line.quantity,
                'adjustment_reason': line.adjustment_reason,
            }
            odoo.create('stock.inventory.adjustment.line', line_vals)

        odoo.call_method('stock.inventory.adjustment', 'action_validate', [inventory_id])

        logger.info(f"Ajuste de inventario creado: {inventory_id}")

        return InventoryAdjustmentResponse(
            id=inventory_id,
            name=adjustment.name,
            date=datetime.now(),
            state='done',
            adjustment_type='partial',
            line_count=len(adjustment.lines),
        )

    except Exception as e:
        logger.error(f"Error al crear ajuste: {e}")
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/adjustments", response_model=List[InventoryAdjustmentResponse])
async def list_adjustments(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    current_user: dict = Depends(get_current_user),
    odoo: OdooClient = Depends(get_odoo_client),
):
    offset = (page - 1) * page_size

    inventories = odoo.search_read(
        'stock.inventory.adjustment',
        domain=[],
        fields=['id', 'name', 'write_date', 'state', 'adjustment_type'],
        limit=page_size,
        offset=offset,
        order='write_date DESC',
    )

    results = []
    for inv in inventories:
        line_count = odoo.search_count(
            'stock.inventory.adjustment.line',
            [('adjustment_id', '=', inv['id'])],
        )
        results.append(InventoryAdjustmentResponse(
            id=inv['id'],
            name=inv['name'],
            date=inv.get('write_date', datetime.now()),
            state=inv['state'],
            adjustment_type=inv.get('adjustment_type', 'partial'),
            line_count=line_count,
        ))

    return results


@router.get("/quants", response_model=List[StockQuantResponse])
async def list_quants(
    product_id: Optional[int] = None,
    location_id: Optional[int] = None,
    limit: int = Query(100, ge=1, le=500),
    current_user: dict = Depends(get_current_user),
    odoo: OdooClient = Depends(get_odoo_client),
):
    domain = []
    
    if product_id:
        domain.append(('product_id', '=', product_id))
    
    if location_id:
        domain.append(('location_id', '=', location_id))
    
    quants = odoo.search_read(
        'stock.quant',
        domain=domain,
        fields=[
            'id', 'product_id', 'location_id', 'quantity',
            'reserved_quantity', 'lot_id', 'in_date'
        ],
        limit=limit,
    )
    
    product_ids = list(set([q['product_id'][0] for q in quants if q.get('product_id')]))
    location_ids = list(set([q['location_id'][0] for q in quants if q.get('location_id')]))
    
    products = {p['id']: p['name'] for p in odoo.read('product.product', product_ids, ['name'])}
    locations = {l['id']: l['name'] for l in odoo.read('stock.location', location_ids, ['name'])}
    
    results = []
    for q in quants:
        results.append(StockQuantResponse(
            id=q['id'],
            product_id=q['product_id'][0] if q.get('product_id') else 0,
            product_name=products.get(q['product_id'][0] if q.get('product_id') else 0, ''),
            location_id=q['location_id'][0] if q.get('location_id') else 0,
            location_name=locations.get(q['location_id'][0] if q.get('location_id') else 0, ''),
            quantity=q.get('quantity', 0),
            reserved_quantity=q.get('reserved_quantity', 0),
            lot_id=q['lot_id'][0] if q.get('lot_id') else None,
            lot_name=q['lot_id'][1] if q.get('lot_id') else None,
        ))
    
    return results


@router.get("/stats", response_model=DashboardStats)
async def get_inventory_stats(
    current_user: dict = Depends(get_current_user),
    odoo: OdooClient = Depends(get_odoo_client),
):
    """KPIs del dashboard principal — datos reales de Odoo."""
    total_products = odoo.search_count(
        'product.product',
        [('active', '=', True), ('type', 'in', ['product', 'consumable'])],
    )
    total_locations = odoo.search_count(
        'stock.location',
        [('usage', '=', 'internal'), ('active', '=', True)],
    )

    try:
        low_stock = odoo.search_count(
            'product.product',
            [('is_low_stock', '=', True), ('active', '=', True)],
        )
    except Exception:
        low_stock = 0

    products_for_value = odoo.search_read(
        'product.product',
        domain=[('active', '=', True), ('type', 'in', ['product', 'consumable'])],
        fields=['qty_available', 'standard_price'],
        limit=500,
    )
    total_value = sum(
        p.get('qty_available', 0) * p.get('standard_price', 0)
        for p in products_for_value
    )

    recent_adjustments = odoo.search_count(
        'stock.inventory.adjustment',
        [('state', '=', 'done')],
    )
    pending_operations = odoo.search_count(
        'stock.inventory.adjustment',
        [('state', 'in', ['draft', 'in_progress'])],
    )

    return DashboardStats(
        total_products=total_products,
        total_locations=total_locations,
        low_stock_products=low_stock,
        total_stock_value=round(total_value, 2),
        recent_adjustments=recent_adjustments,
        pending_operations=pending_operations,
    )


@router.get("/low-stock", response_model=List[LowStockProduct])
async def list_low_stock_products(
    limit: int = Query(20, ge=1, le=100),
    current_user: dict = Depends(get_current_user),
    odoo: OdooClient = Depends(get_odoo_client),
):
    """Productos con stock por debajo del mínimo definido."""
    try:
        products = odoo.search_read(
            'product.product',
            domain=[('is_low_stock', '=', True), ('active', '=', True)],
            fields=['id', 'name', 'default_code', 'qty_available', 'min_stock_level'],
            limit=limit,
            order='qty_available ASC',
        )
    except Exception:
        products = []

    return [
        LowStockProduct(
            id=p['id'],
            name=p['name'],
            default_code=p.get('default_code') or None,
            qty_available=p.get('qty_available', 0),
            min_stock_level=p.get('min_stock_level', 0),
        )
        for p in products
    ]


@router.get("/reports/summary", response_model=ReportSummaryResponse)
async def get_report_summary(
    current_user: dict = Depends(get_current_user),
    odoo: OdooClient = Depends(get_odoo_client),
):
    """Resumen agregado para la página de reportes."""
    products = odoo.search_read(
        'product.product',
        domain=[('active', '=', True), ('type', 'in', ['product', 'consumable'])],
        fields=['categ_id', 'qty_available', 'standard_price'],
        limit=500,
    )

    total_products = len(products)
    total_value = sum(
        p.get('qty_available', 0) * p.get('standard_price', 0)
        for p in products
    )

    try:
        low_stock_count = odoo.search_count(
            'product.product',
            [('is_low_stock', '=', True), ('active', '=', True)],
        )
    except Exception:
        low_stock_count = 0

    out_of_stock_count = sum(1 for p in products if p.get('qty_available', 0) <= 0)

    total_locations = odoo.search_count(
        'stock.location',
        [('usage', '=', 'internal'), ('active', '=', True)],
    )

    cat_map: dict = defaultdict(lambda: {'name': '', 'count': 0, 'value': 0.0})
    for p in products:
        cat = p.get('categ_id')
        if cat:
            cid, cname = cat[0], cat[1]
            cat_map[cid]['name'] = cname
            cat_map[cid]['count'] += 1
            cat_map[cid]['value'] += p.get('qty_available', 0) * p.get('standard_price', 0)

    top_categories = sorted(
        [
            CategoryStats(id=cid, name=v['name'], product_count=v['count'], total_value=round(v['value'], 2))
            for cid, v in cat_map.items()
        ],
        key=lambda c: c.total_value,
        reverse=True,
    )[:8]

    return ReportSummaryResponse(
        total_products=total_products,
        total_locations=total_locations,
        low_stock_count=low_stock_count,
        out_of_stock_count=out_of_stock_count,
        total_stock_value=round(total_value, 2),
        top_categories=top_categories,
    )


@router.get("/by-location/{location_id}", response_model=StockByLocationResponse)
async def get_stock_by_location(
    location_id: int,
    current_user: dict = Depends(get_current_user),
    odoo: OdooClient = Depends(get_odoo_client),
):
    location = odoo.read('stock.location', [location_id])
    if not location:
        raise HTTPException(status_code=404, detail="Ubicación no encontrada")
    
    quants = odoo.search_read(
        'stock.quant',
        domain=[('location_id', '=', location_id)],
        fields=['id', 'product_id', 'quantity', 'reserved_quantity', 'lot_id'],
        limit=500,
    )
    
    product_ids = list(set([q['product_id'][0] for q in quants if q.get('product_id')]))
    products = {p['id']: p['name'] for p in odoo.read('product.product', product_ids, ['name'])}
    
    total_qty = sum(q.get('quantity', 0) for q in quants)
    
    return StockByLocationResponse(
        location_id=location_id,
        location_name=location[0]['name'],
        products=[
            StockQuantResponse(
                id=q['id'],
                product_id=q['product_id'][0] if q.get('product_id') else 0,
                product_name=products.get(q['product_id'][0] if q.get('product_id') else 0, ''),
                location_id=location_id,
                location_name=location[0]['name'],
                quantity=q.get('quantity', 0),
                reserved_quantity=q.get('reserved_quantity', 0),
                lot_id=q['lot_id'][0] if q.get('lot_id') else None,
                lot_name=q['lot_id'][1] if q.get('lot_id') else None,
            )
            for q in quants
        ],
        total_quantity=total_qty,
    )
