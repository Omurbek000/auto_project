import { useState } from 'react'
import { useMutation, useQueryClient } from '@tanstack/react-query'
import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { z } from 'zod'
import { ShieldAlert } from 'lucide-react'
import { complaintApi } from '@/api'
import { apiErrorText } from '@/api/client'
import { useAuth } from '@/features/auth/AuthContext'
import { Modal } from './ui'
import { useToast } from './Toast'
import type { Rental } from '@/types/api'

const schema = z.object({
  reason: z.string().min(1, 'Выберите причину'),
  details: z.string().max(1000).optional(),
})
type Form = z.infer<typeof schema>

const REASONS = [
  'Машина не соответствует описанию',
  'Нечестное поведение при передаче',
  'Проблемы с оплатой',
  'Повреждение имущества',
  'Другое',
]

export function ComplaintModal({ rental }: { rental: Rental }) {
  const toast = useToast()
  const qc = useQueryClient()
  const { user } = useAuth()
  const [open, setOpen] = useState(false)

  const target = user?.id === rental.renter.id ? rental.car.owner : rental.renter

  const { register, handleSubmit, formState: { errors }, reset } = useForm<Form>({
    resolver: zodResolver(schema),
  })

  const mutation = useMutation({
    mutationFn: (data: Form) =>
      complaintApi.create({
        target_user_id: target.id,
        rental: rental.id,
        reason: data.reason,
        details: data.details,
      }),
    onSuccess: () => {
      toast.success('Жалоба отправлена администрации')
      setOpen(false)
      reset()
      void qc.invalidateQueries({ queryKey: ['complaints'] })
    },
    onError: (err) => toast.error(apiErrorText(err)),
  })

  return (
    <>
      <button className="btn btn-sm btn-danger" onClick={() => setOpen(true)}>
        <ShieldAlert size={14} /> Пожаловаться
      </button>
      <Modal open={open} title="Пожаловаться" onClose={() => setOpen(false)}>
        <p className="muted text-sm mb-16">
          На аренду {rental.car.brand} {rental.car.model_name} с участником {target.username}.
          Жалобу рассмотрит администрация.
        </p>
        <form onSubmit={handleSubmit((d) => mutation.mutate(d))} noValidate>
          <div className="field">
            <label htmlFor="comp-reason">Причина</label>
            <select id="comp-reason" className="select" aria-invalid={!!errors.reason} {...register('reason')}>
              <option value="">Выберите причину…</option>
              {REASONS.map((r) => (
                <option key={r} value={r}>{r}</option>
              ))}
            </select>
            {errors.reason && <span className="field-error">{errors.reason.message}</span>}
          </div>
          <div className="field">
            <label htmlFor="comp-details">Подробности</label>
            <textarea id="comp-details" className="input" placeholder="Опишите ситуацию…" {...register('details')} />
          </div>
          <div className="row" style={{ justifyContent: 'flex-end' }}>
            <button type="button" className="btn btn-ghost" onClick={() => setOpen(false)}>Отмена</button>
            <button type="submit" className="btn btn-danger" disabled={mutation.isPending}>
              Отправить жалобу
            </button>
          </div>
        </form>
      </Modal>
    </>
  )
}
