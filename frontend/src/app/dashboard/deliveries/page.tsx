'use client'

import { Card, CardBody, CardHeader } from '@/components/ui/Card'
import { ArrowUpTrayIcon } from '@heroicons/react/24/outline'

export default function DeliveriesPage() {
  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-gray-900">Entregas</h1>
        <p className="text-gray-600 mt-1">Operaciones de salida de mercancía</p>
      </div>
      <Card>
        <CardHeader>
          <h3 className="text-lg font-semibold text-gray-900">Entregas Pendientes</h3>
        </CardHeader>
        <CardBody>
          <div className="flex flex-col items-center justify-center py-12 text-gray-400">
            <ArrowUpTrayIcon className="w-12 h-12 mb-3" />
            <p className="text-sm">Gestiona las entregas desde Odoo</p>
            <a
              href="http://localhost:8069/web#action=stock.action_picking_tree_all&type=outgoing"
              target="_blank"
              rel="noopener noreferrer"
              className="mt-4 text-sm text-primary-600 hover:underline"
            >
              Abrir en Odoo →
            </a>
          </div>
        </CardBody>
      </Card>
    </div>
  )
}
