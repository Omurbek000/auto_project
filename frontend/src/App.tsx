import { BrowserRouter, Navigate, Route, Routes } from 'react-router-dom'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { AuthProvider } from '@/features/auth/AuthContext'
import { RequireAuth } from '@/features/auth/RequireAuth'
import { ToastProvider } from '@/components/Toast'
import { MainLayout } from '@/layouts/Layouts'
import { HomePage } from '@/pages/HomePage'
import { LoginPage } from '@/pages/auth/LoginPage'
import { RegisterPage } from '@/pages/auth/RegisterPage'
import { CarDetailPage } from '@/pages/CarDetailPage'
import { ProfilePage } from '@/pages/ProfilePage'
import { RentalsPage } from '@/pages/RentalsPage'
import { FavoritesPage } from '@/pages/FavoritesPage'
import { MyCarsPage } from '@/pages/MyCarsPage'
import { OwnerStatsPage } from '@/pages/OwnerStatsPage'
import { ChatsPage } from '@/pages/chat/ChatsPage'
import { ChatPage } from '@/pages/chat/ChatPage'
import { ComplaintsPage } from '@/pages/ComplaintsPage'
import { AdminDashboardPage } from '@/pages/admin/AdminDashboardPage'
import { AdminUsersPage } from '@/pages/admin/AdminUsersPage'
import { AdminComplaintsPage } from '@/pages/admin/AdminComplaintsPage'
import { AdminAuditPage } from '@/pages/admin/AdminAuditPage'

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 30_000,
      retry: 1,
      refetchOnWindowFocus: false,
    },
  },
})

export default function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>
        <AuthProvider>
          <ToastProvider>
            <Routes>
              <Route element={<MainLayout />}>
                <Route path="/" element={<HomePage />} />
                <Route path="/car/:id" element={<CarDetailPage />} />

                <Route path="/profile" element={<RequireAuth><ProfilePage /></RequireAuth>} />
                <Route path="/rentals" element={<RequireAuth><RentalsPage /></RequireAuth>} />
                <Route path="/favorites" element={<RequireAuth><FavoritesPage /></RequireAuth>} />
                <Route path="/chat" element={<RequireAuth><ChatsPage /></RequireAuth>} />
                <Route path="/chat/:id" element={<RequireAuth><ChatPage /></RequireAuth>} />
                <Route path="/complaints" element={<RequireAuth><ComplaintsPage /></RequireAuth>} />

                <Route path="/my-cars" element={<RequireAuth ownerOnly><MyCarsPage /></RequireAuth>} />
                <Route path="/owner/stats" element={<RequireAuth ownerOnly><OwnerStatsPage /></RequireAuth>} />

                <Route path="/admin/dashboard" element={<RequireAuth adminOnly><AdminDashboardPage /></RequireAuth>} />
                <Route path="/admin/users" element={<RequireAuth adminOnly><AdminUsersPage /></RequireAuth>} />
                <Route path="/admin/complaints" element={<RequireAuth adminOnly><AdminComplaintsPage /></RequireAuth>} />
                <Route path="/admin/audit" element={<RequireAuth adminOnly><AdminAuditPage /></RequireAuth>} />
              </Route>

              <Route path="/login" element={<LoginPage />} />
              <Route path="/register" element={<RegisterPage />} />
              <Route path="*" element={<Navigate to="/" replace />} />
            </Routes>
          </ToastProvider>
        </AuthProvider>
      </BrowserRouter>
    </QueryClientProvider>
  )
}
