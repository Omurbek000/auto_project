import { useState } from 'react'
import { Link } from 'react-router-dom'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { z } from 'zod'
import { Car, MessageSquare, Star } from 'lucide-react'
import { chatApi, feedbackApi, rentalApi } from '@/api'
import { apiErrorText, mediaUrl } from '@/api/client'
import { useAuth } from '@/features/auth/AuthContext'
import { EmptyState, ErrorBox, Modal, Pagination, RentStatusBadge, Spinner } from '@/components/ui'
import { ComplaintModal } from '@/components/ComplaintModal'
import { SidebarLayout, type SideNavItem } from '@/layouts/Layouts'
import { useToast } from '@/components/Toast'
import type { Rental, RentalStatus } from '@/types/api'

const PAGE_SIZE = 10

const NAV: SideNavItem[] = [
  { to: '/rentals', label: 'Мои аренды', icon: <Car size={17} /> },
  { to: '/favorites', label: 'Избранное', icon: <Star size={17} /> },
  { to: '/profile', label: 'Профиль', icon: <MessageSquare size={17} /> },
]

const STATUS_TABS: { key: '' | RentalStatus; label: string }[] = [
  { key: '', label: 'Все' },
  { key: 'pending', label: 'Ожидают' },
  { key: 'confirmed', label: 'Подтверждены' },
  { key: 'active', label: 'Активные' },
  { key: 'completed', label: 'Завершённые' },
  { key: 'canceled', label: 'Отменённые' },
]

const reviewSchema = z.object({
  rating: z.coerce.number().min(1, 'Выберите оценку').max(5),
  comment: z.string().max(500).optional(),
})
type ReviewForm = z.infer<typeof reviewSchema>

function FeedbackModal({ rental }: { rental: Rental }) {
  const { user } = useAuth()
  const toast = useToast()
  const qc = useQueryClient()
  const [open, setOpen] = useState(false)
  const [hovered, setHovered] = useState(0)
  const isRenter = user?.id === rental.renter.id

  const { register, handleSubmit, setValue, watch, formState: { errors } } = useForm<
    z.input<typeof reviewSchema>,
    unknown,
    z.output<typeof reviewSchema>
  >({
    resolver: zodResolver(reviewSchema),
    defaultValues: { rating: 0, comment: '' },
  })
  const rating = Number(watch('rating')) || 0

  const mutation = useMutation({
    mutationFn: (data: ReviewForm) =>
      feedbackApi.create({
        rental_id: rental.id,
        feedback_type: isRenter ? 'car' : 'renter',
        rating: data.rating,
        comment: data.comment,
      }),
    onSuccess: () => {
      toast.success('Отзыв отправлен')
      setOpen(false)
      void qc.invalidateQueries({ queryKey: ['rentals'] })
    },
    onError: (err) => toast.error(apiErrorText(err)),
  })

  return (
    <>
      <button className="btn btn-sm btn-success" onClick={() => setOpen(true)}>
        <Star size={14} /> Отзыв
      </button>
      <Modal open={open} title={isRenter ? 'Отзыв на машину' : 'Отзыв на арендатора'} onClose={() => setOpen(false)}>
        <form
          onSubmit={handleSubmit((d) => mutation.mutate(d))}
          noValidate
          style={{ display: 'grid', gap: 14 }}
        >
          <div>
            <div className="muted text-sm mb-8">
              {isRenter ? rental.car.brand + ' ' + rental.car.model_name : 'Об арендаторе ' + rental.renter.username}
            </div>
            <div className="stars" style={{ gap: 6 }}>
              {[1, 2, 3, 4, 5].map((n) => (
                <button
                  key={n}
                  type="button"
                  onClick={() => { setValue('rating', n); setHovered(n) }}
                  onMouseEnter={() => setHovered(n)}
                  onMouseLeave={() => setHovered(rating)}
                  aria-label={`Оценка ${n}`}
                  style={{ background: 'none', border: 'none', cursor: 'pointer', padding: 0 }}
                >
                  <Star size={26} fill={n <= (hovered || rating) ? 'currentColor' : 'none'} className={n <= (hovered || rating) ? '' : 'muted'} style={{ color: n <= (hovered || rating) ? '#fbbf24' : 'inherit' }} />
                </button>
              ))}
              <input type="hidden" {...register('rating')} />
            </div>
            {errors.rating && <span className="field-error" role="alert">{errors.rating.message}</span>}
          </div>
          <div className="field" style={{ margin: 0 }}>
            <label htmlFor="review-comment">Комментарий</label>
            <textarea id="review-comment" className="input" {...register('comment')} placeholder="Впечатления от аренды…" />
          </div>
          <div className="row" style={{ justifyContent: 'flex-end' }}>
            <button type="button" className="btn btn-ghost" onClick={() => setOpen(false)}>Отмена</button>
            <button type="submit" className="btn btn-primary" disabled={mutation.isPending}>
              {mutation.isPending ? 'Отправляем…' : 'Отправить отзыв'}
            </button>
          </div>
        </form>
      </Modal>
    </>
  )
}

function RentalActions({ rental, chatId }: { rental: Rental; chatId?: number | null }) {
  const { user } = useAuth()
  const toast = useToast()
  const qc = useQueryClient()
  const isOwner = user?.id === rental.car.owner.id
  const isRenter = user?.id === rental.renter.id

  const run = useMutation({
    mutationFn: (fn: (id: number) => Promise<unknown>) => fn(rental.id),
    onSuccess: () => {
      toast.success('Готово')
      void qc.invalidateQueries({ queryKey: ['rentals'] })
    },
    onError: (err) => toast.error(apiErrorText(err)),
  })

  return (
    <div className="row" style={{ gap: 8, flexWrap: 'wrap', justifyContent: 'flex-end' }}>
      {rental.status === 'pending' && isOwner && (
        <>
          <button className="btn btn-sm btn-success" disabled={run.isPending} onClick={() => run.mutate(rentalApi.confirm)}>
            Подтвердить
          </button>
          <button className="btn btn-sm btn-danger" disabled={run.isPending} onClick={() => run.mutate(rentalApi.reject)}>
            Отклонить
          </button>
        </>
      )}
      {rental.status === 'confirmed' && isRenter && (
        <button className="btn btn-sm btn-primary" disabled={run.isPending} onClick={() => run.mutate(rentalApi.start)}>
          Начать аренду
        </button>
      )}
      {rental.status === 'active' && isRenter && (
        <button className="btn btn-sm btn-success" disabled={run.isPending} onClick={() => run.mutate(rentalApi.complete)}>
          Завершить аренду
        </button>
      )}
      {rental.status === 'completed' && <FeedbackModal rental={rental} />}
      {rental.status !== 'pending' && <ComplaintModal rental={rental} />}
      {chatId ? (
        <Link to={`/chat/${chatId}`} className="btn btn-sm btn-ghost">
          <MessageSquare size={14} /> Чат
        </Link>
      ) : (
        <Link to="/chat" className="btn btn-sm btn-ghost">
          <MessageSquare size={14} /> Чат
        </Link>
      )}
    </div>
  )
}

export function RentalsPage() {
  const { user } = useAuth()
  const [status, setStatus] = useState<'' | RentalStatus>('')
  const [page, setPage] = useState(1)

  const { data, isPending, isError, error } = useQuery({
    queryKey: ['rentals', { status, page }],
    queryFn: () =>
      rentalApi.list({ status, page, page_size: PAGE_SIZE }).then((r) => r.data),
  })

  const { data: chats } = useQuery({
    queryKey: ['chats'],
    queryFn: () => chatApi.list({ page_size: 100 }).then((r) => r.data),
    staleTime: 60_000,
  })
  const chatByRental = new Map((chats?.results ?? []).map((c) => [c.rental?.id, c.id]).filter(([r]) => r) as [number, number][])

  return (
    <SidebarLayout items={NAV} title="Мои аренды">
      <div className="tabs">
        {STATUS_TABS.map((t) => (
          <button
            key={t.key}
            className={`tab${status === t.key ? ' on' : ''}`}
            onClick={() => { setStatus(t.key); setPage(1) }}
          >
            {t.label}
          </button>
        ))}
      </div>

      {isPending ? (
        <Spinner />
      ) : isError ? (
        <ErrorBox text={error instanceof Error ? error.message : 'Ошибка загрузки'} />
      ) : data && data.results.length === 0 ? (
        <EmptyState text="Здесь появятся ваши аренды. Найдите машину в каталоге и забронируйте её." />
      ) : (
        <div style={{ display: 'grid', gap: 14 }}>
          {data?.results.map((rental) => (
            <div key={rental.id} className="glass glass-card">
              <div className="row row-wrap" style={{ justifyContent: 'space-between', gap: 14 }}>
                <div className="row" style={{ gap: 16, alignItems: 'center' }}>
                  {rental.car.image || rental.car.images[0] ? (
                    <img
                      src={mediaUrl(rental.car.image ?? rental.car.images[0]?.image)}
                      alt=""
                      style={{ width: 74, height: 56, objectFit: 'cover', borderRadius: 10 }}
                    />
                  ) : (
                    <span className="avatar" style={{ width: 74, height: 56, borderRadius: 10 }}>
                      <Car size={24} />
                    </span>
                  )}
                  <div>
                    <Link to={`/car/${rental.car.id}`} style={{ color: 'var(--txt)', fontWeight: 700 }}>
                      {rental.car.brand} {rental.car.model_name}
                    </Link>
                    <div className="muted text-sm mt-8">
                      {rental.start_date} → {rental.end_date} · {rental.total_price} ₽
                    </div>
                    <div className="muted text-sm">
                      {rental.renter.id === user?.id ? 'Вы арендатор' : `Арендатор: ${rental.renter.username}`}
                    </div>
                  </div>
                </div>
                <div className="row" style={{ gap: 12, alignItems: 'center' }}>
                  <RentStatusBadge status={rental.status} />
                </div>
              </div>
              <div className="mt-16" style={{ borderTop: '1px solid rgba(255,255,255,0.06)', paddingTop: 14 }}>
                <RentalActions rental={rental} chatId={chatByRental.get(rental.id)} />
              </div>
            </div>
          ))}
        </div>
      )}
      {data && <Pagination count={data.count} page={page} pageSize={PAGE_SIZE} onPage={setPage} />}
    </SidebarLayout>
  )
}
