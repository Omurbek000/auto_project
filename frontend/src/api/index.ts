import client from './client'
import type {
  AdminAnalytics,
  Analytics,
  AuditLogEntry,
  Car,
  CarCalendar,
  CarCreate,
  Chat,
  ChatMessage,
  Complaint,
  ComplaintCreate,
  ComplaintStatus,
  Favorite,
  Feedback,
  GlobalStats,
  LoginResponse,
  Operation,
  OwnerStats,
  Paginated,
  Rental,
  RentalCreate,
  User,
} from '@/types/api'

type Params = Record<string, string | number | boolean | undefined>

// ===== Авторизация и пользователи =====
export const authApi = {
  register: (data: { username: string; email: string; password: string; is_owner?: boolean }) =>
    client.post<{ username: string; email: string; is_owner: boolean }>('/register/', data),
  login: (data: { username: string; password: string }) =>
    client.post<LoginResponse>('/login/', data),
  logout: (refresh: string) => client.post('/logout/', { refresh }),
  me: () => client.get<User>('/users/'),
  updateProfile: (id: number, data: Partial<User>) => client.patch<User>(`/users/${id}/`, data),
  uploadAvatar: (id: number, file: File) => {
    const form = new FormData()
    form.append('avatar', file)
    return client.patch<User>(`/users/${id}/`, form, {
      headers: { 'Content-Type': 'multipart/form-data' },
    })
  },
  passwordChange: (data: { old_password: string; new_password: string }) =>
    client.post('/password/change/', data),
  passwordReset: (email: string) => client.post('/password/reset/', { email }),
  passwordResetConfirm: (data: { email: string; code: string; new_password: string }) =>
    client.post('/password/reset/confirm/', data),
  sendVerification: (verification_type: 'email' | 'phone') =>
    client.post('/verification/send/', { verification_type }),
  confirmVerification: (data: { verification_type: 'email' | 'phone'; code: string }) =>
    client.post('/verification/confirm/', data),
}

// ===== Автомобили =====
export const carApi = {
  list: (params: Params = {}) => client.get<Paginated<Car>>('/car/', { params }),
  my: (params: Params = {}) => client.get<Paginated<Car>>('/car/my/', { params }),
  available: (start_date: string, end_date: string, params: Params = {}) =>
    client.get<Paginated<Car>>('/car/available/', { params: { ...params, start_date, end_date } }),
  detail: (id: number) => client.get<Car>(`/car/${id}/`),
  create: (data: CarCreate) => client.post<Car>('/car/', data),
  update: (id: number, data: Partial<CarCreate>) => client.patch<Car>(`/car/${id}/`, data),
  remove: (id: number) => client.delete(`/car/${id}/`),
  calendar: (id: number, year: number, month: number) =>
    client.get<CarCalendar>(`/car/${id}/calendar/`, { params: { year, month } }),
  uploadImage: (carId: number, file: File) => {
    const form = new FormData()
    form.append('car_id', String(carId))
    form.append('image', file)
    return client.post('/car/image/upload/', form, {
      headers: { 'Content-Type': 'multipart/form-data' },
    })
  },
  bulkUploadImages: (carId: number, files: File[]) => {
    const form = new FormData()
    form.append('car_id', String(carId))
    files.forEach((f) => form.append('images', f))
    return client.post('/car/image/bulk-upload/', form, {
      headers: { 'Content-Type': 'multipart/form-data' },
    })
  },
  deleteImage: (imageId: number) => client.delete(`/car/image/${imageId}/`),
  setMainImage: (imageId: number) => client.post(`/car/image/${imageId}/set-main/`),
  unavailable: (carId: number, data?: { start_date: string; end_date: string; reason?: string }) =>
    client.post(`/car/${carId}/unavailable/`, data),
}

// ===== Аренда =====
export const rentalApi = {
  list: (params: Params = {}) => client.get<Paginated<Rental>>('/rental/', { params }),
  detail: (id: number) => client.get<Rental>(`/rental/${id}/`),
  create: (data: RentalCreate) => client.post<Rental>('/rental/', data),
  update: (id: number, data: Partial<{ start_date: string; end_date: string }>) =>
    client.patch<Rental>(`/rental/${id}/`, data),
  confirm: (id: number) => client.post<Rental>(`/rental/${id}/confirm/`),
  reject: (id: number) => client.post(`/rental/${id}/reject/`),
  start: (id: number) => client.post<Rental>(`/rental/${id}/start/`),
  complete: (id: number) => client.post<Rental>(`/rental/${id}/complete/`),
}

// ===== Отзывы =====
export const feedbackApi = {
  list: (params: Params = {}) => client.get<Paginated<Feedback>>('/feedback/', { params }),
  create: (data: { rental_id: number; feedback_type: 'car' | 'renter'; rating: number; comment?: string }) =>
    client.post<Feedback>('/feedback/', data),
  update: (id: number, data: Partial<{ rating: number; comment: string }>) =>
    client.patch<Feedback>(`/feedback/${id}/`, data),
  remove: (id: number) => client.delete(`/feedback/${id}/`),
}

// ===== Избранное =====
export const favoriteApi = {
  list: (params: Params = {}) => client.get<Paginated<Favorite>>('/favorites/', { params }),
  add: (car_id: number) => client.post<Favorite>('/favorites/', { car_id }),
  remove: (id: number) => client.delete(`/favorites/${id}/`),
}

// ===== Чат =====
export const chatApi = {
  list: (params: Params = {}) => client.get<Paginated<Chat>>('/chat/', { params }),
  detail: (id: number) => client.get<Chat>(`/chat/${id}/`),
  markRead: (id: number) => client.post(`/chat/${id}/read/`),
  send: (chat_id: number, message: string) =>
    client.post<ChatMessage>('/chat/message/', { chat_id, message }),
}

// ===== Жалобы =====
export const complaintApi = {
  list: (params: Params = {}) => client.get<Paginated<Complaint>>('/complaints/', { params }),
  create: (data: ComplaintCreate) => client.post<Complaint>('/complaints/', data),
  detail: (id: number) => client.get<Complaint>(`/complaints/${id}/`),
  update: (id: number, data: Partial<{ status: ComplaintStatus; admin_response: string }>) =>
    client.patch<Complaint>(`/complaints/${id}/`, data),
}

// ===== Статистика и личный кабинет =====
export const statsApi = {
  global: () => client.get<GlobalStats>('/stats/'),
  owner: () => client.get<OwnerStats>('/owner/stats/'),
  analytics: () => client.get<Analytics>('/analytics/'),
  operations: (params: Params = {}) => client.get<Paginated<Operation>>('/operations/', { params }),
}

// ===== Админ =====
export const adminApi = {
  users: (params: Params = {}) => client.get<Paginated<User>>('/admin/users/', { params }),
  userDetail: (id: number) => client.get<User>(`/admin/users/${id}/`),
  updateUser: (id: number, data: Partial<Record<string, unknown>>) =>
    client.patch<User>(`/admin/users/${id}/`, data),
  analytics: () => client.get<AdminAnalytics>('/admin/analytics/'),
  operations: (params: Params = {}) => client.get<Paginated<Operation>>('/admin/operations/', { params }),
  audit: (params: Params = {}) => client.get<Paginated<AuditLogEntry>>('/admin/audit/', { params }),
}
