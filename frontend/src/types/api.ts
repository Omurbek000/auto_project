export type FuelType = 'petrol' | 'diesel' | 'electric' | 'hybrid'
export type Transmission = 'manual' | 'auto'
export type RentalStatus = 'pending' | 'confirmed' | 'active' | 'completed' | 'canceled'
export type ComplaintStatus = 'pending' | 'reviewing' | 'resolved' | 'rejected'
export type FeedbackType = 'car' | 'renter'
export type CalendarStatus = 'free' | 'booked' | 'blocked' | 'past'

export interface User {
  id: number
  username: string
  first_name: string
  last_name: string
  email: string
  phone_number: string | null
  is_owner: boolean
  is_renter: boolean
  is_staff: boolean
  is_active: boolean
  avatar: string | null
  bio: string | null
  date_of_birth: string | null
  age: number | null
  driving_license_number: string | null
  driving_license_date: string | null
  driving_experience: number | null
  languages: string | null
  email_verified: boolean
  phone_verified: boolean
  is_verified: boolean
  renter_rating: number | null
  renter_rating_count: number
  owner_rating: number | null
  owner_rating_count: number
  created_date: string
}

export interface LoginResponse {
  user: User
  access: string
  refresh: string
}

export interface Paginated<T> {
  count: number
  next: string | null
  previous: string | null
  results: T[]
}

export interface CarImage {
  id: number
  image: string
  is_main: boolean
  created_date: string
}

export interface Car {
  id: number
  brand: string
  model_name: string
  year: number
  fuel_type: FuelType
  transmission: Transmission
  mileage: number
  price_per_day: string
  description: string
  location: string
  image: string | null
  images: CarImage[]
  owner: User
  is_available: boolean
  average_rating: number | null
  feedbacks_count: number
  min_age: number
  min_driving_experience: number
  deposit: string
  cancellation_policy: string | null
  unavailable_dates: string[]
  created_date: string
}

export interface CarCreate {
  brand: string
  model_name: string
  year: number
  fuel_type: FuelType
  transmission: Transmission
  mileage: number
  price_per_day: string
  description?: string
  location: string
  deposit?: string
}

export interface Rental {
  id: number
  car: Car
  renter: User
  start_date: string
  end_date: string
  total_price: string
  status: RentalStatus
  created_date: string
}

export interface RentalCreate {
  car_id: number
  start_date: string
  end_date: string
}

export interface Feedback {
  id: number
  rental: number | Rental
  rental_id?: number
  feedback_type: FeedbackType
  author: User
  rating: number
  comment: string
  created_date: string
}

export interface Chat {
  id: number
  rental: Rental
  messages: ChatMessage[]
  created_date: string
}

export interface ChatMessage {
  id: number
  chat: number
  sender: User
  message: string
  created_date: string
  is_read: boolean
}

export interface Complaint {
  id: number
  author: User
  target_user: User | null
  rental: number | null
  reason: string
  description: string
  status: ComplaintStatus
  admin_response: string | null
  created_date: string
  updated_date: string
}

export interface ComplaintCreate {
  target_user_id: number
  rental?: number
  reason: string
  details?: string
}

export interface Favorite {
  id: number
  car: Car
  created_date: string
}

export interface CalendarDay {
  date: string
  status: CalendarStatus
}

export interface CarCalendar {
  car_id: number
  year: number
  month: number
  days: CalendarDay[]
}

export interface GlobalStats {
  total_cars: number
  total_users: number
  total_rentals: number
  active_rentals: number
  pending_rentals: number
  pending_complaints: number
  total_days_rented?: number
}

export interface OwnerStats {
  total_earnings: number
  total_rentals: number
  cars_count: number
  average_rating: number | null
  popular_car: {
    id: number
    brand: string
    model_name: string
    rental_count: number
  } | null
  monthly_revenue: number
}

export interface Analytics {
  rentals_by_status: Record<string, number>
  total_rentals: number
  revenue_total?: number
  revenue_by_month?: { month: string; revenue: number }[]
  cars_by_brand?: { brand: string; count: number }[]
  cars_rental_days?: { id: number; brand: string; model_name: string; rental_days: number; rental_count: number }[]
}

export interface AdminAnalytics {
  total_users: number
  total_cars: number
  total_rentals: number
  active_rentals: number
  pending_rentals: number
  pending_complaints: number
  rentals_by_month: { month: string; count: number }[]
  cars_by_brand: { brand: string; count: number }[]
  rentals_by_status: Record<string, number>
  top_cars_by_days: { id: number; brand: string; model_name: string; rental_days: number }[]
}

export interface Operation {
  id: number
  type: string
  date: string
  status?: string
  amount?: string | number | null
  description: string
  username?: string
  model_name?: string
}

export interface AuditLogEntry {
  id: number
  user: number | null
  username: string | null
  action: string
  model_name: string
  object_id: number | null
  details: Record<string, unknown> | null
  created_date: string
}
