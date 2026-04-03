'use client'

import { Card, CardBody, CardHeader } from '@/components/ui/Card'
import { Button } from '@/components/ui/Button'
import {
  CubeIcon,
  MapPinIcon,
  CurrencyDollarIcon,
  ArrowTrendingDownIcon,
  DocumentArrowDownIcon,
  ExclamationTriangleIcon,
} from '@heroicons/react/24/outline'
import { useReportSummary, useLowStockInventory } from '@/hooks'

export default function ReportsPage() {
  const { summary, isLoading } = useReportSummary()
  const { products: lowStockProducts, isLoading: lowLoading } = useLowStockInventory(20)

  const formatValue = (v: number) =>
    v >= 1_000_000
      ? `$${(v / 1_000_000).toFixed(1)}M`
      : v >= 1_000
      ? `$${(v / 1_000).toFixed(1)}K`
      : `$${v.toLocaleString('es-CO')}`

  const maxCatValue = summary?.top_categories?.[0]?.total_value ?? 1

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Reportes</h1>
          <p className="text-gray-600 mt-1">Informes y análisis de inventario</p>
        </div>
        <Button disabled>
          <DocumentArrowDownIcon className="w-5 h-5 mr-2" />
          Exportar PDF
        </Button>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <Card>
          <CardBody>
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-500">Total Productos</p>
                <p className="text-2xl font-bold text-gray-900">
                  {isLoading ? '…' : (summary?.total_products ?? 0).toLocaleString()}
                </p>
              </div>
              <div className="w-12 h-12 rounded-lg bg-primary-100 flex items-center justify-center">
                <CubeIcon className="w-6 h-6 text-primary-600" />
              </div>
            </div>
          </CardBody>
        </Card>

        <Card>
          <CardBody>
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-500">Valor Total Stock</p>
                <p className="text-2xl font-bold text-gray-900">
                  {isLoading ? '…' : formatValue(summary?.total_stock_value ?? 0)}
                </p>
              </div>
              <div className="w-12 h-12 rounded-lg bg-success-100 flex items-center justify-center">
                <CurrencyDollarIcon className="w-6 h-6 text-success-600" />
              </div>
            </div>
          </CardBody>
        </Card>

        <Card>
          <CardBody>
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-500">Stock Bajo Mínimo</p>
                <p className="text-2xl font-bold text-warning-600">
                  {isLoading ? '…' : (summary?.low_stock_count ?? 0)}
                </p>
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
                <p className="text-2xl font-bold text-danger-600">
                  {isLoading ? '…' : (summary?.out_of_stock_count ?? 0)}
                </p>
              </div>
              <div className="w-12 h-12 rounded-lg bg-danger-100 flex items-center justify-center">
                <ExclamationTriangleIcon className="w-6 h-6 text-danger-600" />
              </div>
            </div>
            <p className="mt-2 text-sm text-gray-500">Agotados</p>
          </CardBody>
        </Card>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <Card>
          <CardHeader>
            <h3 className="text-lg font-semibold text-gray-900">Valor por Categoría</h3>
          </CardHeader>
          <CardBody>
            {isLoading ? (
              <div className="py-8 text-center text-sm text-gray-400">Cargando…</div>
            ) : !summary?.top_categories?.length ? (
              <div className="py-8 text-center text-sm text-gray-400">Sin datos de categorías</div>
            ) : (
              <div className="space-y-4">
                {summary.top_categories.map((cat) => (
                  <div key={cat.id}>
                    <div className="flex items-center justify-between mb-1">
                      <span className="text-sm font-medium text-gray-700">
                        {cat.name}
                        <span className="ml-2 text-xs text-gray-400">({cat.product_count} productos)</span>
                      </span>
                      <span className="text-sm text-gray-900">{formatValue(cat.total_value)}</span>
                    </div>
                    <div className="w-full bg-gray-200 rounded-full h-2">
                      <div
                        className="bg-primary-600 h-2 rounded-full"
                        style={{ width: `${Math.min((cat.total_value / maxCatValue) * 100, 100)}%` }}
                      />
                    </div>
                  </div>
                ))}
              </div>
            )}
          </CardBody>
        </Card>

        <Card>
          <CardHeader>
            <h3 className="text-lg font-semibold text-gray-900">Productos con Stock Bajo</h3>
          </CardHeader>
          <CardBody className="p-0">
            {lowLoading ? (
              <div className="py-8 text-center text-sm text-gray-400">Cargando…</div>
            ) : lowStockProducts.length === 0 ? (
              <div className="py-8 text-center text-sm text-gray-400">
                Ningún producto está por debajo del mínimo
              </div>
            ) : (
              <div className="overflow-x-auto">
                <table className="min-w-full divide-y divide-gray-200">
                  <thead className="bg-gray-50">
                    <tr>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Producto</th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Stock Actual</th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Stock Mínimo</th>
                    </tr>
                  </thead>
                  <tbody className="bg-white divide-y divide-gray-200">
                    {lowStockProducts.map((p) => (
                      <tr key={p.id} className="hover:bg-gray-50">
                        <td className="px-6 py-4 whitespace-nowrap">
                          <p className="text-sm font-medium text-gray-900">{p.name}</p>
                          {p.default_code && (
                            <p className="text-xs text-gray-400">{p.default_code}</p>
                          )}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-danger-600 font-medium">
                          {p.qty_available}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                          {p.min_stock_level}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </CardBody>
        </Card>
      </div>
    </div>
  )
}
