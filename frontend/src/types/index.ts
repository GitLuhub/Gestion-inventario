export type ProductType = 'product' | 'consumable' | 'service'

export interface Product {
  id: number
  name: string
  default_code?: string
  description?: string
  type: ProductType
  list_price: number
  standard_price: number
  weight?: number
  barcode?: string
  active: boolean
  categ_id?: number
  categ_name?: string
  qty_available: number
  virtual_available: number
  create_date?: string
  write_date?: string
}

export interface ProductListResponse {
  items: Product[]
  total: number
  page: number
  page_size: number
  pages: number
}

export interface Location {
  id: number
  name: string
  complete_name?: string
  usage: string
  location_type: string
  barcode?: string
  parent_id?: number
  child_count: number
}

export interface StockQuant {
  id: number
  product_id: number
  product_name: string
  location_id: number
  location_name: string
  quantity: number
  reserved_quantity: number
  lot_id?: number
  lot_name?: string
}

export interface InventoryAdjustment {
  id: number
  name: string
  date: string
  state: string
  adjustment_type: string
  line_count: number
}

export interface DashboardStats {
  total_products: number
  total_locations: number
  low_stock_products: number
  total_stock_value: number
  recent_adjustments: number
  pending_operations: number
}

export interface TokenResponse {
  access_token: string
  token_type: string
  expires_in: number
  refresh_token?: string
}

export interface User {
  username: string
  user_id: number
}

export interface ApiError {
  detail: string
  status_code?: number
}

export interface PaginationParams {
  page?: number
  page_size?: number
}

export interface ProductFilters extends PaginationParams {
  search?: string
  category_id?: number
  active?: boolean
}

export interface InventoryFilters extends PaginationParams {
  product_id?: number
  location_id?: number
}
