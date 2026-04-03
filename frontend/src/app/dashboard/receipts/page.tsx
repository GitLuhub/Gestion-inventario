'use client'

import { Card, CardBody, CardHeader } from '@/components/ui/Card'
import { ArrowDownTrayIcon } from '@heroicons/react/24/outline'

export default function ReceiptsPage() {
  const odooUrl = process.env.NEXT_PUBLIC_ODOO_URL || '/web'

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-gray-900">Recepciones</h1>
        <p className="text-gray-600 mt-1">Operaciones de entrada de mercancía</p>
      </div>
      <Card>
        <CardHeader>
          <h3 className="text-lg font-semibold text-gray-900">Recepciones Pendientes</h3>
        </CardHeader>
        <CardBody>
          <div className="flex flex-col items-center justify-center py-12 text-gray-400">
            <ArrowDownTrayIcon className="w-12 h-12 mb-3" />
            <p className="text-sm font-medium text-gray-600">
              Las recepciones se gestionan directamente en el módulo de inventario de Odoo.
            </p>
            <p className="text-sm text-gray-400 mt-1">
              Desde allí puede registrar entradas de mercancía, validar órdenes de compra y actualizar el stock.
            </p>
            <a
              href={`${odooUrl}#action=stock.action_picking_tree_all`}
              target="_blank"
              rel="noopener noreferrer"
              className="mt-6 inline-flex items-center gap-2 px-4 py-2 bg-primary-600 text-white text-sm font-medium rounded-lg hover:bg-primary-700 transition-colors"
            >
              <ArrowDownTrayIcon className="w-4 h-4" />
              Ir a Recepciones en Odoo
            </a>
          </div>
        </CardBody>
      </Card>
    </div>
  )
}
