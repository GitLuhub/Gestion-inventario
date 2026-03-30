"""
schemas.py — Modelos Pydantic con ejemplos para Swagger enriquecido (J5 / GAP-18)

Cada campo usa Field(..., example=...) para que FastAPI genere ejemplos reales
en /docs (Swagger UI) y /redoc. Mejora la experiencia del desarrollador y del
reclutador técnico que evalúa el proyecto.
"""

from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List
from datetime import datetime
from enum import Enum


class ProductType(str, Enum):
    PRODUCT = "product"
    CONSUMABLE = "consumable"
    SERVICE = "service"


class StockLocationType(str, Enum):
    WAREHOUSE = "warehouse"
    ZONE = "zone"
    AISLE = "aisle"
    RACK = "rack"
    SHELF = "shelf"
    BIN = "bin"


class AdjustmentType(str, Enum):
    FULL = "full"
    PARTIAL = "partial"
    CYCLIC = "cyclic"


class TokenResponse(BaseModel):
    access_token: str = Field(..., example="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...")
    token_type: str = Field("bearer", example="bearer")
    expires_in: int = Field(..., example=1800, description="Segundos hasta expiración")
    refresh_token: Optional[str] = Field(
        None,
        example=None,
        description="Null — el refresh token se entrega en cookie httpOnly",
    )


class TokenData(BaseModel):
    username: Optional[str] = Field(None, example="admin")
    user_id: Optional[int] = Field(None, example=1)


class LoginRequest(BaseModel):
    username: str = Field(..., min_length=1, example="admin")
    password: str = Field(..., min_length=1, example="admin")


class ProductBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=255, example="Laptop HP EliteBook 840")
    default_code: Optional[str] = Field(None, max_length=64, example="LAP-HP-840")
    description: Optional[str] = Field(None, example="Laptop empresarial con procesador Intel i7")
    type: ProductType = Field(ProductType.PRODUCT, example="product")
    list_price: float = Field(default=0.0, ge=0, example=1299.99)
    standard_price: float = Field(default=0.0, ge=0, example=950.00)
    weight: Optional[float] = Field(default=0.0, ge=0, example=1.8)
    barcode: Optional[str] = Field(None, example="7891234567890")
    active: bool = Field(True, example=True)
    categ_id: Optional[int] = Field(None, example=5)


class ProductCreate(ProductBase):
    min_stock_level: float = Field(0.0, ge=0, example=5.0,
                                   description="Stock mínimo antes de generar alerta")
    max_stock_level: float = Field(0.0, ge=0, example=50.0,
                                   description="Stock máximo recomendado")
    brand_id: Optional[int] = Field(None, example=1, description="ID de la marca del producto")


class ProductUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=255, example="Laptop HP EliteBook 845")
    description: Optional[str] = Field(None, example="Descripción actualizada")
    list_price: Optional[float] = Field(None, ge=0, example=1199.99)
    standard_price: Optional[float] = Field(None, ge=0, example=880.00)
    weight: Optional[float] = Field(None, ge=0, example=1.7)
    active: Optional[bool] = Field(None, example=True)


class ProductResponse(ProductBase):
    model_config = ConfigDict(from_attributes=True)

    id: int = Field(..., example=42)
    qty_available: float = Field(0, example=12.0)
    virtual_available: float = Field(0, example=10.0)
    categ_name: Optional[str] = Field(None, example="Electrónica / Laptops")
    create_date: Optional[datetime] = None
    write_date: Optional[datetime] = None


class ProductListResponse(BaseModel):
    items: List[ProductResponse]
    total: int = Field(..., example=150)
    page: int = Field(..., example=1)
    page_size: int = Field(..., example=20)
    pages: int = Field(..., example=8)


class LocationBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=255, example="Estantería A-3")
    complete_name: Optional[str] = Field(None, example="Almacén Principal / Zona A / Estantería A-3")
    usage: str = Field("internal", example="internal")
    location_type: StockLocationType = Field(StockLocationType.SHELF, example="shelf")
    barcode: Optional[str] = Field(None, example="LOC-A3-001")


class LocationResponse(LocationBase):
    model_config = ConfigDict(from_attributes=True)

    id: int = Field(..., example=8)
    parent_id: Optional[int] = Field(None, example=3)
    company_id: Optional[int] = Field(None, example=1)
    child_count: int = Field(0, example=0)


class InventoryAdjustmentBase(BaseModel):
    name: str = Field(..., min_length=1, example="Ajuste Enero 2026")
    product_id: int = Field(..., example=42)
    location_id: int = Field(..., example=8)
    quantity: float = Field(..., example=15.0, description="Nueva cantidad de stock")
    adjustment_reason: Optional[str] = Field("count", example="count")
    notes: Optional[str] = Field(None, example="Conteo físico mensual")


class InventoryAdjustmentCreate(BaseModel):
    name: str = Field(..., min_length=1, example="Ajuste Mensual Enero 2026")
    lines: List[InventoryAdjustmentBase] = Field(..., min_length=1)


class InventoryAdjustmentResponse(BaseModel):
    id: int = Field(..., example=7)
    name: str = Field(..., example="ADJ/00007")
    date: datetime
    state: str = Field(..., example="done")
    adjustment_type: str = Field(..., example="partial")
    line_count: int = Field(..., example=5)


class StockQuantResponse(BaseModel):
    id: int = Field(..., example=21)
    product_id: int = Field(..., example=42)
    product_name: str = Field(..., example="Laptop HP EliteBook 840")
    location_id: int = Field(..., example=8)
    location_name: str = Field(..., example="Estantería A-3")
    quantity: float = Field(..., example=12.0)
    reserved_quantity: float = Field(..., example=2.0)
    lot_id: Optional[int] = Field(None, example=None)
    lot_name: Optional[str] = Field(None, example=None)


class StockByLocationResponse(BaseModel):
    location_id: int = Field(..., example=8)
    location_name: str = Field(..., example="Estantería A-3")
    products: List[StockQuantResponse]
    total_quantity: float = Field(..., example=47.0)


class DashboardStats(BaseModel):
    total_products: int = Field(..., example=150)
    total_locations: int = Field(..., example=12)
    low_stock_products: int = Field(..., example=3)
    total_stock_value: float = Field(..., example=48750.00)
    recent_adjustments: int = Field(..., example=7)
    pending_operations: int = Field(..., example=2)


class HealthResponse(BaseModel):
    status: str = Field(..., example="healthy")
    version: str = Field(..., example="1.0.0")
    odoo_connected: bool = Field(..., example=True)
    timestamp: datetime
