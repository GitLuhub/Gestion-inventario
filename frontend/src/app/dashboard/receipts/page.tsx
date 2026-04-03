'use client'

import { Card, CardBody, CardHeader } from '@/components/ui/Card'
import { ArrowDownTrayIcon } from '@heroicons/react/24/outline'

export default function ReceiptsPage() {
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
            <p className="text-sm">Gestiona las recepciones desde Odoo</p>
            <a
              href="http://localhost:8069/web#action=stock.action_picking_tree_all&type=incoming"
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
