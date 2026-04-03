'use client'

import { useState } from 'react'
import { Table } from '@/components/ui/Table'
import { Card, CardBody, CardHeader, StatCard } from '@/components/ui/Card'
import { Input } from '@/components/ui/Input'
import { Button } from '@/components/ui/Button'
import { Modal } from '@/components/ui/Modal'
import { useForm } from 'react-hook-form'
import { StockQuant, InventoryAdjustment } from '@/types'
import { CubeIcon, MapPinIcon, ArrowsUpDownIcon, ClipboardDocumentListIcon } from '@heroicons/react/24/outline'
import { PlusIcon, MagnifyingGlassIcon } from '@heroicons/react/24/outline'
import toast from 'react-hot-toast'
import { useInventoryStats, useInventoryQuants, useInventoryAdjustments } from '@/hooks'
import { inventoryService } from '@/services/inventory'

type AdjustmentFormData = {
  name: string
  adjustment_type: string
}

export default function InventoryPage() {
  const [search, setSearch] = useState('')
  const [isModalOpen, setIsModalOpen] = useState(false)
  const [isSubmitting, setIsSubmitting] = useState(false)

  const { stats } = useInventoryStats()
  const { quants, isLoading: quantsLoading } = useInventoryQuants()
  const { adjustments, isLoading: adjLoading, mutate: mutateAdj } = useInventoryAdjustments(1, 20)

  const { register, handleSubmit, reset, formState: { errors } } = useForm<AdjustmentFormData>()

  const filteredQuants = quants.filter(q =>
    q.product_name.toLowerCase().includes(search.toLowerCase()) ||
    q.location_name.toLowerCase().includes(search.toLowerCase())
  )

  const totalStock = quants.reduce((sum, q) => sum + q.quantity, 0)
  const totalReserved = quants.reduce((sum, q) => sum + q.reserved_quantity, 0)
  const pendingAdj = adjustments.filter(a => a.state === 'draft' || a.state === 'in_progress').length

  const onSubmitAdjustment = async (data: AdjustmentFormData) => {
    setIsSubmitting(true)
    try {
      await inventoryService.createAdjustment({ name: data.name, adjustment_type: data.adjustment_type } as any)
      await mutateAdj()
      toast.success('Ajuste creado correctamente')
      setIsModalOpen(false)
      reset()
    } catch (e: any) {
      toast.error(e?.message || 'Error al crear el ajuste')
    } finally {
      setIsSubmitting(false)
    }
  }

  const stateLabel: Record<string, string> = {
    draft: 'Borrador',
    in_progress: 'En Progreso',
    done: 'Completado',
    cancel: 'Cancelado',
  }

  const quantColumns = [
    {
      key: 'product',
      header: 'Producto',
      render: (item: StockQuant) => (
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-lg bg-primary-100 flex items-center justify-center">
            <CubeIcon className="w-5 h-5 text-primary-600" />
          </div>
          <span className="font-medium">{item.product_name}</span>
        </div>
      ),
    },
    {
      key: 'location',
      header: 'Ubicación',
      render: (item: StockQuant) => (
        <div className="flex items-center gap-2">
          <MapPinIcon className="w-4 h-4 text-gray-400" />
          <span className="text-gray-600">{item.location_name}</span>
        </div>
      ),
    },
    {
      key: 'quantity',
      header: 'Cantidad',
      render: (item: StockQuant) => (
        <div className="flex items-center gap-2">
          <span className="font-medium">{item.quantity}</span>
          {item.reserved_quantity > 0 && (
            <span className="text-xs text-warning-600">({item.reserved_quantity} reservadas)</span>
          )}
        </div>
      ),
    },
    {
      key: 'lot',
      header: 'Lote',
      render: (item: StockQuant) =>
        item.lot_name ? (
          <span className="px-2 py-1 text-xs rounded-full bg-gray-100 text-gray-600">{item.lot_name}</span>
        ) : (
          <span className="text-gray-300 text-xs">—</span>
        ),
    },
  ]

  const adjustmentColumns = [
    {
      key: 'name',
      header: 'Referencia',
      render: (item: InventoryAdjustment) => (
        <span className="font-mono font-medium">{item.name}</span>
      ),
    },
    {
      key: 'adjustment_type',
      header: 'Tipo',
      render: (item: InventoryAdjustment) => (
        <span className="px-2 py-1 text-xs rounded-full bg-gray-100 text-gray-700">
          {item.adjustment_type}
        </span>
      ),
    },
    {
      key: 'date',
      header: 'Fecha',
      render: (item: InventoryAdjustment) =>
        new Date(item.date).toLocaleDateString('es-CO'),
    },
    {
      key: 'state',
      header: 'Estado',
      render: (item: InventoryAdjustment) => (
        <span className={`px-2 py-1 text-xs rounded-full ${
          item.state === 'done'
            ? 'bg-success-100 text-success-700'
            : item.state === 'in_progress'
            ? 'bg-primary-100 text-primary-700'
            : 'bg-warning-100 text-warning-700'
        }`}>
          {stateLabel[item.state] ?? item.state}
        </span>
      ),
    },
    {
      key: 'line_count',
      header: 'Líneas',
    },
  ]

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Inventario</h1>
          <p className="text-gray-600 mt-1">Control de stock y movimientos</p>
        </div>
        <Button onClick={() => setIsModalOpen(true)}>
          <PlusIcon className="w-5 h-5 mr-2" />
          Nuevo Ajuste
        </Button>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <StatCard
          title="Total Stock"
          value={quantsLoading ? '…' : totalStock.toLocaleString()}
          icon={<CubeIcon className="w-6 h-6 text-primary-600" />}
        />
        <StatCard
          title="Ubicaciones Activas"
          value={stats?.total_locations?.toLocaleString() ?? '…'}
          icon={<MapPinIcon className="w-6 h-6 text-success-600" />}
        />
        <StatCard
          title="Unidades Reservadas"
          value={quantsLoading ? '…' : totalReserved.toLocaleString()}
          icon={<ArrowsUpDownIcon className="w-6 h-6 text-warning-600" />}
        />
        <StatCard
          title="Ajustes Pendientes"
          value={adjLoading ? '…' : pendingAdj.toString()}
          icon={<ClipboardDocumentListIcon className="w-6 h-6 text-danger-600" />}
        />
      </div>

      <Card>
        <CardHeader>
          <h3 className="text-lg font-semibold text-gray-900">Existencias por Ubicación</h3>
        </CardHeader>
        <CardBody>
          <div className="flex gap-4 mb-6">
            <div className="flex-1">
              <Input
                placeholder="Buscar producto o ubicación..."
                value={search}
                onChange={(e) => setSearch(e.target.value)}
              />
            </div>
            <Button variant="outline">
              <MagnifyingGlassIcon className="w-5 h-5" />
            </Button>
          </div>
          <Table
            data={filteredQuants}
            columns={quantColumns}
            keyExtractor={(item) => item.id}
            isLoading={quantsLoading}
            emptyMessage="No hay existencias que mostrar"
          />
        </CardBody>
      </Card>

      <Card>
        <CardHeader>
          <h3 className="text-lg font-semibold text-gray-900">Ajustes de Inventario</h3>
        </CardHeader>
        <CardBody className="p-0">
          <Table
            data={adjustments}
            columns={adjustmentColumns}
            keyExtractor={(item) => item.id}
            isLoading={adjLoading}
            emptyMessage="No hay ajustes registrados"
          />
        </CardBody>
      </Card>

      <Modal
        isOpen={isModalOpen}
        onClose={() => { setIsModalOpen(false); reset() }}
        title="Nuevo Ajuste de Inventario"
        footer={
          <div className="flex justify-end gap-3">
            <Button variant="secondary" onClick={() => { setIsModalOpen(false); reset() }}>
              Cancelar
            </Button>
            <Button type="submit" form="adjustment-form" isLoading={isSubmitting}>
              Crear Ajuste
            </Button>
          </div>
        }
      >
        <form id="adjustment-form" onSubmit={handleSubmit(onSubmitAdjustment)} className="space-y-4">
          <Input
            label="Nombre"
            placeholder="Descripción del ajuste"
            {...register('name', { required: 'El nombre es requerido' })}
            error={errors.name?.message}
          />
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Tipo de Ajuste</label>
            <select
              {...register('adjustment_type', { required: true })}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500"
            >
              <option value="partial">Parcial</option>
              <option value="cyclic">Cíclico</option>
              <option value="full">Completo</option>
              <option value="correction">Corrección</option>
            </select>
          </div>
        </form>
      </Modal>
    </div>
  )
}
