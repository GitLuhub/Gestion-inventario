import { apiClient, getToken } from './api'
import { TokenResponse } from '@/types'

export const authService = {
  login: async (username: string, password: string): Promise<TokenResponse> => {
    const formData = new URLSearchParams()
    formData.append('username', username)
    formData.append('password', password)
    
    const response = await fetch(
      `${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}/api/v1/auth/login`,
      {
        method: 'POST',
        headers: {
          'Content-Type': 'application/x-www-form-urlencoded',
        },
        body: formData,
      }
    )
    
    if (!response.ok) {
      const error = await response.json().catch(() => ({ detail: 'Error de autenticación' }))
      throw new Error(error.detail || 'Credenciales incorrectas')
    }
    
    return response.json()
  },
  
  refresh: async (refreshToken: string): Promise<TokenResponse> => {
    return apiClient.post<TokenResponse>('/api/v1/auth/refresh', { refresh_token: refreshToken })
  },
  
  logout: async (): Promise<void> => {
    const token = getToken()
    if (token) {
      await apiClient.post('/api/v1/auth/logout', undefined, { token })
    }
  },
  
  getCurrentUser: async () => {
    const token = getToken()
    if (!token) throw new Error('No autenticado')
    return apiClient.get('/api/v1/auth/me', { token })
  },
}
