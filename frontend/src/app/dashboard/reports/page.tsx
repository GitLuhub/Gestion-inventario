'use client'

import { useState } from 'react'
import { Card, CardBody, CardHeader } from '@/components/ui/Card'
import { Select } from '@/components/ui/Input'
import { Button } from '@/components/ui/Button'
import { 
  CubeIcon, 
  MapPinIcon, 
  CurrencyDollarIcon, 
  ArrowTrendingUpIcon,
  ArrowTrendingDownIcon,
  DocumentArrowDownIcon
} from '@heroicons/react/24/outline'

const reportTypes = [
  { value: 'inventory', label: 'Resumen de Inventario' },
  { value: 'valuation', label: 'Valorización de Stock' },
  { value: 'movements', label: 'Movimientos de Stock' },
  { value: 'low_stock', label: 'Productos Stock Bajo' },
]

export default function ReportsPage() {
  const [selectedReport, setSelectedReport] = useState('inventory')

  const mockData = {
    total_products: 1234,
    total_value: 125000000,
    low_stock_count: 23,
    out_of_stock_count: 5,
    top_categories: [
      { name: 'Electrónica', count: 456, value: 45000000 },
      { name: 'Oficina', count: 234, value: 23000000 },
      { name: 'Muebles', count: 189, value: 35000000 },
      { name: 'Accesorios', count: 355, value: 22000000 },
    ],
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Reportes</h1>
          <p className="text-gray-600 mt-1">Informes y análisis de inventario</p>
        </div>
        <Button>
          <DocumentArrowDownIcon className="w-5 h-5 mr-2" />
          Exportar PDF
        </Button>
      </div>

      <div className="flex gap-4">
        <div className="w-64">
          <Select
            label="Tipo de Reporte"
            value={selectedReport}
            onChange={(e) => setSelectedReport(e.target.value)}
            options={reportTypes}
          />
        </div>
        <div className="flex items-end">
          <Button variant="outline">Generar Reporte</Button>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <Card>
          <CardBody>
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-500">Total Productos</p>
                <p className="text-2xl font-bold text-gray-900">{mockData.total_products.toLocaleString()}</p>
              </div>
              <div className="w-12 h-12 rounded-lg bg-primary-100 flex items-center justify-center">
                <CubeIcon className="w-6 h-6 text-primary-600" />
              </div>
            </div>
            <div className="mt-2 flex items-center gap-1 text-sm text-success-600">
              <ArrowTrendingUpIcon className="w-4 h-4" />
              <span>+12% vs mes anterior</span>
            </div>
          </CardBody>
        </Card>

        <Card>
          <CardBody>
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-500">Valor Total Stock</p>
                <p className="text-2xl font-bold text-gray-900">${(mockData.total_value / 1000000).toFixed(1)}M</p>
              </div>
              <div className="w-12 h-12 rounded-lg bg-success-100 flex items-center justify-center">
                <CurrencyDollarIcon className="w-6 h-6 text-success-600" />
              </div>
            </div>
            <div className="mt-2 flex items-center gap-1 text-sm text-success-600">
              <ArrowTrendingUpIcon className="w-4 h-4" />
              <span>+8% vs mes anterior</span>
            </div>
          </CardBody>
        </Card>

        <Card>
          <CardBody>
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-500">Stock Bajo</p>
                <p className="text-2xl font-bold text-warning-600">{mockData.low_stock_count}</p>
              </div>
              <div className="w-12 h-12 rounded-lg bg-warning-100 flex items-center justify-center">
                <ArrowTrendingDownIcon className="w-6 h-6 text-warning-600" />
              </div>
            </div>
            <p className="mt-2 text-sm text-gray-500">Requieren atención</p>
          </CardBody>
        </Card>

        <Card>
          <CardBody>
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-500">Sin Stock</p>
                <p className="text-2xl font-bold text-danger-600">{mockData.out_of_stock_count}</p>
              </div>
              <div className="w-12 h-12 rounded-lg bg-danger-100 flex items-center justify-center">
                <CubeIcon className="w-6 h-6 text-danger-600" />
              </div>
            </div>
            <p className="mt-2 text-sm text-gray-500">Agotados</p>
          </CardBody>
        </Card>
      </div>

      <Card>
        <CardHeader>
          <h3 className="text-lg font-semibold text-gray-900">Valor por Categoría</h3>
        </CardHeader>
        <CardBody>
          <div className="space-y-4">
            {mockData.top_categories.map((cat, idx) => (
              <div key={idx}>
                <div className="flex items-center justify-between mb-1">
                  <span className="text-sm font-medium text-gray-700">{cat.name}</span>
                  <span className="text-sm text-gray-900">${cat.value.toLocaleString()}</span>
                </div>
                <div className="w-full bg-gray-200 rounded-full h-2">
                  <div 
                    className="bg-primary-600 h-2 rounded-full" 
                    style={{ width: `${(cat.value / mockData.total_value) * 100}%` }}
                  />
                </div>
              </div>
            ))}
          </div>
        </CardBody>
      </Card>

      <Card>
        <CardHeader>
          <h3 className="text-lg font-semibold text-gray-900">Productos con Stock Bajo</h3>
        </CardHeader>
        <CardBody className="p-0">
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-gray-200">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Producto</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Stock Actual</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Stock Mínimo</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Ubicación</th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {[
                  { name: 'Cable HDMI 2m', current: 3, min: 10, location: 'Estante A1' },
                  { name: 'Mouse Inalámbrico', current: 5, min: 15, location: 'Estante B2' },
                  { name: 'Memoria USB 32GB', current: 2, min: 20, location: 'Estante C1' },
                  { name: 'Pilas AA (pack)', current: 8, min: 25, location: 'Estante A2' },
                ].map((item, idx) => (
                  <tr key={idx} className="hover:bg-gray-50">
                    <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">{item.name}</td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-danger-600 font-medium">{item.current}</td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">{item.min}</td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                      <span className="flex items-center gap-1">
                        <MapPinIcon className="w-4 h-4" />
                        {item.location}
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </CardBody>
      </Card>
    </div>
  )
}
