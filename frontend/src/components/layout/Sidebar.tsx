'use client'

import Link from 'next/link'
import { usePathname } from 'next/navigation'
import { useAuthStore, useAppStore } from '@/store'
import { cn } from '@/lib/utils'
import {
  HomeIcon,
  CubeIcon,
  MapPinIcon,
  ArrowDownTrayIcon,
  ArrowUpTrayIcon,
  AdjustmentsHorizontalIcon,
  ChartBarIcon,
  Cog6ToothIcon,
  ArrowRightStartOnRectangleIcon,
} from '@heroicons/react/24/outline'

const navigation = [
  { name: 'Dashboard', href: '/dashboard', icon: HomeIcon, exact: true },
  { name: 'Productos', href: '/dashboard/products', icon: CubeIcon, exact: false },
  { name: 'Inventario', href: '/dashboard/inventory', icon: AdjustmentsHorizontalIcon, exact: true },
  { name: 'Ubicaciones', href: '/dashboard/locations', icon: MapPinIcon, exact: true },
  { name: 'Recepciones', href: '/dashboard/receipts', icon: ArrowDownTrayIcon, exact: true },
  { name: 'Entregas', href: '/dashboard/deliveries', icon: ArrowUpTrayIcon, exact: true },
  { name: 'Informes', href: '/dashboard/reports', icon: ChartBarIcon, exact: true },
]

export function Sidebar() {
  const pathname = usePathname()
  const { logout } = useAuthStore()
  const { sidebarOpen } = useAppStore()

  return (
    <div className={cn(
      'fixed inset-y-0 left-0 z-50 w-64 bg-gray-900 transform transition-transform duration-300 ease-in-out lg:translate-x-0',
      sidebarOpen ? 'translate-x-0' : '-translate-x-full'
    )}>
      <div className="flex flex-col h-full">
        <div className="flex items-center justify-center h-16 px-4 bg-gray-800">
          <h1 className="text-xl font-bold text-white">Gestión Inventario</h1>
        </div>
        
        <nav className="flex-1 px-2 py-4 space-y-1 overflow-y-auto">
          {navigation.map((item) => {
            const isActive = item.exact
              ? pathname === item.href
              : pathname === item.href || pathname.startsWith(item.href + '/')
            return (
              <Link
                key={item.name}
                href={item.href}
                className={cn(
                  'flex items-center px-4 py-3 text-sm font-medium rounded-lg transition-colors',
                  isActive
                    ? 'bg-primary-600 text-white'
                    : 'text-gray-300 hover:bg-gray-700 hover:text-white'
                )}
              >
                <item.icon className="w-5 h-5 mr-3" />
                {item.name}
              </Link>
            )
          })}
        </nav>

        <div className="p-4 border-t border-gray-700">
          <Link
            href="/settings"
            className="flex items-center px-4 py-2 text-sm font-medium text-gray-300 rounded-lg hover:bg-gray-700 hover:text-white transition-colors"
          >
            <Cog6ToothIcon className="w-5 h-5 mr-3" />
            Configuración
          </Link>
          <button
            onClick={() => logout()}
            className="flex items-center w-full px-4 py-2 mt-2 text-sm font-medium text-gray-300 rounded-lg hover:bg-gray-700 hover:text-white transition-colors"
          >
            <ArrowRightStartOnRectangleIcon className="w-5 h-5 mr-3" />
            Cerrar Sesión
          </button>
        </div>
      </div>
    </div>
  )
}
