import axios, { AxiosError, type InternalAxiosRequestConfig } from 'axios'
import type { LoginResponse } from '@/types/api'

export const API_URL =
  (import.meta.env.VITE_API_URL as string | undefined) ?? 'http://127.0.0.1:8000'

const ACCESS_KEY = 'avto_access'
const REFRESH_KEY = 'avto_refresh'

export const tokenStore = {
  getAccess: () => localStorage.getItem(ACCESS_KEY),
  getRefresh: () => localStorage.getItem(REFRESH_KEY),
  set: (access: string, refresh: string) => {
    localStorage.setItem(ACCESS_KEY, access)
    localStorage.setItem(REFRESH_KEY, refresh)
  },
  setAccess: (access: string) => localStorage.setItem(ACCESS_KEY, access),
  clear: () => {
    localStorage.removeItem(ACCESS_KEY)
    localStorage.removeItem(REFRESH_KEY)
  },
}

export function mediaUrl(path: string | null | undefined): string {
  if (!path) return ''
  if (/^https?:\/\//.test(path)) return path
  return `${API_URL}${path.startsWith('/') ? '' : '/'}${path}`
}

/** Форматирует ошибку API ({detail} | {field:[...]}) в строку для показа. */
export function apiErrorText(err: unknown): string {
  if (axios.isAxiosError(err)) {
    const data = (err as AxiosError<Record<string, unknown>>).response?.data
    if (data) {
      if (typeof data.detail === 'string') return data.detail
      if (typeof data.detail === 'object' && data.detail !== null)
        return JSON.stringify(data.detail)
      const parts: string[] = []
      for (const [field, value] of Object.entries(data)) {
        if (field === 'detail' || field === 'non_field_errors') continue
        const msg = Array.isArray(value) ? value.join(', ') : String(value)
        parts.push(`${field}: ${msg}`)
      }
      if (parts.length) return parts.join('; ')
    }
    if (err.response?.status === 401) return 'Сессия истекла, войдите заново'
    if (!err.response) return 'Нет соединения с сервером'
  }
  return err instanceof Error ? err.message : 'Произошла ошибка'
}

const client = axios.create({
  baseURL: API_URL,
  headers: { 'Content-Type': 'application/json' },
})

client.interceptors.request.use((config) => {
  const access = tokenStore.getAccess()
  if (access) config.headers.Authorization = `Bearer ${access}`
  return config
})

interface RetriableConfig extends InternalAxiosRequestConfig {
  _retried?: boolean
}

let refreshPromise: Promise<string> | null = null

function refreshAccessToken(): Promise<string> {
  const refresh = tokenStore.getRefresh()
  if (!refresh) return Promise.reject(new Error('no refresh token'))
  if (!refreshPromise) {
    refreshPromise = axios
      .post<LoginResponse>(`${API_URL}/token/refresh/`, { refresh })
      .then((res) => {
        const access = res.data.access
        tokenStore.setAccess(access)
        return access
      })
      .finally(() => {
        refreshPromise = null
      })
  }
  return refreshPromise
}

let onUnauthorized: (() => void) | null = null
export function setUnauthorizedHandler(fn: (() => void) | null) {
  onUnauthorized = fn
}

client.interceptors.response.use(
  (res) => res,
  async (error: AxiosError) => {
    const original = error.config as RetriableConfig | undefined
    const status = error.response?.status

    if (status === 401 && original && !original._retried && !original.url?.includes('/token/refresh/')) {
      try {
        const access = await refreshAccessToken()
        original._retried = true
        original.headers.Authorization = `Bearer ${access}`
        return client(original)
      } catch {
        tokenStore.clear()
        onUnauthorized?.()
      }
    }
    return Promise.reject(error)
  },
)

export default client
