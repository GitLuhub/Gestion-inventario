import useSWR from 'swr'
import { Product, ProductListResponse, ProductFilters } from '@/types'
import { productService } from '@/services/products'

export function useProducts(filters: ProductFilters = {}) {
  const { data, error, isLoading, mutate } = useSWR<ProductListResponse>(
    ['products', filters],
    () => productService.list(filters),
    {
      revalidateOnFocus: false,
      dedupingInterval: 5000,
    }
  )

  return {
    products: data?.items ?? [],
    total: data?.total ?? 0,
    pages: data?.pages ?? 1,
    isLoading,
    isError: error,
    mutate,
  }
}

export function useProduct(id: number | string) {
  const { data, error, isLoading, mutate } = useSWR<Product>(
    id ? ['product', id] : null,
    () => productService.get(Number(id)),
    {
      revalidateOnFocus: false,
    }
  )

  return {
    product: data,
    isLoading,
    isError: error,
    mutate,
  }
}

export function useLowStockProducts(limit: number = 10) {
  const { data, error, isLoading } = useSWR<Product[]>(
    ['low-stock-products', limit],
    () => productService.getLowStock(limit),
    {
      revalidateOnFocus: false,
      dedupingInterval: 5000,
    }
  )

  return {
    products: data ?? [],
    isLoading,
    isError: error,
  }
}
