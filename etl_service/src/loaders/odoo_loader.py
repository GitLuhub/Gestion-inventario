import xmlrpc.client
from typing import Dict, Any, Optional, List
from tenacity import retry, stop_after_attempt, wait_exponential
from utils.logger_util import get_logger
from config import Config


class OdooLoader:
    def __init__(self, url: str = None, db: str = None, 
                 user: str = None, password: str = None):
        self.url = url or Config.ODOO_URL
        self.db = db or Config.ODOO_DB
        self.user = user or Config.ODOO_USER
        self.password = password or Config.ODOO_PASSWORD
        
        self.logger = get_logger('OdooLoader')
        self.uid = None
        
        self.common = None
        self.models = None
        
        self._connect()
    
    def _connect(self):
        try:
            self.common = xmlrpc.client.ServerProxy(f'{self.url}/xmlrpc/2/common')
            self.models = xmlrpc.client.ServerProxy(f'{self.url}/xmlrpc/2/object')
            
            self.uid = self.common.authenticate(self.db, self.user, self.password, {})
            
            if not self.uid:
                raise Exception("Autenticación fallida")
            
            self.logger.info(f"Conectado a Odoo (UID: {self.uid})")
            
        except Exception as e:
            self.logger.error(f"Error al conectar a Odoo: {e}")
            raise
    
    def _execute(self, model: str, method: str, *args, **kwargs) -> Any:
        try:
            return self.models.execute_kw(
                self.db, self.uid, self.password,
                model, method, args, kwargs
            )
        except xmlrpc.client.Fault as e:
            self.logger.error(f"Error XML-RPC: {e.faultCode} - {e.faultString}")
            raise
        except Exception as e:
            self.logger.error(f"Error en _execute: {e}")
            raise
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10)
    )
    def search_record(self, model: str, domain: List) -> List[int]:
        return self._execute(model, 'search', domain)
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10)
    )
    def read_record(self, model: str, ids: List[int], fields: List[str]) -> List[Dict]:
        if not ids:
            return []
        return self._execute(model, 'read', ids, fields=fields)
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10)
    )
    def create_record(self, model: str, values: Dict[str, Any]) -> int:
        return self._execute(model, 'create', values)
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10)
    )
    def write_record(self, model: str, ids: List[int], values: Dict[str, Any]) -> bool:
        return self._execute(model, 'write', ids, values)
    
    def get_product_by_sku(self, sku: str) -> Optional[Dict[str, Any]]:
        if not sku:
            return None
        
        product_ids = self.search_record(
            'product.product', 
            [('default_code', '=', sku)]
        )
        
        if product_ids:
            products = self.read_record('product.product', product_ids, [
                'id', 'name', 'default_code', 'type', 'list_price', 
                'standard_price', 'active', 'categ_id'
            ])
            return products[0] if products else None
        
        return None
    
    def get_category_by_name(self, name: str) -> Optional[int]:
        if not name:
            return None
        
        category_ids = self.search_record(
            'product.category', 
            [('name', '=', name)]
        )
        
        return category_ids[0] if category_ids else None
    
    def create_category(self, name: str) -> int:
        category_id = self.get_category_by_name(name)
        if category_id:
            return category_id
        
        return self.create_record('product.category', {'name': name})
    
    def create_or_update_product(self, product_data: Dict[str, Any]) -> int:
        sku = product_data.get('default_code')
        
        existing = self.get_product_by_sku(sku)
        
        product_vals = {
            'name': product_data.get('name'),
            'default_code': sku,
            'type': product_data.get('type', 'product'),
            'list_price': product_data.get('list_price', 0),
            'standard_price': product_data.get('standard_price', 0),
            'active': product_data.get('active', True),
        }
        
        if product_data.get('description'):
            product_vals['description'] = product_data['description']
        
        if product_data.get('barcode'):
            product_vals['barcode'] = product_data['barcode']
        
        if product_data.get('categ_name'):
            category_id = self.create_category(product_data['categ_name'])
            product_vals['categ_id'] = category_id
        
        if existing:
            self.write_record('product.product', [existing['id']], product_vals)
            self.logger.debug(f"Producto actualizado: {sku}")
            return existing['id']
        else:
            new_id = self.create_record('product.product', product_vals)
            self.logger.debug(f"Producto creado: {sku}")
            return new_id
    
    def get_location_by_name(self, name: str) -> Optional[int]:
        if not name:
            return None
        
        location_ids = self.search_record(
            'stock.location', 
            [('complete_name', 'ilike', name)]
        )
        
        if not location_ids:
            location_ids = self.search_record(
                'stock.location', 
                [('name', '=', name)]
            )
        
        return location_ids[0] if location_ids else None
    
    def adjust_inventory(
        self,
        product_id: int,
        location_id: int,
        quantity: float,
        lot_name: str = None,
        expiration_date: str = None
    ) -> bool:
        """Ajusta el inventario en Odoo 16 usando stock.quant directamente.

        En Odoo 16, stock.inventory y stock.inventory.line fueron eliminados.
        El flujo correcto es: escribir inventory_quantity en stock.quant
        y luego llamar action_apply_inventory().
        """
        try:
            domain = [
                ('product_id', '=', product_id),
                ('location_id', '=', location_id),
            ]

            lot_id = None
            if lot_name:
                lot_id = self._get_or_create_lot(product_id, lot_name, expiration_date)
                if lot_id:
                    domain.append(('lot_id', '=', lot_id))

            quant_ids = self.search_record('stock.quant', domain)

            if quant_ids:
                self.write_record('stock.quant', quant_ids,
                                  {'inventory_quantity': quantity})
            else:
                quant_vals = {
                    'product_id': product_id,
                    'location_id': location_id,
                    'inventory_quantity': quantity,
                }
                if lot_id:
                    quant_vals['lot_id'] = lot_id
                quant_ids = [self.create_record('stock.quant', quant_vals)]

            self._execute('stock.quant', 'action_apply_inventory', quant_ids)

            self.logger.info(
                f"Ajuste aplicado: Producto {product_id}, "
                f"Ubicación {location_id}, Cantidad {quantity}"
            )
            return True

        except Exception as e:
            self.logger.error(f"Error al ajustar inventario: {e}")
            return False
    
    def _get_or_create_lot(
        self, 
        product_id: int, 
        lot_name: str,
        expiration_date: str = None
    ) -> Optional[int]:
        # En Odoo 16 el modelo es stock.lot (antes stock.production.lot)
        lot_ids = self.search_record(
            'stock.lot',
            [('name', '=', lot_name), ('product_id', '=', product_id)]
        )

        if lot_ids:
            return lot_ids[0]

        lot_vals = {
            'name': lot_name,
            'product_id': product_id,
        }

        if expiration_date:
            lot_vals['expiration_date'] = expiration_date

        return self.create_record('stock.lot', lot_vals)
    
    def test_connection(self) -> bool:
        try:
            version = self.common.version()
            self.logger.info(f"Odoo version: {version}")
            return True
        except Exception as e:
            self.logger.error(f"Error en test_connection: {e}")
            return False
