import { useRef, useState } from 'react'
import { useMutation, useQueryClient } from '@tanstack/react-query'
import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { z } from 'zod'
import { BadgeCheck, Camera, Car, KeyRound, ShieldCheck, Star } from 'lucide-react'
import { authApi } from '@/api'
import { apiErrorText, mediaUrl } from '@/api/client'
import { useAuth } from '@/features/auth/AuthContext'
import { Modal, Spinner, Stars } from '@/components/ui'
import { SidebarLayout, type SideNavItem } from '@/layouts/Layouts'
import { useToast } from '@/components/Toast'

const NAV: SideNavItem[] = [
  { to: '/rentals', label: 'Мои аренды', icon: <Car size={17} /> },
  { to: '/favorites', label: 'Избранное', icon: <Star size={17} /> },
  { to: '/profile', label: 'Профиль', icon: <BadgeCheck size={17} /> },
]

const profileSchema = z.object({
  first_name: z.string().max(50).optional(),
  last_name: z.string().max(50).optional(),
  phone_number: z.string().max(20).optional(),
  bio: z.string().max(500).optional(),
  languages: z.string().max(100).optional(),
  date_of_birth: z.string().optional(),
})
type ProfileForm = z.infer<typeof profileSchema>

const passwordSchema = z
  .object({
    old_password: z.string().min(1, 'Введите текущий пароль'),
    new_password: z.string().min(8, 'Минимум 8 символов'),
    confirm: z.string(),
  })
  .refine((d) => d.new_password === d.confirm, { message: 'Пароли не совпадают', path: ['confirm'] })
type PasswordForm = z.infer<typeof passwordSchema>

function VerificationCard() {
  const { user, refreshUser } = useAuth()
  const toast = useToast()
  const [type, setType] = useState<'email' | 'phone'>('email')
  const [open, setOpen] = useState(false)
  const [code, setCode] = useState('')

  const send = useMutation({
    mutationFn: (t: 'email' | 'phone') => authApi.sendVerification(t),
    onSuccess: (_data, t) => {
      toast.toast('Код отправлен. Проверьте почту (в dev-режиме код в консоли бэкенда).')
      setType(t)
      setOpen(true)
    },
    onError: (err) => toast.error(apiErrorText(err)),
  })

  const confirm = useMutation({
    mutationFn: () => authApi.confirmVerification({ verification_type: type, code }),
    onSuccess: () => {
      toast.success('Подтверждено!')
      setOpen(false)
      setCode('')
      void refreshUser()
    },
    onError: (err) => toast.error(apiErrorText(err)),
  })

  return (
    <div className="glass glass-card">
      <div className="card-title mb-16">Верификация</div>
      <div style={{ display: 'grid', gap: 10 }}>
        <div className="row" style={{ justifyContent: 'space-between' }}>
          <span>Email — {user?.email}</span>
          <span className={`badge ${user?.email_verified ? 'st-active' : 'st-default'}`}>
            {user?.email_verified ? 'подтверждён' : 'не подтверждён'}
          </span>
          {!user?.email_verified && (
            <button className="btn btn-sm" onClick={() => send.mutate('email')}>Отправить код</button>
          )}
        </div>
        <div className="row" style={{ justifyContent: 'space-between' }}>
          <span>Телефон — {user?.phone_number || 'не указан'}</span>
          <span className={`badge ${user?.phone_verified ? 'st-active' : 'st-default'}`}>
            {user?.phone_verified ? 'подтверждён' : 'не подтверждён'}
          </span>
          {!user?.phone_verified && (
            <button className="btn btn-sm" onClick={() => send.mutate('phone')}>Отправить код</button>
          )}
        </div>
      </div>
      <Modal open={open} title="Введите код подтверждения" onClose={() => setOpen(false)}>
        <input
          className="input"
          value={code}
          onChange={(e) => setCode(e.target.value)}
          placeholder="6-значный код"
          aria-label="Код подтверждения"
        />
        <div className="row" style={{ justifyContent: 'flex-end', marginTop: 16 }}>
          <button className="btn btn-ghost" onClick={() => setOpen(false)}>Отмена</button>
          <button className="btn btn-primary" disabled={code.length < 6 || confirm.isPending} onClick={() => confirm.mutate()}>
            Подтвердить
          </button>
        </div>
      </Modal>
    </div>
  )
}

export function ProfilePage() {
  const { user, setUser } = useAuth()
  const toast = useToast()
  const qc = useQueryClient()
  const avatarRef = useRef<HTMLInputElement>(null)

  const { register, handleSubmit, formState: { errors, isSubmitting } } = useForm<ProfileForm>({
    resolver: zodResolver(profileSchema),
    defaultValues: {
      first_name: user?.first_name ?? '',
      last_name: user?.last_name ?? '',
      phone_number: user?.phone_number ?? '',
      bio: user?.bio ?? '',
      languages: user?.languages ?? '',
      date_of_birth: user?.date_of_birth ?? '',
    },
  })

  const saveProfile = useMutation({
    mutationFn: (data: ProfileForm) => authApi.updateProfile(user!.id, data),
    onSuccess: (res) => {
      setUser(res.data)
      toast.success('Профиль сохранён')
      void qc.invalidateQueries({ queryKey: ['me'] })
    },
    onError: (err) => toast.error(apiErrorText(err)),
  })

  const avatarMutation = useMutation({
    mutationFn: (file: File) => authApi.uploadAvatar(user!.id, file),
    onSuccess: (res) => {
      setUser(res.data)
      toast.success('Аватар обновлён')
    },
    onError: (err) => toast.error(apiErrorText(err)),
  })

  const toggleOwner = useMutation({
    mutationFn: () => authApi.updateProfile(user!.id, { is_owner: !user!.is_owner }),
    onSuccess: (res) => {
      setUser(res.data)
      toast.success(res.data.is_owner ? 'Вы теперь владелец — можно добавлять машины' : 'Режим владельца выключен')
    },
    onError: (err) => toast.error(apiErrorText(err)),
  })

  const changePassword = useMutation({
    mutationFn: (data: PasswordForm) => authApi.passwordChange({ old_password: data.old_password, new_password: data.new_password }),
    onSuccess: () => toast.success('Пароль изменён'),
    onError: (err) => toast.error(apiErrorText(err)),
  })

  const passwordForm = useForm<PasswordForm>({
    resolver: zodResolver(passwordSchema),
  })

  if (!user) return <Spinner />

  return (
    <SidebarLayout items={NAV} title="Профиль">
      <div className="grid g2" style={{ gap: 20 }}>
        <div>
          <div className="glass glass-card mb-16" style={{ textAlign: 'center', padding: 28 }}>
            {user.avatar ? (
              <img src={mediaUrl(user.avatar)} alt="Аватар" style={{ width: 96, height: 96, borderRadius: '50%', objectFit: 'cover', margin: '0 auto 12px' }} />
            ) : (
              <span className="avatar" style={{ width: 96, height: 96, fontSize: 36, margin: '0 auto 12px' }}>
                {user.username.slice(0, 1).toUpperCase()}
              </span>
            )}
            <div style={{ fontWeight: 800, fontSize: 20 }}>{user.username}</div>
            <div className="muted text-sm mb-16">{user.email}</div>
            <button className="btn btn-sm" onClick={() => avatarRef.current?.click()}>
              <Camera size={15} /> Сменить аватар
            </button>
            <input
              ref={avatarRef}
              type="file"
              accept="image/*"
              hidden
              onChange={(e) => {
                const f = e.target.files?.[0]
                if (f) avatarMutation.mutate(f)
                e.target.value = ''
              }}
            />
            <div className="row" style={{ justifyContent: 'center', gap: 20, marginTop: 18 }}>
              <div style={{ textAlign: 'center' }}>
                <div className="muted text-sm">Как арендатор</div>
                <Stars rating={user.renter_rating} />
              </div>
              <div style={{ textAlign: 'center' }}>
                <div className="muted text-sm">Как владелец</div>
                <Stars rating={user.owner_rating} />
              </div>
            </div>
          </div>

          <VerificationCard />
        </div>

        <div style={{ display: 'grid', gap: 20, alignContent: 'start' }}>
          <div className="glass glass-card">
            <div className="card-title mb-16">Личные данные</div>
            <form onSubmit={handleSubmit((d) => saveProfile.mutate(d))} noValidate>
              <div className="grid g2" style={{ gap: 12 }}>
                <div className="field">
                  <label htmlFor="pf-first">Имя</label>
                  <input id="pf-first" className="input" {...register('first_name')} />
                </div>
                <div className="field">
                  <label htmlFor="pf-last">Фамилия</label>
                  <input id="pf-last" className="input" {...register('last_name')} />
                </div>
              </div>
              <div className="grid g2" style={{ gap: 12 }}>
                <div className="field">
                  <label htmlFor="pf-phone">Телефон</label>
                  <input id="pf-phone" className="input" {...register('phone_number')} />
                </div>
                <div className="field">
                  <label htmlFor="pf-birth">Дата рождения</label>
                  <input id="pf-birth" type="date" className="input" {...register('date_of_birth')} />
                </div>
              </div>
              <div className="field">
                <label htmlFor="pf-lang">Языки</label>
                <input id="pf-lang" className="input" placeholder="Русский, English…" {...register('languages')} />
              </div>
              <div className="field">
                <label htmlFor="pf-bio">О себе</label>
                <textarea id="pf-bio" className="input" {...register('bio')} />
                {errors.bio && <span className="field-error">{errors.bio.message}</span>}
              </div>
              <button className="btn btn-primary" type="submit" disabled={isSubmitting || saveProfile.isPending}>
                Сохранить
              </button>
            </form>
          </div>

          <div className="glass glass-card">
            <div className="card-title mb-16" style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
              <ShieldCheck size={17} /> Роль
            </div>
            <div className="row" style={{ justifyContent: 'space-between' }}>
              <div>
                <div style={{ fontWeight: 600 }}>{user.is_owner ? 'Вы владелец' : 'Вы арендатор'}</div>
                <div className="muted text-sm">
                  {user.is_owner
                    ? 'Вы можете добавлять машины и подтверждать аренду'
                    : 'Включите режим владельца, чтобы сдавать машины'}
                </div>
              </div>
              <button className={`btn btn-sm ${user.is_owner ? 'btn-ghost' : 'btn-primary'}`} onClick={() => toggleOwner.mutate()}>
                {user.is_owner ? 'Выключить' : 'Стать владельцем'}
              </button>
            </div>
          </div>

          <div className="glass glass-card">
            <div className="card-title mb-16" style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
              <KeyRound size={17} /> Смена пароля
            </div>
            <form
              onSubmit={passwordForm.handleSubmit((d) => changePassword.mutate(d))}
              noValidate
            >
              <div className="field">
                <label htmlFor="pw-old">Текущий пароль</label>
                <input id="pw-old" type="password" className="input" {...passwordForm.register('old_password')} />
                {passwordForm.formState.errors.old_password && (
                  <span className="field-error">{passwordForm.formState.errors.old_password.message}</span>
                )}
              </div>
              <div className="grid g2" style={{ gap: 12 }}>
                <div className="field">
                  <label htmlFor="pw-new">Новый пароль</label>
                  <input id="pw-new" type="password" className="input" {...passwordForm.register('new_password')} />
                  {passwordForm.formState.errors.new_password && (
                    <span className="field-error">{passwordForm.formState.errors.new_password.message}</span>
                  )}
                </div>
                <div className="field">
                  <label htmlFor="pw-confirm">Повторите</label>
                  <input id="pw-confirm" type="password" className="input" {...passwordForm.register('confirm')} />
                </div>
              </div>
              {passwordForm.formState.errors.confirm && (
                <span className="field-error">{passwordForm.formState.errors.confirm.message}</span>
              )}
              <button className="btn btn-primary" type="submit" disabled={changePassword.isPending}>
                Сменить пароль
              </button>
            </form>
          </div>
        </div>
      </div>
    </SidebarLayout>
  )
}
