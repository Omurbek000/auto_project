import type { ReactNode } from 'react'
import { Star, StarHalf } from 'lucide-react'
import type { ComplaintStatus, RentalStatus } from '@/types/api'

const rentalLabels: Record<RentalStatus, string> = {
  pending: 'Ожидает',
  confirmed: 'Подтверждена',
  active: 'Активна',
  completed: 'Завершена',
  canceled: 'Отменена',
}

const complaintLabels: Record<ComplaintStatus, string> = {
  pending: 'На рассмотрении',
  reviewing: 'Рассматривается',
  resolved: 'Решена',
  rejected: 'Отклонена',
}

export function rentalStatusClass(s: RentalStatus): string {
  return `st-${s}`
}

export function complaintStatusClass(s: ComplaintStatus): string {
  return `st-${s}`
}

export function Spinner({ label }: { label?: string }) {
  return (
    <div className="center-box">
      <div className="spinner" role="status" aria-label="Загрузка" />
      {label && <span>{label}</span>}
    </div>
  )
}

export function EmptyState({ icon, text }: { icon?: ReactNode; text: string }) {
  return (
    <div className="empty">
      {icon && <div style={{ marginBottom: 10, opacity: 0.6 }}>{icon}</div>}
      {text}
    </div>
  )
}

export function ErrorBox({ text }: { text: string }) {
  return (
    <div className="glass glass-card" style={{ borderColor: 'rgba(239,68,68,0.4)', color: '#f87171' }}>
      {text}
    </div>
  )
}

export function RentStatusBadge({ status }: { status: RentalStatus }) {
  return (
    <span className={`badge ${rentalStatusClass(status)}`}>
      <span className="b-dot" />
      {rentalLabels[status] ?? status}
    </span>
  )
}

export function ComplaintStatusBadge({ status }: { status: ComplaintStatus }) {
  return (
    <span className={`badge ${complaintStatusClass(status)}`}>
      <span className="b-dot" />
      {complaintLabels[status] ?? status}
    </span>
  )
}

export function Stars({ rating }: { rating: number | null }) {
  if (rating === null || rating === undefined) return <span className="muted">нет оценок</span>
  const full = Math.floor(rating)
  const hasHalf = rating - full >= 0.5
  return (
    <span className="stars" aria-label={`Рейтинг ${rating}`}>
      {Array.from({ length: full }).map((_, i) => (
        <Star key={i} fill="currentColor" strokeWidth={0} />
      ))}
      {hasHalf && <StarHalf fill="currentColor" strokeWidth={0} />}
      {Array.from({ length: 5 - full - (hasHalf ? 1 : 0) }).map((_, i) => (
        <Star key={`e${i}`} />
      ))}
      <span className="rating-num" style={{ marginLeft: 4 }}>
        {rating.toFixed(1)}
      </span>
    </span>
  )
}

interface PaginationProps {
  count: number
  page: number
  pageSize: number
  onPage: (page: number) => void
}

export function Pagination({ count, page, pageSize, onPage }: PaginationProps) {
  const pages = Math.max(1, Math.ceil(count / pageSize))
  if (count <= pageSize) return null
  return (
    <nav className="pager" aria-label="Пагинация">
      <button className="btn btn-sm" disabled={page <= 1} onClick={() => onPage(page - 1)}>
        ←
      </button>
      <span className="pager-info">
        стр. {page} из {pages} · {count} всего
      </span>
      <button className="btn btn-sm" disabled={page >= pages} onClick={() => onPage(page + 1)}>
        →
      </button>
    </nav>
  )
}

interface ModalProps {
  open: boolean
  title: string
  onClose: () => void
  children: ReactNode
}

export function Modal({ open, title, onClose, children }: ModalProps) {
  if (!open) return null
  return (
    <div className="modal-backdrop" onClick={onClose}>
      <div
        className="modal"
        role="dialog"
        aria-modal="true"
        aria-label={title}
        onClick={(e) => e.stopPropagation()}
      >
        <h3>{title}</h3>
        {children}
      </div>
    </div>
  )
}

export function formatDate(d: string): string {
  if (!d) return ''
  return d.slice(0, 10)
}
