'use client'

import { useRouter } from 'next/navigation'
import { Card, CardHeader, CardBody, StatCard } from '@/components/ui/Card'
import { CubeIcon, MapPinIcon, ExclamationTriangleIcon, CurrencyDollarIcon, ClipboardDocumentListIcon } from '@heroicons/react/24/outline'
import { useInventoryStats, useInventoryAdjustments } from '@/hooks'
import { useProducts } from '@/hooks'

export default function DashboardPage() {
  const router = useRouter()
  const { stats, isLoading: statsLoading } = useInventoryStats()
  const { products, isLoading: productsLoading } = useProducts({ page: 1, page_size: 5 })
  const { adjustments, isLoading: adjLoading } = useInventoryAdjustments(1, 5)

  const formatValue = (v: number) =>
    v >= 1_000_000
      ? `$${(v / 1_000_000).toFixed(1)}M`
      : v >= 1_000
      ? `$${(v / 1_000).toFixed(1)}K`
      : `$${v.toLocaleString('es-CO')}`

  const stateLabel: Record<string, string> = {
    draft: 'Borrador',
    in_progress: 'En Progreso',
    done: 'Completado',
    cancel: 'Cancelado',
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-gray-900">Dashboard</h1>
        <p className="text-gray-600 mt-1">Resumen de la gestión de inventario</p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <StatCard
          title="Total Productos"
          value={statsLoading ? '…' : (stats?.total_products ?? 0).toLocaleString()}
          icon={<CubeIcon className="w-8 h-8 text-primary-600" />}
        />
        <StatCard
          title="Ubicaciones"
          value={statsLoading ? '…' : (stats?.total_locations ?? 0).toLocaleString()}
          icon={<MapPinIcon className="w-8 h-8 text-success-600" />}
        />
        <StatCard
          title="Stock Bajo Mínimo"
          value={statsLoading ? '…' : (stats?.low_stock_products ?? 0).toLocaleString()}
          icon={<ExclamationTriangleIcon className="w-8 h-8 text-warning-600" />}
        />
        <StatCard
          title="Valor Total Stock"
          value={statsLoading ? '…' : formatValue(stats?.total_stock_value ?? 0)}
          icon={<CurrencyDollarIcon className="w-8 h-8 text-primary-600" />}
        />
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <Card>
          <CardHeader>
            <h3 className="text-lg font-semibold text-gray-900">Productos Recientes</h3>
          </CardHeader>
          <CardBody className="p-0">
            {productsLoading ? (
              <div className="px-6 py-8 text-center text-sm text-gray-400">Cargando…</div>
            ) : products.length === 0 ? (
              <div className="px-6 py-8 text-center text-sm text-gray-400">Sin productos</div>
            ) : (
              <div className="divide-y divide-gray-200">
                {products.map((p) => (
                  <div
                    key={p.id}
                    className="flex items-center justify-between px-6 py-4 hover:bg-gray-50 cursor-pointer"
                    onClick={() => router.push(`/dashboard/products/${p.id}`)}
                  >
                    <div className="flex items-center space-x-4">
                      <div className="w-10 h-10 rounded-lg bg-primary-100 flex items-center justify-center">
                        <CubeIcon className="w-5 h-5 text-primary-600" />
                      </div>
                      <div>
                        <p className="text-sm font-medium text-gray-900">{p.name}</p>
                        <p className="text-sm text-gray-500">{p.default_code || 'Sin código'}</p>
                      </div>
                    </div>
                    <div className="text-right">
                      <p className="text-sm font-medium text-gray-900">
                        {p.qty_available} uds
                      </p>
                      <p className="text-sm text-gray-500">
                        ${p.list_price.toLocaleString('es-CO')}
                      </p>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </CardBody>
        </Card>

        <Card>
          <CardHeader>
            <div className="flex items-center justify-between">
              <h3 className="text-lg font-semibold text-gray-900">Ajustes Recientes</h3>
              <div className="flex items-center gap-2 text-sm text-gray-500">
                <ClipboardDocumentListIcon className="w-4 h-4" />
                <span>{statsLoading ? '…' : stats?.pending_operations ?? 0} pendientes</span>
              </div>
            </div>
          </CardHeader>
          <CardBody className="p-0">
            {adjLoading ? (
              <div className="px-6 py-8 text-center text-sm text-gray-400">Cargando…</div>
            ) : adjustments.length === 0 ? (
              <div className="px-6 py-8 text-center text-sm text-gray-400">Sin ajustes registrados</div>
            ) : (
              <div className="divide-y divide-gray-200">
                {adjustments.map((a) => (
                  <div key={a.id} className="flex items-center justify-between px-6 py-4 hover:bg-gray-50">
                    <div>
                      <p className="text-sm font-medium text-gray-900 font-mono">{a.name}</p>
                      <p className="text-sm text-gray-500">{a.adjustment_type} · {a.line_count} líneas</p>
                    </div>
                    <span className={`px-2 py-1 text-xs rounded-full ${
                      a.state === 'done'
                        ? 'bg-success-100 text-success-700'
                        : a.state === 'in_progress'
                        ? 'bg-primary-100 text-primary-700'
                        : 'bg-warning-100 text-warning-700'
                    }`}>
                      {stateLabel[a.state] ?? a.state}
                    </span>
                  </div>
                ))}
              </div>
            )}
          </CardBody>
        </Card>
      </div>
    </div>
  )
}
