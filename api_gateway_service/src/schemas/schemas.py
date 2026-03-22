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
    access_token: str
    token_type: str = "bearer"
    expires_in: int
    refresh_token: Optional[str] = None


class TokenData(BaseModel):
    username: Optional[str] = None
    user_id: Optional[int] = None


class LoginRequest(BaseModel):
    username: str = Field(..., min_length=1)
    password: str = Field(..., min_length=1)


class ProductBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    default_code: Optional[str] = Field(None, max_length=64)
    description: Optional[str] = None
    type: ProductType = ProductType.PRODUCT
    list_price: float = Field(default=0.0, ge=0)
    standard_price: float = Field(default=0.0, ge=0)
    weight: Optional[float] = Field(default=0.0, ge=0)
    barcode: Optional[str] = None
    active: bool = True
    categ_id: Optional[int] = None


class ProductCreate(ProductBase):
    pass


class ProductUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    list_price: Optional[float] = Field(None, ge=0)
    standard_price: Optional[float] = Field(None, ge=0)
    weight: Optional[float] = Field(None, ge=0)
    active: Optional[bool] = None


class ProductResponse(ProductBase):
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    qty_available: float = 0
    virtual_available: float = 0
    categ_name: Optional[str] = None
    create_date: Optional[datetime] = None
    write_date: Optional[datetime] = None


class ProductListResponse(BaseModel):
    items: List[ProductResponse]
    total: int
    page: int
    page_size: int
    pages: int


class LocationBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    complete_name: Optional[str] = None
    usage: str = "internal"
    location_type: StockLocationType = StockLocationType.BIN
    barcode: Optional[str] = None


class LocationResponse(LocationBase):
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    parent_id: Optional[int] = None
    company_id: Optional[int] = None
    child_count: int = 0


class InventoryAdjustmentBase(BaseModel):
    name: str = Field(..., min_length=1)
    product_id: int
    location_id: int
    quantity: float = Field(..., description="Nueva cantidad de stock")
    adjustment_reason: Optional[str] = "count"
    notes: Optional[str] = None


class InventoryAdjustmentCreate(BaseModel):
    name: str = Field(..., min_length=1)
    lines: List[InventoryAdjustmentBase] = Field(..., min_length=1)


class InventoryAdjustmentResponse(BaseModel):
    id: int
    name: str
    date: datetime
    state: str
    adjustment_type: str
    line_count: int


class StockQuantResponse(BaseModel):
    id: int
    product_id: int
    product_name: str
    location_id: int
    location_name: str
    quantity: float
    reserved_quantity: float
    lot_id: Optional[int] = None
    lot_name: Optional[str] = None


class StockByLocationResponse(BaseModel):
    location_id: int
    location_name: str
    products: List[StockQuantResponse]
    total_quantity: float


class DashboardStats(BaseModel):
    total_products: int
    total_locations: int
    low_stock_products: int
    total_stock_value: float
    recent_adjustments: int
    pending_operations: int


class HealthResponse(BaseModel):
    status: str
    version: str
    odoo_connected: bool
    timestamp: datetime
