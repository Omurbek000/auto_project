import { useRef, useState } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { z } from 'zod'
import { Car, ImagePlus, Link2, Plus, Star, Trash2 } from 'lucide-react'
import { carApi } from '@/api'
import { apiErrorText, mediaUrl } from '@/api/client'
import { EmptyState, ErrorBox, Modal, Pagination, Spinner } from '@/components/ui'
import { SidebarLayout, type SideNavItem } from '@/layouts/Layouts'
import { useToast } from '@/components/Toast'
import type { Car as CarType, CarCreate, FuelType, Transmission } from '@/types/api'

const PAGE_SIZE = 9
const NAV: SideNavItem[] = [
  { to: '/my-cars', label: 'Мои машины', icon: <Car size={17} /> },
  { to: '/owner/stats', label: 'Статистика', icon: <Star size={17} /> },
  { to: '/profile', label: 'Профиль', icon: <Star size={17} /> },
]

const carSchema = z.object({
  brand: z.string().min(1, 'Укажите марку'),
  model_name: z.string().min(1, 'Укажите модель'),
  year: z.coerce.number().min(1990, 'Год с 1990').max(2030),
  fuel_type: z.enum(['petrol', 'diesel', 'electric', 'hybrid'] as const),
  transmission: z.enum(['manual', 'auto'] as const),
  mileage: z.coerce.number().min(0, 'Пробег ≥ 0'),
  price_per_day: z.string().min(1, 'Укажите цену'),
  location: z.string().min(1, 'Укажите город'),
  deposit: z.string().optional().default('0.00'),
  description: z.string().optional(),
})
type CarForm = z.infer<typeof carSchema>

function CarFormModal({
  open,
  onClose,
  initial,
}: {
  open: boolean
  onClose: () => void
  initial?: CarType
}) {
  const toast = useToast()
  const qc = useQueryClient()
  const { register, handleSubmit, formState: { errors, isSubmitting } } = useForm<
    z.input<typeof carSchema>,
    unknown,
    z.output<typeof carSchema>
  >({
    resolver: zodResolver(carSchema),
    defaultValues: initial
      ? {
          brand: initial.brand,
          model_name: initial.model_name,
          year: initial.year,
          fuel_type: initial.fuel_type as FuelType,
          transmission: initial.transmission as Transmission,
          mileage: initial.mileage,
          price_per_day: initial.price_per_day,
          location: initial.location,
          deposit: initial.deposit,
          description: initial.description,
        }
      : { fuel_type: 'petrol', transmission: 'auto', deposit: '0.00' },
  })

  const mutation = useMutation({
    mutationFn: (data: CarForm) =>
      initial
        ? carApi.update(initial.id, data).then((r) => r.data)
        : carApi.create(data as CarCreate).then((r) => r.data),
    onSuccess: () => {
      toast.success(initial ? 'Машина обновлена' : 'Машина добавлена')
      onClose()
      void qc.invalidateQueries({ queryKey: ['my-cars'] })
    },
    onError: (err) => toast.error(apiErrorText(err)),
  })

  return (
    <Modal open={open} title={initial ? 'Редактировать машину' : 'Добавить машину'} onClose={onClose}>
      <form onSubmit={handleSubmit((d) => mutation.mutate(d))} noValidate>
        <div className="grid g2" style={{ gap: 12 }}>
          <div className="field">
            <label htmlFor="cbrand">Марка</label>
            <input id="cbrand" className="input" aria-invalid={!!errors.brand} {...register('brand')} />
            {errors.brand && <span className="field-error">{errors.brand.message}</span>}
          </div>
          <div className="field">
            <label htmlFor="cmodel">Модель</label>
            <input id="cmodel" className="input" aria-invalid={!!errors.model_name} {...register('model_name')} />
            {errors.model_name && <span className="field-error">{errors.model_name.message}</span>}
          </div>
        </div>
        <div className="grid g2" style={{ gap: 12 }}>
          <div className="field">
            <label htmlFor="cyear">Год</label>
            <input id="cyear" type="number" className="input" {...register('year')} />
            {errors.year && <span className="field-error">{errors.year.message}</span>}
          </div>
          <div className="field">
            <label htmlFor="cmileage">Пробег, км</label>
            <input id="cmileage" type="number" className="input" {...register('mileage')} />
            {errors.mileage && <span className="field-error">{errors.mileage.message}</span>}
          </div>
        </div>
        <div className="grid g2" style={{ gap: 12 }}>
          <div className="field">
            <label htmlFor="cfuel">Топливо</label>
            <select id="cfuel" className="select" {...register('fuel_type')}>
              <option value="petrol">Бензин</option>
              <option value="diesel">Дизель</option>
              <option value="electric">Электро</option>
              <option value="hybrid">Гибрид</option>
            </select>
          </div>
          <div className="field">
            <label htmlFor="ctrans">Коробка</label>
            <select id="ctrans" className="select" {...register('transmission')}>
              <option value="auto">Автомат</option>
              <option value="manual">Механика</option>
            </select>
          </div>
        </div>
        <div className="grid g2" style={{ gap: 12 }}>
          <div className="field">
            <label htmlFor="cprice">Цена за день, ₽</label>
            <input id="cprice" type="number" step="0.01" className="input" {...register('price_per_day')} />
            {errors.price_per_day && <span className="field-error">{errors.price_per_day.message}</span>}
          </div>
          <div className="field">
            <label htmlFor="cdeposit">Залог, ₽</label>
            <input id="cdeposit" type="number" step="0.01" className="input" {...register('deposit')} />
          </div>
        </div>
        <div className="field">
          <label htmlFor="cloc">Город</label>
          <input id="cloc" className="input" aria-invalid={!!errors.location} {...register('location')} />
          {errors.location && <span className="field-error">{errors.location.message}</span>}
        </div>
        <div className="field">
          <label htmlFor="cdesc">Описание</label>
          <textarea id="cdesc" className="input" {...register('description')} />
        </div>
        <div className="row" style={{ justifyContent: 'flex-end' }}>
          <button type="button" className="btn btn-ghost" onClick={onClose}>Отмена</button>
          <button type="submit" className="btn btn-primary" disabled={isSubmitting || mutation.isPending}>
            {mutation.isPending ? 'Сохраняем…' : 'Сохранить'}
          </button>
        </div>
      </form>
    </Modal>
  )
}

function BlockDatesModal({ car }: { car: CarType }) {
  const toast = useToast()
  const qc = useQueryClient()
  const [open, setOpen] = useState(false)
  const [start, setStart] = useState('')
  const [end, setEnd] = useState('')

  const mutation = useMutation({
    mutationFn: () => carApi.unavailable(car.id, { start_date: start, end_date: end }),
    onSuccess: () => {
      toast.success('Даты заблокированы')
      setOpen(false)
      setStart('')
      setEnd('')
      void qc.invalidateQueries({ queryKey: ['my-cars'] })
      void qc.invalidateQueries({ queryKey: ['car-calendar'] })
    },
    onError: (err) => toast.error(apiErrorText(err)),
  })

  return (
    <>
      <button className="btn btn-sm btn-ghost" onClick={() => setOpen(true)}>
        <Link2 size={14} /> Заблокировать даты
      </button>
      <Modal open={open} title={`Заблокировать даты — ${car.brand} ${car.model_name}`} onClose={() => setOpen(false)}>
        <div className="grid g2" style={{ gap: 12 }}>
          <div className="field">
            <label htmlFor="bd-start">С даты</label>
            <input id="bd-start" type="date" className="input" value={start} onChange={(e) => setStart(e.target.value)} />
          </div>
          <div className="field">
            <label htmlFor="bd-end">По дату</label>
            <input id="bd-end" type="date" className="input" value={end} onChange={(e) => setEnd(e.target.value)} />
          </div>
        </div>
        <div className="row" style={{ justifyContent: 'flex-end' }}>
          <button className="btn btn-ghost" onClick={() => setOpen(false)}>Отмена</button>
          <button className="btn btn-danger" disabled={!start || !end || mutation.isPending} onClick={() => mutation.mutate()}>
            Заблокировать
          </button>
        </div>
      </Modal>
    </>
  )
}

function PhotoManagerModal({ car }: { car: CarType }) {
  const toast = useToast()
  const qc = useQueryClient()
  const fileRef = useRef<HTMLInputElement>(null)
  const [open, setOpen] = useState(false)

  const invalidate = () => {
    void qc.invalidateQueries({ queryKey: ['my-cars'] })
    void qc.invalidateQueries({ queryKey: ['car', car.id] })
  }

  const upload = useMutation({
    mutationFn: (files: File[]) => carApi.bulkUploadImages(car.id, files),
    onSuccess: () => {
      toast.success('Фото добавлены')
      invalidate()
    },
    onError: (err) => toast.error(apiErrorText(err)),
  })

  const setMain = useMutation({
    mutationFn: (imageId: number) => carApi.setMainImage(imageId),
    onSuccess: () => {
      toast.success('Фото установлено основным')
      invalidate()
    },
    onError: (err) => toast.error(apiErrorText(err)),
  })

  const remove = useMutation({
    mutationFn: (imageId: number) => carApi.deleteImage(imageId),
    onSuccess: () => {
      toast.success('Фото удалено')
      invalidate()
    },
    onError: (err) => toast.error(apiErrorText(err)),
  })

  const photos = car.images.map((img) => ({ id: img.id, url: img.image, isMain: img.is_main }))

  return (
    <>
      <button className="btn btn-sm" onClick={() => setOpen(true)}>
        <ImagePlus size={14} /> Фото
      </button>
      <Modal open={open} title={`Фотографии — ${car.brand} ${car.model_name}`} onClose={() => setOpen(false)}>
        <p className="muted text-sm mb-8">Можно выбрать несколько фото сразу. Первое загруженное станет основным, потом его можно поменять.</p>
        <div className="row" style={{ gap: 8, marginBottom: 14, flexWrap: 'wrap' }}>
          <button className="btn btn-primary btn-sm" onClick={() => fileRef.current?.click()} disabled={upload.isPending}>
            <ImagePlus size={14} /> Загрузить фото
          </button>
          <input
            ref={fileRef}
            type="file"
            accept="image/*"
            multiple
            hidden
            onChange={(e) => {
              const files = Array.from(e.target.files ?? [])
              if (files.length) upload.mutate(files)
              e.target.value = ''
            }}
          />
          {upload.isPending && <span className="muted text-sm">Загружаем…</span>}
        </div>

        {photos.length === 0 ? (
          <p className="muted text-sm" style={{ padding: 16, textAlign: 'center' }}>Пока нет фотографий</p>
        ) : (
          <div className="photo-grid">
            {photos.map((p) => (
              <div key={p.id} className={`photo-tile${p.isMain ? ' on' : ''}`}>
                <img src={mediaUrl(p.url)} alt="" />
                {p.isMain && <span className="photo-main-tag">Основное</span>}
                <div className="photo-tile-actions">
                  {!p.isMain && (
                    <button className="btn btn-sm btn-primary" disabled={setMain.isPending} onClick={() => setMain.mutate(p.id)}>
                      Сделать основным
                    </button>
                  )}
                  <button className="btn btn-sm btn-danger" disabled={remove.isPending} onClick={() => remove.mutate(p.id)}>
                    <Trash2 size={13} /> Удалить
                  </button>
                </div>
              </div>
            ))}
          </div>
        )}
      </Modal>
    </>
  )
}

function CarActions({ car }: { car: CarType }) {
  const toast = useToast()
  const qc = useQueryClient()
  const [editOpen, setEditOpen] = useState(false)

  const remove = useMutation({
    mutationFn: () => carApi.remove(car.id),
    onSuccess: () => {
      toast.success('Машина удалена')
      void qc.invalidateQueries({ queryKey: ['my-cars'] })
    },
    onError: (err) => toast.error(apiErrorText(err)),
  })

  return (
    <>
      <div className="row" style={{ gap: 8, flexWrap: 'wrap' }}>
        <button className="btn btn-sm" onClick={() => setEditOpen(true)}>Изменить</button>
        <PhotoManagerModal car={car} />
        <BlockDatesModal car={car} />
        <button
          className="btn btn-sm btn-danger"
          onClick={() => {
            if (confirm(`Удалить ${car.brand} ${car.model_name}?`)) remove.mutate()
          }}
        >
          <Trash2 size={14} />
        </button>
      </div>
      {editOpen && <CarFormModal open={editOpen} onClose={() => setEditOpen(false)} initial={car} />}
    </>
  )
}

export function MyCarsPage() {
  const [page, setPage] = useState(1)
  const [createOpen, setCreateOpen] = useState(false)

  const { data, isPending, isError, error } = useQuery({
    queryKey: ['my-cars', page],
    queryFn: () => carApi.my({ page, page_size: PAGE_SIZE }).then((r) => r.data),
  })

  return (
    <SidebarLayout items={NAV} title="Мои машины">
      <div className="row" style={{ justifyContent: 'space-between', marginBottom: 18 }}>
        <p className="page-sub" style={{ margin: 0 }}>
          Ваши автомобили на площадке. Добавьте машину, чтобы сдавать её в аренду.
        </p>
        <button className="btn btn-primary" onClick={() => setCreateOpen(true)}>
          <Plus size={17} /> Добавить машину
        </button>
      </div>

      {isPending ? (
        <Spinner />
      ) : isError ? (
        <ErrorBox text={error instanceof Error ? error.message : 'Ошибка загрузки'} />
      ) : data && data.results.length === 0 ? (
        <EmptyState text="У вас пока нет машин. Добавьте первую — это займёт пару минут." />
      ) : (
        <>
          <div className="grid g3">
            {data?.results.map((car) => (
              <div key={car.id}>
                <div
                  className="glass"
                  style={{ overflow: 'hidden', marginBottom: 12 }}
                >
                  {car.image || car.images[0] ? (
                    <img
                      src={mediaUrl(car.image ?? car.images[0]?.image)}
                      alt=""
                      style={{ width: '100%', height: 130, objectFit: 'cover' }}
                    />
                  ) : (
                    <div style={{ height: 130, display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                      <Car size={34} className="muted" />
                    </div>
                  )}
                </div>
                <div style={{ marginBottom: 10 }}>
                  <div style={{ fontWeight: 700 }}>
                    {car.brand} {car.model_name}
                  </div>
                  <div className="muted text-sm">
                    {car.price_per_day} ₽/день · {car.year} · {car.location}
                  </div>
                  <span className={`badge ${car.is_available ? 'st-active' : 'st-canceled'} mt-8`}>
                    {car.is_available ? 'доступна' : 'недоступна'}
                  </span>
                </div>
                <CarActions car={car} />
              </div>
            ))}
          </div>
          {data && <Pagination count={data.count} page={page} pageSize={PAGE_SIZE} onPage={setPage} />}
        </>
      )}

      {createOpen && <CarFormModal open={createOpen} onClose={() => setCreateOpen(false)} />}
    </SidebarLayout>
  )
}
