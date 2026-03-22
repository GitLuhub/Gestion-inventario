'use client'

import { useState } from 'react'
import { useRouter } from 'next/navigation'
import { useForm } from 'react-hook-form'
import { Card, CardBody, CardHeader } from '@/components/ui/Card'
import { Input } from '@/components/ui/Input'
import { Select } from '@/components/ui/Input'
import { Button } from '@/components/ui/Button'
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

export default function NewProductPage() {
  const router = useRouter()
  const [isSubmitting, setIsSubmitting] = useState(false)

  const { register, handleSubmit, formState: { errors } } = useForm<ProductFormData>({
    defaultValues: {
      type: 'product',
      list_price: 0,
      standard_price: 0,
    },
  })

  const onSubmit = async (data: ProductFormData) => {
    setIsSubmitting(true)
    try {
      await productService.create(data as Partial<Product>)
      toast.success('Producto creado correctamente')
      router.push('/dashboard/products')
    } catch {
      toast.error('Error al crear el producto')
    } finally {
      setIsSubmitting(false)
    }
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
          <h1 className="text-2xl font-bold text-gray-900">Nuevo Producto</h1>
          <p className="text-gray-600 mt-1">Crear un nuevo producto en el inventario</p>
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
                {...register('name', { required: 'El nombre es requerido' })}
                error={errors.name?.message}
              />
              <Input
                label="Código de producto"
                placeholder="SKU-001"
                {...register('default_code')}
              />
            </div>
            <Input
              label="Descripción"
              placeholder="Descripción detallada del producto"
              {...register('description')}
            />
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <Select
                label="Tipo *"
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
                placeholder="0.00"
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
                placeholder="0.00"
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
            <Input
              label="Peso (kg)"
              type="number"
              step="0.01"
              placeholder="0.00"
              {...register('weight', { valueAsNumber: true })}
            />
          </CardBody>
        </Card>

        <div className="flex justify-end gap-3">
          <Button type="button" variant="secondary" onClick={() => router.back()}>
            Cancelar
          </Button>
          <Button type="submit" isLoading={isSubmitting}>
            Crear Producto
          </Button>
        </div>
      </form>
    </div>
  )
}
