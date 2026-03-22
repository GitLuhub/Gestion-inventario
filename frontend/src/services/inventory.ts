import { apiClient, getToken } from './api'
import { StockQuant, InventoryAdjustment } from '@/types'

export const inventoryService = {
  getQuants: async (productId?: number, locationId?: number): Promise<StockQuant[]> => {
    const token = getToken()
    const params = new URLSearchParams()
    
    if (productId) params.append('product_id', productId.toString())
    if (locationId) params.append('location_id', locationId.toString())
    
    const queryString = params.toString() ? `?${params.toString()}` : ''
    return apiClient.get<StockQuant[]>(`/api/v1/inventory/quants${queryString}`, { token })
  },
  
  getAdjustments: async (page: number = 1, pageSize: number = 20): Promise<InventoryAdjustment[]> => {
    const token = getToken()
    return apiClient.get<InventoryAdjustment[]>(
      `/api/v1/inventory/adjustments?page=${page}&page_size=${pageSize}`,
      { token }
    )
  },
  
  createAdjustment: async (adjustment: Partial<InventoryAdjustment>): Promise<InventoryAdjustment> => {
    const token = getToken()
    return apiClient.post<InventoryAdjustment>('/api/v1/inventory/adjustments', adjustment, { token })
  },
  
  getStockByLocation: async (locationId: number) => {
    const token = getToken()
    return apiClient.get(`/api/v1/inventory/by-location/${locationId}`, { token })
  },
}
