'use client'

import { useAppStore, useAuthStore } from '@/store'
import { Bars3Icon, BellIcon } from '@heroicons/react/24/outline'

export function Header() {
  const { toggleSidebar } = useAppStore()
  const { user } = useAuthStore()

  return (
    <header className="sticky top-0 z-40 bg-white border-b border-gray-200">
      <div className="px-4 py-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between">
          <div className="flex items-center">
            <button
              onClick={toggleSidebar}
              className="p-2 text-gray-500 rounded-lg hover:bg-gray-100 lg:hidden"
            >
              <Bars3Icon className="w-6 h-6" />
            </button>
            <div className="hidden sm:block">
              <h2 className="text-2xl font-semibold text-gray-900">
                Panel de Control
              </h2>
            </div>
          </div>

          <div className="flex items-center space-x-4">
            <button className="relative p-2 text-gray-500 rounded-lg hover:bg-gray-100">
              <BellIcon className="w-6 h-6" />
              <span className="absolute top-1 right-1 w-2 h-2 bg-danger-500 rounded-full"></span>
            </button>
            
            <div className="flex items-center space-x-3">
              <div className="w-10 h-10 rounded-full bg-primary-600 flex items-center justify-center">
                <span className="text-sm font-medium text-white">
                  {user?.username?.charAt(0).toUpperCase() || 'U'}
                </span>
              </div>
              <div className="hidden sm:block">
                <p className="text-sm font-medium text-gray-900">
                  {user?.username || 'Usuario'}
                </p>
              </div>
            </div>
          </div>
        </div>
      </div>
    </header>
  )
}
