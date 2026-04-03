import useSWR from 'swr'
import { DashboardStats, StockQuant, InventoryAdjustment, LowStockProduct, ReportSummary } from '@/types'
import { inventoryService } from '@/services/inventory'

export function useInventoryStats() {
  const { data, error, isLoading } = useSWR<DashboardStats>(
    'inventory-stats',
    () => inventoryService.getStats(),
    { revalidateOnFocus: false, dedupingInterval: 30000 }
  )
  return { stats: data, isLoading, isError: error }
}

export function useInventoryQuants(productId?: number, locationId?: number) {
  const key = ['inventory-quants', productId, locationId]
  const { data, error, isLoading, mutate } = useSWR<StockQuant[]>(
    key,
    () => inventoryService.getQuants(productId, locationId),
    { revalidateOnFocus: false, dedupingInterval: 10000 }
  )
  return { quants: data ?? [], isLoading, isError: error, mutate }
}

export function useInventoryAdjustments(page: number = 1, pageSize: number = 20) {
  const { data, error, isLoading, mutate } = useSWR<InventoryAdjustment[]>(
    ['inventory-adjustments', page, pageSize],
    () => inventoryService.getAdjustments(page, pageSize),
    { revalidateOnFocus: false, dedupingInterval: 10000 }
  )
  return { adjustments: data ?? [], isLoading, isError: error, mutate }
}

export function useLowStockInventory(limit: number = 20) {
  const { data, error, isLoading } = useSWR<LowStockProduct[]>(
    ['inventory-low-stock', limit],
    () => inventoryService.getLowStock(limit),
    { revalidateOnFocus: false, dedupingInterval: 30000 }
  )
  return { products: data ?? [], isLoading, isError: error }
}

export function useReportSummary() {
  const { data, error, isLoading } = useSWR<ReportSummary>(
    'report-summary',
    () => inventoryService.getReportSummary(),
    { revalidateOnFocus: false, dedupingInterval: 30000 }
  )
  return { summary: data, isLoading, isError: error }
}
