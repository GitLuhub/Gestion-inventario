import { create } from 'zustand'

interface AppState {
  sidebarOpen: boolean
  currentPage: string
  notifications: Notification[]
  
  toggleSidebar: () => void
  setSidebarOpen: (open: boolean) => void
  setCurrentPage: (page: string) => void
  addNotification: (notification: Notification) => void
  removeNotification: (id: string) => void
  clearNotifications: () => void
}

interface Notification {
  id: string
  type: 'success' | 'error' | 'warning' | 'info'
  title: string
  message?: string
  duration?: number
}

export const useAppStore = create<AppState>((set, get) => ({
  sidebarOpen: true,
  currentPage: 'dashboard',
  notifications: [],

  toggleSidebar: () => set((state) => ({ sidebarOpen: !state.sidebarOpen })),
  
  setSidebarOpen: (open: boolean) => set({ sidebarOpen: open }),
  
  setCurrentPage: (page: string) => set({ currentPage: page }),
  
  addNotification: (notification: Notification) => {
    const id = `notification-${Date.now()}`
    const newNotification = { ...notification, id }
    
    set((state) => ({
      notifications: [...state.notifications, newNotification],
    }))
    
    const duration = notification.duration || 5000
    setTimeout(() => {
      get().removeNotification(id)
    }, duration)
  },
  
  removeNotification: (id: string) => {
    set((state) => ({
      notifications: state.notifications.filter((n) => n.id !== id),
    }))
  },
  
  clearNotifications: () => set({ notifications: [] }),
}))
