import { apiClient, getToken } from './api'
import { Product, ProductListResponse, ProductFilters } from '@/types'

export const productService = {
  list: async (filters: ProductFilters = {}): Promise<ProductListResponse> => {
    const token = getToken()
    const params = new URLSearchParams()
    
    if (filters.page) params.append('page', filters.page.toString())
    if (filters.page_size) params.append('page_size', filters.page_size.toString())
    if (filters.search) params.append('search', filters.search)
    if (filters.category_id) params.append('category_id', filters.category_id.toString())
    if (filters.active !== undefined) params.append('active', filters.active.toString())
    
    const queryString = params.toString() ? `?${params.toString()}` : ''
    return apiClient.get<ProductListResponse>(`/api/v1/products${queryString}`, { token })
  },
  
  get: async (id: number): Promise<Product> => {
    const token = getToken()
    return apiClient.get<Product>(`/api/v1/products/${id}`, { token })
  },
  
  create: async (product: Partial<Product>): Promise<Product> => {
    const token = getToken()
    return apiClient.post<Product>('/api/v1/products', product, { token })
  },
  
  update: async (id: number, product: Partial<Product>): Promise<Product> => {
    const token = getToken()
    return apiClient.put<Product>(`/api/v1/products/${id}`, product, { token })
  },
  
  delete: async (id: number): Promise<void> => {
    const token = getToken()
    return apiClient.delete(`/api/v1/products/${id}`, { token })
  },
  
  getLowStock: async (limit: number = 10): Promise<Product[]> => {
    const token = getToken()
    return apiClient.get<Product[]>(`/api/v1/products/search/low-stock?limit=${limit}`, { token })
  },
}
