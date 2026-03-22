import { create } from 'zustand'
import { persist } from 'zustand/middleware'
import Cookies from 'js-cookie'
import { User, TokenResponse } from '@/types'
import { authService } from '@/services/auth'

interface AuthState {
  user: User | null
  accessToken: string | null
  refreshToken: string | null
  isAuthenticated: boolean
  isLoading: boolean
  error: string | null
  
  login: (username: string, password: string) => Promise<void>
  logout: () => void
  refreshAccessToken: () => Promise<void>
  setError: (error: string | null) => void
  clearError: () => void
}

export const useAuthStore = create<AuthState>()(
  persist(
    (set, get) => ({
      user: null,
      accessToken: null,
      refreshToken: null,
      isAuthenticated: false,
      isLoading: false,
      error: null,

      login: async (username: string, password: string) => {
        set({ isLoading: true, error: null })
        try {
          const response = await authService.login(username, password)
          
          Cookies.set('access_token', response.access_token, {
            expires: response.expires_in / 86400,
            secure: process.env.NODE_ENV === 'production',
            sameSite: 'strict',
          })
          
          if (response.refresh_token) {
            Cookies.set('refresh_token', response.refresh_token, {
              expires: 7,
              secure: process.env.NODE_ENV === 'production',
              sameSite: 'strict',
            })
          }
          
          set({
            accessToken: response.access_token,
            refreshToken: response.refresh_token || null,
            isAuthenticated: true,
            isLoading: false,
            user: { username, user_id: 0 },
          })
        } catch (error: any) {
          set({
            error: error.message || 'Error al iniciar sesión',
            isLoading: false,
            isAuthenticated: false,
          })
          throw error
        }
      },

      logout: () => {
        Cookies.remove('access_token')
        Cookies.remove('refresh_token')
        set({
          user: null,
          accessToken: null,
          refreshToken: null,
          isAuthenticated: false,
          error: null,
        })
      },

      refreshAccessToken: async () => {
        const refreshToken = get().refreshToken || Cookies.get('refresh_token')
        if (!refreshToken) {
          get().logout()
          return
        }
        
        try {
          const response = await authService.refresh(refreshToken)
          
          Cookies.set('access_token', response.access_token, {
            expires: response.expires_in / 86400,
            secure: process.env.NODE_ENV === 'production',
            sameSite: 'strict',
          })
          
          set({
            accessToken: response.access_token,
            refreshToken: response.refresh_token || null,
          })
        } catch (error) {
          get().logout()
        }
      },

      setError: (error: string | null) => set({ error }),
      clearError: () => set({ error: null }),
    }),
    {
      name: 'auth-storage',
      partialize: (state) => ({
        user: state.user,
        isAuthenticated: state.isAuthenticated,
      }),
    }
  )
)
