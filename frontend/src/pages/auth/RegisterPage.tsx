import { useEffect } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { z } from 'zod'
import { ArrowRight } from 'lucide-react'
import { useAuth } from '@/features/auth/AuthContext'
import { roleHome } from '@/features/auth/RequireAuth'
import { AuthLayout } from '@/layouts/AuthLayout'
import { apiErrorText } from '@/api/client'
import { useToast } from '@/components/Toast'

const schema = z
  .object({
    username: z.string().min(3, 'Минимум 3 символа').max(30, 'Максимум 30 символов'),
    email: z.string().email('Некорректный email'),
    password: z.string().min(8, 'Минимум 8 символов'),
    confirm: z.string(),
    is_owner: z.boolean().optional(),
  })
  .refine((d) => d.password === d.confirm, {
    message: 'Пароли не совпадают',
    path: ['confirm'],
  })

type FormData = z.infer<typeof schema>

export function RegisterPage() {
  const { register: registerApi, isAuthenticated, user } = useAuth()
  const navigate = useNavigate()
  const toast = useToast()

  const {
    register,
    handleSubmit,
    formState: { errors, isSubmitting },
    setError,
  } = useForm<FormData>({ resolver: zodResolver(schema) })

  useEffect(() => {
    if (isAuthenticated) navigate(roleHome(user), { replace: true })
  }, [isAuthenticated, navigate, user])

  const onSubmit = async (data: FormData) => {
    try {
      const u = await registerApi({
        username: data.username,
        email: data.email,
        password: data.password,
        is_owner: data.is_owner,
      })
      navigate(roleHome(u), { replace: true })
    } catch (err) {
      const text = apiErrorText(err)
      if (text.toLowerCase().includes('username')) setError('username', { message: text })
      else if (text.toLowerCase().includes('email')) setError('email', { message: text })
      else toast.error(text)
    }
  }

  return (
    <AuthLayout>
      <div className="glass glass-card" style={{ maxWidth: 460, margin: '0 auto', padding: 32 }}>
        <h2 className="card-title" style={{ fontSize: 24, marginBottom: 4 }}>
          Регистрация
        </h2>
        <p className="card-desc mb-16" style={{ marginBottom: 24 }}>
          Создайте аккаунт, чтобы арендовать или сдавать машины
        </p>
        <form onSubmit={handleSubmit(onSubmit)} noValidate>
          <div className="field">
            <label htmlFor="reg-username">Логин</label>
            <input
              id="reg-username"
              className="input"
              autoComplete="username"
              aria-invalid={!!errors.username}
              {...register('username')}
            />
            {errors.username && <span className="field-error" role="alert">{errors.username.message}</span>}
          </div>
          <div className="field">
            <label htmlFor="reg-email">Email</label>
            <input
              id="reg-email"
              type="email"
              className="input"
              autoComplete="email"
              aria-invalid={!!errors.email}
              {...register('email')}
            />
            {errors.email && <span className="field-error" role="alert">{errors.email.message}</span>}
          </div>
          <div className="field">
            <label htmlFor="reg-password">Пароль</label>
            <input
              id="reg-password"
              type="password"
              className="input"
              autoComplete="new-password"
              aria-invalid={!!errors.password}
              {...register('password')}
            />
            {errors.password && <span className="field-error" role="alert">{errors.password.message}</span>}
          </div>
          <div className="field">
            <label htmlFor="reg-confirm">Повторите пароль</label>
            <input
              id="reg-confirm"
              type="password"
              className="input"
              autoComplete="new-password"
              aria-invalid={!!errors.confirm}
              {...register('confirm')}
            />
            {errors.confirm && <span className="field-error" role="alert">{errors.confirm.message}</span>}
          </div>
          <label className="row" style={{ gap: 10, cursor: 'pointer', marginBottom: 20, fontSize: 14 }}>
            <input type="checkbox" style={{ width: 17, height: 17, accentColor: 'var(--a2)' }} {...register('is_owner')} />
            <span style={{ color: 'var(--txt2)' }}>Я владелец — хочу сдавать машины</span>
          </label>
          <button className="btn btn-primary btn-block btn-lg" disabled={isSubmitting} type="submit">
            {isSubmitting ? 'Создаём…' : 'Создать аккаунт'} <ArrowRight size={17} />
          </button>
        </form>
        <div className="row" style={{ justifyContent: 'center', marginTop: 18, fontSize: 13.5 }}>
          <span className="muted">Уже есть аккаунт?</span>
          <Link to="/login">Войти</Link>
        </div>
      </div>
    </AuthLayout>
  )
}
