'use client'

import { useState } from 'react'
import { Table } from '@/components/ui/Table'
import { Card, CardBody, CardHeader } from '@/components/ui/Card'
import { Button } from '@/components/ui/Button'
import { Location } from '@/types'
import { MapPinIcon, ChevronRightIcon, HomeIcon, BuildingOfficeIcon, CubeIcon } from '@heroicons/react/24/outline'

const mockLocations: Location[] = [
  { id: 1, name: 'Almacén Principal', complete_name: 'Ubicaciones / Almacén Principal', usage: 'internal', location_type: 'warehouse', child_count: 5 },
  { id: 2, name: 'Almacén Secundario', complete_name: 'Ubicaciones / Almacén Secundario', usage: 'internal', location_type: 'warehouse', child_count: 3 },
  { id: 3, name: 'Estante A1', complete_name: 'Almacén Principal / Estante A1', usage: 'internal', location_type: 'shelf', parent_id: 1, child_count: 0 },
  { id: 4, name: 'Estante B2', complete_name: 'Almacén Principal / Estante B2', usage: 'internal', location_type: 'shelf', parent_id: 1, child_count: 0 },
  { id: 5, name: 'Ubicaciones Virtuales', complete_name: 'Ubicaciones / Virtuales', usage: 'view', location_type: 'view', child_count: 0 },
]

export default function LocationsPage() {
  const [locations, setLocations] = useState<Location[]>(mockLocations)

  const getIcon = (type: string) => {
    switch (type) {
      case 'warehouse':
        return <BuildingOfficeIcon className="w-5 h-5 text-primary-600" />
      case 'shelf':
        return <CubeIcon className="w-5 h-5 text-success-600" />
      case 'view':
        return <HomeIcon className="w-5 h-5 text-gray-400" />
      default:
        return <MapPinIcon className="w-5 h-5 text-gray-400" />
    }
  }

  const columns = [
    {
      key: 'name',
      header: 'Ubicación',
      render: (item: Location) => (
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-lg bg-gray-100 flex items-center justify-center">
            {getIcon(item.location_type)}
          </div>
          <div>
            <p className="font-medium text-gray-900">{item.name}</p>
            <p className="text-sm text-gray-500">{item.complete_name}</p>
          </div>
        </div>
      ),
    },
    {
      key: 'usage',
      header: 'Uso',
      render: (item: Location) => (
        <span className={`px-2 py-1 text-xs rounded-full ${
          item.usage === 'internal' 
            ? 'bg-primary-100 text-primary-700' 
            : item.usage === 'view'
            ? 'bg-gray-100 text-gray-700'
            : 'bg-success-100 text-success-700'
        }`}>
          {item.usage === 'internal' ? 'Interno' : item.usage === 'view' ? 'Vista' : 'Cliente'}
        </span>
      ),
    },
    {
      key: 'type',
      header: 'Tipo',
      render: (item: Location) => (
        <span className="text-gray-600 capitalize">{item.location_type}</span>
      ),
    },
    {
      key: 'child_count',
      header: 'Sub-ubicaciones',
      render: (item: Location) => (
        <span className={item.child_count > 0 ? 'text-primary-600 font-medium' : 'text-gray-400'}>
          {item.child_count} {item.child_count === 1 ? 'ubicación' : 'ubicaciones'}
        </span>
      ),
    },
    {
      key: 'actions',
      header: '',
      render: (item: Location) => (
        item.child_count > 0 && (
          <button className="p-2 text-gray-400 hover:text-primary-600 hover:bg-gray-100 rounded-lg transition-colors">
            <ChevronRightIcon className="w-5 h-5" />
          </button>
        )
      ),
    },
  ]

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Ubicaciones</h1>
          <p className="text-gray-600 mt-1">Gestión de almacenes y ubicaciones de almacenamiento</p>
        </div>
        <Button>
          <MapPinIcon className="w-5 h-5 mr-2" />
          Nueva Ubicación
        </Button>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <Card>
          <CardBody>
            <div className="flex items-center gap-4">
              <div className="w-12 h-12 rounded-lg bg-primary-100 flex items-center justify-center">
                <BuildingOfficeIcon className="w-6 h-6 text-primary-600" />
              </div>
              <div>
                <p className="text-2xl font-bold text-gray-900">{locations.filter(l => l.location_type === 'warehouse').length}</p>
                <p className="text-sm text-gray-500">Almacenes</p>
              </div>
            </div>
          </CardBody>
        </Card>
        <Card>
          <CardBody>
            <div className="flex items-center gap-4">
              <div className="w-12 h-12 rounded-lg bg-success-100 flex items-center justify-center">
                <CubeIcon className="w-6 h-6 text-success-600" />
              </div>
              <div>
                <p className="text-2xl font-bold text-gray-900">{locations.filter(l => l.location_type === 'shelf').length}</p>
                <p className="text-sm text-gray-500">Estantes</p>
              </div>
            </div>
          </CardBody>
        </Card>
        <Card>
          <CardBody>
            <div className="flex items-center gap-4">
              <div className="w-12 h-12 rounded-lg bg-warning-100 flex items-center justify-center">
                <MapPinIcon className="w-6 h-6 text-warning-600" />
              </div>
              <div>
                <p className="text-2xl font-bold text-gray-900">{locations.reduce((acc, l) => acc + l.child_count, 0)}</p>
                <p className="text-sm text-gray-500">Total Sub-ubicaciones</p>
              </div>
            </div>
          </CardBody>
        </Card>
      </div>

      <Card>
        <CardHeader>
          <h3 className="text-lg font-semibold text-gray-900">Todas las Ubicaciones</h3>
        </CardHeader>
        <CardBody className="p-0">
          <Table
            data={locations}
            columns={columns}
            keyExtractor={(item) => item.id}
            emptyMessage="No hay ubicaciones configuradas"
          />
        </CardBody>
      </Card>
    </div>
  )
}
