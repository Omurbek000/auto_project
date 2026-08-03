import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useState,
  type ReactNode,
} from 'react'
import { authApi } from '@/api'
import { setUnauthorizedHandler, tokenStore } from '@/api/client'
import type { User } from '@/types/api'

type AuthStatus = 'loading' | 'authenticated' | 'guest'

interface AuthContextValue {
  user: User | null
  status: AuthStatus
  isAuthenticated: boolean
  isOwner: boolean
  isAdmin: boolean
  login: (username: string, password: string) => Promise<User>
  register: (data: { username: string; email: string; password: string; is_owner?: boolean }) => Promise<User>
  logout: () => Promise<void>
  refreshUser: () => Promise<void>
  setUser: (user: User) => void
}

const AuthContext = createContext<AuthContextValue | null>(null)

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null)
  const [status, setStatus] = useState<AuthStatus>('loading')

  const loadMe = useCallback(async () => {
    try {
      const res = await authApi.me()
      setUser(res.data)
      setStatus('authenticated')
    } catch {
      tokenStore.clear()
      setUser(null)
      setStatus('guest')
    }
  }, [])

  useEffect(() => {
    if (tokenStore.getAccess()) {
      void loadMe()
    } else {
      setStatus('guest')
    }
  }, [loadMe])

  useEffect(() => {
    setUnauthorizedHandler(() => {
      setUser(null)
      setStatus('guest')
    })
    return () => setUnauthorizedHandler(null)
  }, [])

  const login = useCallback(async (username: string, password: string) => {
    const res = await authApi.login({ username, password })
    tokenStore.set(res.data.access, res.data.refresh)
    setUser(res.data.user)
    setStatus('authenticated')
    void authApi.me().then((r) => setUser(r.data)).catch(() => undefined)
    return res.data.user
  }, [])

  const register = useCallback(
    async (data: { username: string; email: string; password: string; is_owner?: boolean }) => {
      const res = await authApi.register(data)
      await login(data.username, data.password)
      return res.data as unknown as User
    },
    [login],
  )

  const logout = useCallback(async () => {
    const refresh = tokenStore.getRefresh()
    if (refresh) {
      try {
        await authApi.logout(refresh)
      } catch {
        // токен уже мог истечь — игнорируем
      }
    }
    tokenStore.clear()
    setUser(null)
    setStatus('guest')
  }, [])

  const refreshUser = useCallback(async () => {
    await loadMe()
  }, [loadMe])

  const value = useMemo<AuthContextValue>(
    () => ({
      user,
      status,
      isAuthenticated: status === 'authenticated',
      isOwner: !!user?.is_owner,
      isAdmin: !!user?.is_staff,
      login,
      register,
      logout,
      refreshUser,
      setUser,
    }),
    [user, status, login, register, logout, refreshUser],
  )

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>
}

export function useAuth(): AuthContextValue {
  const ctx = useContext(AuthContext)
  if (!ctx) throw new Error('useAuth must be used within AuthProvider')
  return ctx
}
