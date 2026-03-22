'use client'

import { useState } from 'react'
import { useRouter, useParams } from 'next/navigation'
import { useForm } from 'react-hook-form'
import { Card, CardBody, CardHeader } from '@/components/ui/Card'
import { Input } from '@/components/ui/Input'
import { Select } from '@/components/ui/Input'
import { Button } from '@/components/ui/Button'
import { useProduct } from '@/hooks'
import { productService } from '@/services/products'
import { Product, ProductType } from '@/types'
import { ArrowLeftIcon } from '@heroicons/react/24/outline'
import toast from 'react-hot-toast'

type ProductFormData = {
  name: string
  default_code?: string
  description?: string
  type: ProductType
  list_price: number
  standard_price: number
  weight?: number
  barcode?: string
  categ_id?: number
}

export default function EditProductPage() {
  const router = useRouter()
  const params = useParams()
  const id = params.id as string
  const { product, isLoading, isError } = useProduct(id)
  const [isSubmitting, setIsSubmitting] = useState(false)

  const { register, handleSubmit, formState: { errors }, reset } = useForm<ProductFormData>({
    defaultValues: {
      type: 'product',
      list_price: 0,
      standard_price: 0,
    },
  })

  useState(() => {
    if (product) {
      reset({
        name: product.name,
        default_code: product.default_code,
        description: product.description,
        type: product.type,
        list_price: product.list_price,
        standard_price: product.standard_price,
        weight: product.weight,
        barcode: product.barcode,
      })
    }
  })

  const onSubmit = async (data: ProductFormData) => {
    setIsSubmitting(true)
    try {
      await productService.update(Number(id), data as Partial<Product>)
      toast.success('Producto actualizado correctamente')
      router.push('/dashboard/products')
    } catch {
      toast.error('Error al actualizar el producto')
    } finally {
      setIsSubmitting(false)
    }
  }

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary-600" />
      </div>
    )
  }

  if (isError || !product) {
    return (
      <div className="text-center py-12">
        <p className="text-gray-500">Producto no encontrado</p>
        <Button variant="secondary" onClick={() => router.push('/dashboard/products')} className="mt-4">
          Volver a productos
        </Button>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center gap-4">
        <button
          onClick={() => router.back()}
          className="p-2 hover:bg-gray-100 rounded-lg transition-colors"
        >
          <ArrowLeftIcon className="w-5 h-5 text-gray-600" />
        </button>
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Editar Producto</h1>
          <p className="text-gray-600 mt-1">{product.default_code || `ID: ${product.id}`}</p>
        </div>
      </div>

      <form onSubmit={handleSubmit(onSubmit)} className="space-y-6">
        <Card>
          <CardHeader>
            <h3 className="text-lg font-semibold text-gray-900">Información General</h3>
          </CardHeader>
          <CardBody className="space-y-4">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <Input
                label="Nombre *"
                placeholder="Nombre del producto"
                defaultValue={product.name}
                {...register('name', { required: 'El nombre es requerido' })}
                error={errors.name?.message}
              />
              <Input
                label="Código de producto"
                placeholder="SKU-001"
                defaultValue={product.default_code}
                {...register('default_code')}
              />
            </div>
            <Input
              label="Descripción"
              placeholder="Descripción detallada del producto"
              defaultValue={product.description}
              {...register('description')}
            />
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <Select
                label="Tipo *"
                defaultValue={product.type}
                {...register('type', { required: true })}
                options={[
                  { value: 'product', label: 'Producto almacenable' },
                  { value: 'consumable', label: 'Consumible' },
                  { value: 'service', label: 'Servicio' },
                ]}
              />
              <Input
                label="Código de barras"
                placeholder="7891234567890"
                defaultValue={product.barcode}
                {...register('barcode')}
              />
            </div>
          </CardBody>
        </Card>

        <Card>
          <CardHeader>
            <h3 className="text-lg font-semibold text-gray-900">Precios</h3>
          </CardHeader>
          <CardBody className="space-y-4">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <Input
                label="Precio de venta *"
                type="number"
                step="0.01"
                defaultValue={product.list_price}
                {...register('list_price', { 
                  required: 'El precio de venta es requerido',
                  valueAsNumber: true,
                })}
                error={errors.list_price?.message}
              />
              <Input
                label="Costo estándar *"
                type="number"
                step="0.01"
                defaultValue={product.standard_price}
                {...register('standard_price', { 
                  required: 'El costo es requerido',
                  valueAsNumber: true,
                })}
                error={errors.standard_price?.message}
              />
            </div>
          </CardBody>
        </Card>

        <Card>
          <CardHeader>
            <h3 className="text-lg font-semibold text-gray-900">Información Adicional</h3>
          </CardHeader>
          <CardBody className="space-y-4">
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <Input
                label="Stock disponible"
                value={product.qty_available}
                disabled
                helperText="Se actualiza con movimientos de inventario"
              />
              <Input
                label="Stock virtual"
                value={product.virtual_available}
                disabled
              />
              <Input
                label="Peso (kg)"
                type="number"
                step="0.01"
                defaultValue={product.weight}
                {...register('weight', { valueAsNumber: true })}
              />
            </div>
          </CardBody>
        </Card>

        <div className="flex justify-end gap-3">
          <Button type="button" variant="secondary" onClick={() => router.back()}>
            Cancelar
          </Button>
          <Button type="submit" isLoading={isSubmitting}>
            Guardar Cambios
          </Button>
        </div>
      </form>
    </div>
  )
}
