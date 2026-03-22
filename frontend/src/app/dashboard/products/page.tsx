'use client'

import { useState } from 'react'
import { useRouter } from 'next/navigation'
import { Table, Pagination } from '@/components/ui/Table'
import { Input } from '@/components/ui/Input'
import { Button } from '@/components/ui/Button'
import { Card, CardBody } from '@/components/ui/Card'
import { ConfirmDialog } from '@/components/ui/Modal'
import { useProducts } from '@/hooks'
import { productService } from '@/services/products'
import { Product } from '@/types'
import { PlusIcon, PencilIcon, TrashIcon, CubeIcon, MagnifyingGlassIcon } from '@heroicons/react/24/outline'
import toast from 'react-hot-toast'

export default function ProductsPage() {
  const router = useRouter()
  const [page, setPage] = useState(1)
  const [search, setSearch] = useState('')
  const [deleteProduct, setDeleteProduct] = useState<Product | null>(null)
  const [isDeleting, setIsDeleting] = useState(false)

  const { products, total, pages, isLoading, mutate } = useProducts({
    page,
    page_size: 10,
    search: search || undefined,
  })

  const handleDelete = async () => {
    if (!deleteProduct) return
    setIsDeleting(true)
    try {
      await productService.delete(deleteProduct.id)
      mutate()
      toast.success('Producto eliminado correctamente')
    } catch {
      toast.error('Error al eliminar el producto')
    } finally {
      setIsDeleting(false)
      setDeleteProduct(null)
    }
  }

  const columns = [
    {
      key: 'name',
      header: 'Producto',
      render: (item: Product) => (
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-lg bg-primary-100 flex items-center justify-center">
            <CubeIcon className="w-5 h-5 text-primary-600" />
          </div>
          <div>
            <p className="font-medium text-gray-900">{item.name}</p>
            <p className="text-sm text-gray-500">{item.default_code || 'Sin código'}</p>
          </div>
        </div>
      ),
    },
    {
      key: 'type',
      header: 'Tipo',
      render: (item: Product) => (
        <span className="px-2 py-1 text-xs rounded-full bg-gray-100 text-gray-700 capitalize">
          {item.type === 'product' ? 'Producto' : item.type === 'consumable' ? 'Consumible' : 'Servicio'}
        </span>
      ),
    },
    {
      key: 'list_price',
      header: 'Precio Venta',
      render: (item: Product) => `$${item.list_price.toLocaleString('es-CO')}`,
    },
    {
      key: 'qty_available',
      header: 'Stock',
      render: (item: Product) => (
        <span className={item.qty_available < 10 ? 'text-danger-600 font-medium' : ''}>
          {item.qty_available} unidades
        </span>
      ),
    },
    {
      key: 'actions',
      header: 'Acciones',
      render: (item: Product) => (
        <div className="flex gap-2">
          <button
            onClick={(e) => {
              e.stopPropagation()
              router.push(`/products/${item.id}`)
            }}
            className="p-2 text-gray-500 hover:text-primary-600 hover:bg-gray-100 rounded-lg transition-colors"
          >
            <PencilIcon className="w-4 h-4" />
          </button>
          <button
            onClick={(e) => {
              e.stopPropagation()
              setDeleteProduct(item)
            }}
            className="p-2 text-gray-500 hover:text-danger-600 hover:bg-gray-100 rounded-lg transition-colors"
          >
            <TrashIcon className="w-4 h-4" />
          </button>
        </div>
      ),
    },
  ]

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Productos</h1>
          <p className="text-gray-600 mt-1">{total} productos en el sistema</p>
        </div>
        <Button onClick={() => router.push('/products/new')}>
          <PlusIcon className="w-5 h-5 mr-2" />
          Nuevo Producto
        </Button>
      </div>

      <Card>
        <CardBody>
          <div className="flex gap-4 mb-6">
            <div className="flex-1">
              <Input
                placeholder="Buscar por nombre o código..."
                value={search}
                onChange={(e) => {
                  setSearch(e.target.value)
                  setPage(1)
                }}
              />
            </div>
            <Button variant="outline" onClick={() => setPage(1)}>
              <MagnifyingGlassIcon className="w-5 h-5" />
            </Button>
          </div>

          <Table
            data={products}
            columns={columns}
            keyExtractor={(item) => item.id}
            onRowClick={(item) => router.push(`/products/${item.id}`)}
            isLoading={isLoading}
            emptyMessage="No hay productos que mostrar"
          />

          {pages > 1 && (
            <Pagination
              currentPage={page}
              totalPages={pages}
              onPageChange={setPage}
            />
          )}
        </CardBody>
      </Card>

      <ConfirmDialog
        isOpen={!!deleteProduct}
        onClose={() => setDeleteProduct(null)}
        onConfirm={handleDelete}
        title="Eliminar Producto"
        message={`¿Estás seguro de eliminar "${deleteProduct?.name}"? Esta acción no se puede deshacer.`}
        confirmText="Eliminar"
        variant="danger"
        isLoading={isDeleting}
      />
    </div>
  )
}
