import xmlrpc.client
from typing import List, Dict, Any, Optional
from tenacity import retry, stop_after_attempt, wait_exponential
from ..config import settings
from .logger import get_logger

# request_id flows automatically into logs via the JsonFormatter ContextVar.
logger = get_logger(__name__)


class OdooClient:
    def __init__(self):
        self.url = settings.ODOO_URL
        self.db = settings.ODOO_DB
        self.user = settings.ODOO_USER
        self.password = settings.odoo_password_from_file
        self.uid = None
        self.common = None
        self.models = None
        self._connect()
    
    def _connect(self):
        try:
            self.common = xmlrpc.client.ServerProxy(f'{self.url}/xmlrpc/2/common')
            self.models = xmlrpc.client.ServerProxy(f'{self.url}/xmlrpc/2/object')
            
            self.uid = self.common.authenticate(
                self.db, 
                self.user, 
                self.password, 
                {}
            )
            
            if not self.uid:
                logger.warning("odoo_auth_no_uid")

            logger.info("odoo_connected", extra={"uid": self.uid})

        except Exception as e:
            logger.error("odoo_connect_error", extra={"error": str(e)})
            raise
    
    def _execute(self, model: str, method: str, *args, **kwargs) -> Any:
        try:
            return self.models.execute_kw(
                self.db, self.uid, self.password,
                model, method, args, kwargs
            )
        except xmlrpc.client.Fault as e:
            logger.error("odoo_xmlrpc_fault", extra={"fault_code": e.faultCode, "fault_string": e.faultString})
            raise
        except Exception as e:
            logger.error("odoo_execute_error", extra={"error": str(e)})
            raise
    
    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2))
    def search_read(
        self, 
        model: str, 
        domain: List = None,
        fields: List[str] = None,
        limit: int = 100,
        offset: int = 0,
        order: str = None
    ) -> List[Dict]:
        domain = domain or []
        fields = fields or []
        
        if fields:
            result = self._execute(
                model, 'search_read',
                domain,
                {'fields': fields, 'limit': limit, 'offset': offset, 'order': order}
            )
        else:
            ids = self._execute(model, 'search', domain, {'limit': limit, 'offset': offset})
            if ids:
                result = self._execute(model, 'read', ids)
            else:
                result = []
        
        return result
    
    def create(self, model: str, values: Dict[str, Any]) -> int:
        return self._execute(model, 'create', values)
    
    def write(self, model: str, ids: List[int], values: Dict[str, Any]) -> bool:
        return self._execute(model, 'write', ids, values)
    
    def unlink(self, model: str, ids: List[int]) -> bool:
        return self._execute(model, 'unlink', ids)
    
    def search_count(self, model: str, domain: List = None) -> int:
        domain = domain or []
        ids = self._execute(model, 'search', domain)
        return len(ids) if ids else 0
    
    def search(self, model: str, domain: List = None, limit: int = None) -> List[int]:
        domain = domain or []
        return self._execute(model, 'search', domain, {'limit': limit})
    
    def read(self, model: str, ids: List[int], fields: List[str] = None) -> List[Dict]:
        fields = fields or []
        if not ids:
            return []
        return self._execute(model, 'read', ids, {'fields': fields})
    
    def call_method(self, model: str, method: str, *args, **kwargs) -> Any:
        return self._execute(model, method, args, kwargs)
    
    def test_connection(self) -> bool:
        try:
            version = self.common.version()
            return True
        except Exception as e:
            logger.error("odoo_test_connection_error", extra={"error": str(e)})
            return False


odoo_client = OdooClient()


def get_odoo_client() -> OdooClient:
    return odoo_client
