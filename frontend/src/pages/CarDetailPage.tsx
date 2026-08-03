import { useEffect, useMemo, useState } from 'react'
import { Link, useNavigate, useParams } from 'react-router-dom'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import dayjs from 'dayjs'
import {
  Car as CarIcon,
  CalendarDays,
  ChevronLeft,
  ChevronRight,
  Fuel,
  Gauge,
  Heart,
  MapPin,
  Settings,
  ShieldCheck,
  User as UserIcon,
  X,
} from 'lucide-react'
import { carApi, favoriteApi, rentalApi } from '@/api'
import { apiErrorText, mediaUrl } from '@/api/client'
import { useAuth } from '@/features/auth/AuthContext'
import { AvailabilityCalendar } from '@/components/AvailabilityCalendar'
import { ErrorBox, Spinner, Stars } from '@/components/ui'
import { useToast } from '@/components/Toast'

const FUEL: Record<string, string> = {
  petrol: 'Бензин',
  diesel: 'Дизель',
  electric: 'Электро',
  hybrid: 'Гибрид',
}
const TRANS: Record<string, string> = { manual: 'Механика', auto: 'Автомат' }

export function CarDetailPage() {
  const { id } = useParams()
  const carId = Number(id)
  const { isAuthenticated } = useAuth()
  const toast = useToast()
  const navigate = useNavigate()
  const qc = useQueryClient()

  const [month, setMonth] = useState(dayjs())
  const [pick, setPick] = useState<{ start: string | null; end: string | null }>({ start: null, end: null })
  const [lightbox, setLightbox] = useState<number | null>(null)

  const { data: car, isPending, isError, error } = useQuery({
    queryKey: ['car', carId],
    queryFn: () => carApi.detail(carId).then((r) => r.data),
    enabled: Number.isFinite(carId),
  })

  const photos = useMemo(
    () => [...new Set([car?.image, ...(car?.images ?? []).map((i) => i.image)].filter(Boolean))] as string[],
    [car],
  )

  const closeLightbox = () => setLightbox(null)
  const stepLightbox = (dir: 1 | -1) =>
    setLightbox((i) => (i === null || photos.length === 0 ? i : (i + dir + photos.length) % photos.length))

  useEffect(() => {
    if (lightbox === null) return
    const onKey = (e: KeyboardEvent) => {
      if (e.key === 'Escape') closeLightbox()
      if (e.key === 'ArrowRight') stepLightbox(1)
      if (e.key === 'ArrowLeft') stepLightbox(-1)
    }
    window.addEventListener('keydown', onKey)
    return () => window.removeEventListener('keydown', onKey)
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [lightbox])

  const { data: calendar } = useQuery({
    queryKey: ['car-calendar', carId, month.year(), month.month() + 1],
    queryFn: () => carApi.calendar(carId, month.year(), month.month() + 1).then((r) => r.data),
    enabled: Number.isFinite(carId),
  })

  const { data: favorites } = useQuery({
    queryKey: ['favorites'],
    queryFn: () => favoriteApi.list({ page_size: 100 }).then((r) => r.data),
    enabled: isAuthenticated,
  })
  const favId = favorites?.results.find((f) => f.car.id === carId)?.id

  const selectedDates = useMemo(
    () => (pick.start && pick.end ? [pick.start, pick.end] : pick.start ? [pick.start] : []),
    [pick],
  )

  const days = useMemo(() => {
    if (!pick.start || !pick.end) return 0
    return dayjs(pick.end).diff(dayjs(pick.start), 'day')
  }, [pick])

  const total = useMemo(() => {
    if (!car || !days) return null
    return (parseFloat(car.price_per_day) * days).toFixed(2)
  }, [car, days])

  const bookMutation = useMutation({
    mutationFn: () =>
      rentalApi.create({
        car_id: carId,
        start_date: pick.start!,
        end_date: pick.end!,
      }),
    onSuccess: (res) => {
      toast.success(`Заявка №${res.data.id} создана. Ждём подтверждения владельца.`)
      setPick({ start: null, end: null })
      void qc.invalidateQueries({ queryKey: ['car-calendar'] })
      void qc.invalidateQueries({ queryKey: ['rentals'] })
      navigate('/rentals')
    },
    onError: (err) => toast.error(apiErrorText(err)),
  })

  const favMutation = useMutation({
    mutationFn: () => (favId ? favoriteApi.remove(favId) : favoriteApi.add(carId)),
    onSuccess: () => {
      toast.success(favId ? 'Убрано из избранного' : 'Добавлено в избранное')
      void qc.invalidateQueries({ queryKey: ['favorites'] })
    },
    onError: (err) => toast.error(apiErrorText(err)),
  })

  if (isPending) return <Spinner label="Загружаем машину…" />
  if (isError || !car)
    return (
      <div className="container page">
        <ErrorBox text={error instanceof Error ? error.message : 'Машина не найдена'} />
      </div>
    )


  return (
    <div className="container page">
      <Link to="/" className="btn btn-ghost btn-sm mb-16" style={{ paddingLeft: 0 }}>
        <ChevronLeft size={16} /> Назад к каталогу
      </Link>

      <div className="grid g2 car-detail-grid" style={{ alignItems: 'start', gap: 28 }}>
        {/* Левая колонка: галерея + описание */}
        <div>
          <div
            className="glass car-detail-photo"
            style={{ overflow: 'hidden', background: 'linear-gradient(135deg, rgba(108,99,255,0.25), rgba(79,140,255,0.2))', cursor: 'zoom-in' }}
            onClick={() => photos[0] && setLightbox(0)}
          >
            {photos[0] ? (
              <img src={mediaUrl(photos[0])} alt={`${car.brand} ${car.model_name}`} style={{ width: '100%', height: '100%', objectFit: 'cover' }} />
            ) : (
              <div className="empty" style={{ height: '100%', display: 'flex', flexDirection: 'column', gap: 10 }}>
                <CarIcon size={52} /> Фото пока нет
              </div>
            )}
          </div>
          {photos.length > 1 && (
            <div className="row car-detail-photos-row" style={{ gap: 10, marginTop: 12, overflowX: 'auto', paddingBottom: 4 }}>
              {photos.slice(1).map((p, idx) => (
                <img
                  key={p}
                  src={mediaUrl(p)}
                  alt=""
                  onClick={() => setLightbox(idx + 1)}
                  style={{ width: 96, height: 70, objectFit: 'cover', borderRadius: 12, border: '1px solid var(--edge)', cursor: 'zoom-in' }}
                />
              ))}
            </div>
          )}

          <div className="glass glass-card mt-16">
            <div className="card-title mb-8">Описание</div>
            <p className="card-desc" style={{ lineHeight: 1.65 }}>
              {car.description || 'Описание пока не добавлено владельцем.'}
            </p>
            <div className="grid g2" style={{ gap: 12, marginTop: 18 }}>
              {[
                { label: 'Топливо', value: FUEL[car.fuel_type] ?? car.fuel_type, icon: <Fuel size={16} /> },
                { label: 'Коробка', value: TRANS[car.transmission] ?? car.transmission, icon: <Settings size={16} /> },
                { label: 'Пробег', value: `${car.mileage.toLocaleString('ru-RU')} км`, icon: <Gauge size={16} /> },
                { label: 'Год', value: String(car.year), icon: <CalendarDays size={16} /> },
                { label: 'Залог', value: `${car.deposit} ₽`, icon: <ShieldCheck size={16} /> },
                { label: 'Локация', value: car.location, icon: <MapPin size={16} /> },
              ].map((s) => (
                <div key={s.label} className="row" style={{ gap: 12 }}>
                  <span className="ic" style={{ width: 38, height: 38, margin: 0 }}>{s.icon}</span>
                  <div>
                    <div className="muted text-sm">{s.label}</div>
                    <div style={{ fontWeight: 600 }}>{s.value}</div>
                  </div>
                </div>
              ))}
            </div>
          </div>

          <div className="glass glass-card mt-16">
            <div className="card-title mb-8">Владелец</div>
            <div className="row" style={{ gap: 14 }}>
              {car.owner.avatar ? (
                <span className="avatar" style={{ width: 48, height: 48 }}>
                  <img src={mediaUrl(car.owner.avatar)} alt="" />
                </span>
              ) : (
                <span className="avatar" style={{ width: 48, height: 48 }}>
                  <UserIcon size={22} />
                </span>
              )}
              <div>
                <div style={{ fontWeight: 700 }}>{car.owner.username}</div>
                <div className="row" style={{ gap: 10, marginTop: 4 }}>
                  <span className="text-sm muted">
                    {car.owner.owner_rating ? `рейтинг ${car.owner.owner_rating.toFixed(1)}` : 'новый владелец'}
                  </span>
                  {car.owner.is_verified && (
                    <span className="chip text-sm" style={{ color: '#34d399' }}>
                      <ShieldCheck size={13} /> проверен
                    </span>
                  )}
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* Правая колонка: цена + бронирование + календарь */}
        <div className="car-detail-sticky" style={{ position: 'sticky', top: 84 }}>
          <div className="glass glass-card">
            <div className="row" style={{ justifyContent: 'space-between', marginBottom: 10 }}>
              <h1 className="page-title" style={{ fontSize: 26, margin: 0 }}>
                {car.brand} {car.model_name}
              </h1>
              {isAuthenticated && (
                <button
                  className={`btn ${favId ? 'btn-danger' : 'btn-ghost'} btn-sm`}
                  onClick={() => favMutation.mutate()}
                  aria-label={favId ? 'Убрать из избранного' : 'В избранное'}
                >
                  <Heart size={17} fill={favId ? 'currentColor' : 'none'} />
                </button>
              )}
            </div>
            <div className="row" style={{ gap: 12, marginBottom: 16 }}>
              <Stars rating={car.average_rating} />
              <span className="muted text-sm">({car.feedbacks_count} отзывов)</span>
              <span className={`badge ${car.is_available ? 'st-active' : 'st-canceled'}`}>
                {car.is_available ? 'доступна' : 'недоступна'}
              </span>
            </div>
            <div className="row" style={{ justifyContent: 'space-between', alignItems: 'flex-end', marginBottom: 18 }}>
              <span className="price" style={{ fontSize: 26 }}>
                {car.price_per_day} <small>₽/день</small>
              </span>
            </div>

            <div className="card-title mb-8" style={{ fontSize: 14 }}>
              Календарь доступности — {month.format('MMMM YYYY')}
            </div>
            <div className="row" style={{ justifyContent: 'space-between', marginBottom: 12 }}>
              <button
                className="btn btn-ghost btn-sm"
                onClick={() => setMonth(month.subtract(1, 'month'))}
                aria-label="Предыдущий месяц"
              >
                <ChevronLeft size={16} />
              </button>
              <button
                className="btn btn-ghost btn-sm"
                onClick={() => setMonth(month.add(1, 'month'))}
                aria-label="Следующий месяц"
              >
                <ChevronRight size={16} />
              </button>
            </div>
            {calendar ? (
              <AvailabilityCalendar
                data={calendar}
                selected={selectedDates}
                onPick={(date) => {
                  if (!pick.start || (pick.start && pick.end)) {
                    setPick({ start: date, end: null })
                  } else if (dayjs(date).isBefore(dayjs(pick.start), 'day')) {
                    setPick({ start: date, end: null })
                  } else {
                    setPick({ start: pick.start, end: date })
                  }
                }}
              />
            ) : (
              <Spinner />
            )}

            {pick.start && pick.end && (
              <div className="glass" style={{ padding: 14, marginTop: 16, borderColor: 'rgba(16,185,129,0.4)' }}>
                <div className="row" style={{ justifyContent: 'space-between' }}>
                  <div>
                    <div className="muted text-sm">Период</div>
                    <div style={{ fontWeight: 700 }}>
                      {pick.start} — {pick.end}
                    </div>
                  </div>
                  <div style={{ textAlign: 'right' }}>
                    <div className="muted text-sm">Стоимость</div>
                    <div style={{ fontWeight: 800, fontSize: 18 }}>{total} ₽</div>
                    <div className="muted text-sm">({days} дн. × {car.price_per_day} ₽)</div>
                  </div>
                </div>
              </div>
            )}

            <div className="mt-16">
              {!isAuthenticated ? (
                <Link to="/login" state={{ from: `/car/${car.id}` }} className="btn btn-primary btn-block btn-lg">
                  Войдите, чтобы забронировать
                </Link>
              ) : (
                <button
                  className="btn btn-primary btn-block btn-lg"
                  disabled={!pick.start || !pick.end || bookMutation.isPending}
                  onClick={() => bookMutation.mutate()}
                >
                  {bookMutation.isPending
                    ? 'Бронируем…'
                    : pick.start && pick.end
                      ? `Забронировать за ${total} ₽`
                      : 'Выберите даты на календаре'}
                </button>
              )}
            </div>
            <p className="muted text-sm mt-12" style={{ fontSize: 12 }}>
              После брони владелец подтвердит заявку, затем вы сможете начать аренду.
            </p>
          </div>
        </div>
      </div>

      {lightbox !== null && photos[lightbox] && (
        <div className="lightbox" onClick={closeLightbox}>
          <button className="lightbox-close" aria-label="Закрыть" onClick={closeLightbox}>
            <X size={22} />
          </button>
          {photos.length > 1 && (
            <>
              <button
                className="lightbox-nav lightbox-prev"
                aria-label="Предыдущее фото"
                onClick={(e) => {
                  e.stopPropagation()
                  stepLightbox(-1)
                }}
              >
                <ChevronLeft size={28} />
              </button>
              <button
                className="lightbox-nav lightbox-next"
                aria-label="Следующее фото"
                onClick={(e) => {
                  e.stopPropagation()
                  stepLightbox(1)
                }}
              >
                <ChevronRight size={28} />
              </button>
            </>
          )}
          <img
            src={mediaUrl(photos[lightbox])}
            alt={`${car.brand} ${car.model_name} — фото ${lightbox + 1}`}
            className="lightbox-img"
            onClick={(e) => e.stopPropagation()}
          />
          <div className="lightbox-count">
            {lightbox + 1} / {photos.length}
          </div>
        </div>
      )}
    </div>
  )
}
