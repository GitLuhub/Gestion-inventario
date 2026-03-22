'use client'

import { useState } from 'react'
import { Table, Pagination } from '@/components/ui/Table'
import { Card, CardBody, CardHeader, StatCard } from '@/components/ui/Card'
import { Input } from '@/components/ui/Input'
import { Button } from '@/components/ui/Button'
import { Modal } from '@/components/ui/Modal'
import { useForm } from 'react-hook-form'
import { StockQuant, InventoryAdjustment } from '@/types'
import { CubeIcon, MapPinIcon, ArrowsUpDownIcon, ClipboardDocumentListIcon } from '@heroicons/react/24/outline'
import { PlusIcon, MagnifyingGlassIcon } from '@heroicons/react/24/outline'
import toast from 'react-hot-toast'

const mockQuants: StockQuant[] = [
  { id: 1, product_id: 1, product_name: 'Portátil HP ProBook 450', location_id: 1, location_name: 'Almacén Principal / Estante A1', quantity: 15, reserved_quantity: 2 },
  { id: 2, product_id: 2, product_name: 'Monitor Dell 27"', location_id: 1, location_name: 'Almacén Principal / Estante B2', quantity: 8, reserved_quantity: 1 },
  { id: 3, product_id: 3, product_name: 'Teclado Mecánico RGB', location_id: 2, location_name: 'Almacén Secundario / Estante C1', quantity: 45, reserved_quantity: 0 },
]

const mockAdjustments: InventoryAdjustment[] = [
  { id: 1, name: 'INV-2024-001', date: '2024-01-15', state: 'done', adjustment_type: 'Ajuste', line_count: 12 },
  { id: 2, name: 'INV-2024-002', date: '2024-01-18', state: 'done', adjustment_type: 'Recuento', line_count: 8 },
  { id: 3, name: 'INV-2024-003', date: '2024-01-20', state: 'draft', adjustment_type: 'Ajuste', line_count: 5 },
]

type AdjustmentFormData = {
  name: string
  adjustment_type: string
  location_id: number
}

export default function InventoryPage() {
  const [quants, setQuants] = useState<StockQuant[]>(mockQuants)
  const [adjustments, setAdjustments] = useState<InventoryAdjustment[]>(mockAdjustments)
  const [search, setSearch] = useState('')
  const [page, setPage] = useState(1)
  const [isModalOpen, setIsModalOpen] = useState(false)

  const { register, handleSubmit, reset, formState: { errors } } = useForm<AdjustmentFormData>()

  const filteredQuants = quants.filter(q => 
    q.product_name.toLowerCase().includes(search.toLowerCase()) ||
    q.location_name.toLowerCase().includes(search.toLowerCase())
  )

  const onSubmitAdjustment = (data: AdjustmentFormData) => {
    const newAdjustment: InventoryAdjustment = {
      id: adjustments.length + 1,
      name: `INV-2024-${String(adjustments.length + 4).padStart(3, '0')}`,
      date: new Date().toISOString().split('T')[0],
      state: 'draft',
      adjustment_type: data.adjustment_type,
      line_count: 0,
    }
    setAdjustments([newAdjustment, ...adjustments])
    toast.success('Ajuste creado correctamente')
    setIsModalOpen(false)
    reset()
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
    },
    {
      key: 'state',
      header: 'Estado',
      render: (item: InventoryAdjustment) => (
        <span className={`px-2 py-1 text-xs rounded-full ${
          item.state === 'done' 
            ? 'bg-success-100 text-success-700' 
            : 'bg-warning-100 text-warning-700'
        }`}>
          {item.state === 'done' ? 'Completado' : 'Borrador'}
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
          value="1,234"
          icon={<CubeIcon className="w-6 h-6 text-primary-600" />}
        />
        <StatCard
          title="Ubicaciones Activas"
          value="23"
          icon={<MapPinIcon className="w-6 h-6 text-success-600" />}
        />
        <StatCard
          title="Reservas"
          value="45"
          icon={<ArrowsUpDownIcon className="w-6 h-6 text-warning-600" />}
        />
        <StatCard
          title="Ajustes Pendientes"
          value={adjustments.filter(a => a.state === 'draft').length.toString()}
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
            emptyMessage="No hay existencias que mostrar"
          />
        </CardBody>
      </Card>

      <Card>
        <CardHeader>
          <h3 className="text-lg font-semibold text-gray-900">Ajustes Recientes</h3>
        </CardHeader>
        <CardBody className="p-0">
          <Table
            data={adjustments}
            columns={adjustmentColumns}
            keyExtractor={(item) => item.id}
            emptyMessage="No hay ajustes recientes"
          />
        </CardBody>
      </Card>

      <Modal
        isOpen={isModalOpen}
        onClose={() => setIsModalOpen(false)}
        title="Nuevo Ajuste de Inventario"
        footer={
          <div className="flex justify-end gap-3">
            <Button variant="secondary" onClick={() => setIsModalOpen(false)}>
              Cancelar
            </Button>
            <Button type="submit" form="adjustment-form">
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
              <option value="Ajuste">Ajuste</option>
              <option value="Recuento">Recuento</option>
              <option value="Corrección">Corrección</option>
            </select>
          </div>
        </form>
      </Modal>
    </div>
  )
}
