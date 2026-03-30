import { create } from 'zustand'
import { persist } from 'zustand/middleware'
import Cookies from 'js-cookie'
import { User, TokenResponse } from '@/types'
import { authService } from '@/services/auth'
import { setRefreshCallback, clearRefreshCallback } from '@/services/api'

interface AuthState {
  user: User | null
  accessToken: string | null
  isAuthenticated: boolean
  isLoading: boolean
  error: string | null

  login: (username: string, password: string) => Promise<void>
  logout: () => void
  refreshAccessToken: () => Promise<string | null>
  setError: (error: string | null) => void
  clearError: () => void
}

export const useAuthStore = create<AuthState>()(
  persist(
    (set, get) => ({
      user: null,
      accessToken: null,
      isAuthenticated: false,
      isLoading: false,
      error: null,

      login: async (username: string, password: string) => {
        set({ isLoading: true, error: null })
        try {
          const response = await authService.login(username, password)

          // access_token: cookie JS-accesible (short-lived, 30 min)
          Cookies.set('access_token', response.access_token, {
            expires: response.expires_in / 86400,
            secure: process.env.NODE_ENV === 'production',
            sameSite: 'strict',
          })

          // G2: refresh_token ya NO se almacena aquí —
          // el servidor lo escribe en una cookie httpOnly automáticamente.

          // G3: registra el callback de refresco para el interceptor de api.ts
          setRefreshCallback(get().refreshAccessToken)

          set({
            accessToken: response.access_token,
            isAuthenticated: true,
            isLoading: false,
            user: { username, user_id: 0 },
          })
        } catch (error: unknown) {
          const message = error instanceof Error ? error.message : 'Error al iniciar sesión'
          set({ error: message, isLoading: false, isAuthenticated: false })
          throw error
        }
      },

      logout: () => {
        Cookies.remove('access_token')
        // G3: elimina el callback — peticiones futuras no intentarán refrescar
        clearRefreshCallback()
        set({
          user: null,
          accessToken: null,
          isAuthenticated: false,
          error: null,
        })
      },

      /**
       * G3: Llama a /auth/refresh (cookie httpOnly se envía automáticamente).
       * Retorna el nuevo access token o null si falla.
       */
      refreshAccessToken: async (): Promise<string | null> => {
        try {
          const response = await authService.refresh()

          Cookies.set('access_token', response.access_token, {
            expires: response.expires_in / 86400,
            secure: process.env.NODE_ENV === 'production',
            sameSite: 'strict',
          })

          set({ accessToken: response.access_token })
          return response.access_token
        } catch {
          get().logout()
          return null
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
      // G3: re-registra el callback tras rehidratar desde localStorage
      onRehydrateStorage: () => (state) => {
        if (state?.isAuthenticated) {
          setRefreshCallback(state.refreshAccessToken)
        }
      },
    }
  )
)
