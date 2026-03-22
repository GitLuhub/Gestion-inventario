'use client'

import { Card, CardHeader, CardBody, StatCard } from '@/components/ui/Card'
import { CubeIcon, MapPinIcon, ExclamationTriangleIcon, CurrencyDollarIcon } from '@heroicons/react/24/outline'

export default function DashboardPage() {
  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-gray-900">Dashboard</h1>
        <p className="text-gray-600 mt-1">Resumen de la gestión de inventario</p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <StatCard
          title="Total Productos"
          value="1,234"
          icon={<CubeIcon className="w-8 h-8 text-primary-600" />}
          trend={{ value: 12, isPositive: true }}
        />
        <StatCard
          title="Ubicaciones"
          value="56"
          icon={<MapPinIcon className="w-8 h-8 text-success-600" />}
          trend={{ value: 5, isPositive: true }}
        />
        <StatCard
          title="Stock Bajo"
          value="23"
          icon={<ExclamationTriangleIcon className="w-8 h-8 text-warning-600" />}
        />
        <StatCard
          title="Valor Total"
          value="$125,000,000"
          icon={<CurrencyDollarIcon className="w-8 h-8 text-primary-600" />}
          trend={{ value: 8, isPositive: true }}
        />
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <Card>
          <CardHeader>
            <h3 className="text-lg font-semibold text-gray-900">Productos Recientes</h3>
          </CardHeader>
          <CardBody className="p-0">
            <div className="divide-y divide-gray-200">
              {[1, 2, 3, 4, 5].map((i) => (
                <div key={i} className="flex items-center justify-between px-6 py-4 hover:bg-gray-50">
                  <div className="flex items-center space-x-4">
                    <div className="w-10 h-10 rounded-lg bg-primary-100 flex items-center justify-center">
                      <CubeIcon className="w-5 h-5 text-primary-600" />
                    </div>
                    <div>
                      <p className="text-sm font-medium text-gray-900">Producto {i}</p>
                      <p className="text-sm text-gray-500">SKU-00{i}</p>
                    </div>
                  </div>
                  <div className="text-right">
                    <p className="text-sm font-medium text-gray-900">100 unidades</p>
                    <p className="text-sm text-gray-500">$50,000</p>
                  </div>
                </div>
              ))}
            </div>
          </CardBody>
        </Card>

        <Card>
          <CardHeader>
            <h3 className="text-lg font-semibold text-gray-900">Actividad Reciente</h3>
          </CardHeader>
          <CardBody className="p-0">
            <div className="divide-y divide-gray-200">
              {[
                { action: 'Recepción', user: 'Carlos M.', time: 'Hace 5 min' },
                { action: 'Ajuste de inventario', user: 'Ana L.', time: 'Hace 15 min' },
                { action: 'Entrega', user: 'Juan P.', time: 'Hace 30 min' },
                { action: 'Creación producto', user: 'María G.', time: 'Hace 1 hora' },
                { action: 'Transferencia', user: 'Pedro R.', time: 'Hace 2 horas' },
              ].map((item, i) => (
                <div key={i} className="flex items-center justify-between px-6 py-4 hover:bg-gray-50">
                  <div>
                    <p className="text-sm font-medium text-gray-900">{item.action}</p>
                    <p className="text-sm text-gray-500">por {item.user}</p>
                  </div>
                  <p className="text-sm text-gray-400">{item.time}</p>
                </div>
              ))}
            </div>
          </CardBody>
        </Card>
      </div>
    </div>
  )
}
