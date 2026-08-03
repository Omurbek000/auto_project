import type { ReactNode } from 'react'
import { Navigate, useLocation } from 'react-router-dom'
import { useAuth } from '@/features/auth/AuthContext'
import { Spinner } from '@/components/ui'

interface RequireAuthProps {
  children: ReactNode
  adminOnly?: boolean
  ownerOnly?: boolean
}

export function RequireAuth({ children, adminOnly = false, ownerOnly = false }: RequireAuthProps) {
  const { status, isAuthenticated, isAdmin, isOwner } = useAuth()
  const location = useLocation()

  if (status === 'loading') return <Spinner label="Загрузка…" />

  if (!isAuthenticated) {
    return <Navigate to="/login" replace state={{ from: location.pathname }} />
  }

  if (adminOnly && !isAdmin) {
    return <Navigate to="/" replace />
  }

  if (ownerOnly && !isOwner) {
    return <Navigate to="/" replace />
  }

  return <>{children}</>
}

/** Куда вести пользователя после логина в зависимости от роли. */
export function roleHome(user: { is_staff?: boolean; is_owner?: boolean } | null): string {
  if (!user) return '/'
  if (user.is_staff) return '/admin/dashboard'
  if (user.is_owner) return '/owner/stats'
  return '/'
}
