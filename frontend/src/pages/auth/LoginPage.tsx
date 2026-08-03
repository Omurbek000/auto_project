import { useEffect } from 'react'
import { Link, useLocation, useNavigate } from 'react-router-dom'
import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { z } from 'zod'
import { ArrowRight, Lock, User as UserIcon } from 'lucide-react'
import { useAuth } from '@/features/auth/AuthContext'
import { roleHome } from '@/features/auth/RequireAuth'
import { AuthLayout } from '@/layouts/AuthLayout'
import { apiErrorText } from '@/api/client'
import { useToast } from '@/components/Toast'

const schema = z.object({
  username: z.string().min(1, 'Введите логин'),
  password: z.string().min(1, 'Введите пароль'),
})

type FormData = z.infer<typeof schema>

export function LoginPage() {
  const { login, isAuthenticated, user } = useAuth()
  const navigate = useNavigate()
  const location = useLocation()
  const toast = useToast()
  const from = (location.state as { from?: string } | null)?.from

  const {
    register,
    handleSubmit,
    formState: { errors, isSubmitting },
    setError,
  } = useForm<FormData>({ resolver: zodResolver(schema) })

  useEffect(() => {
    if (isAuthenticated) navigate(from && !from.includes('/login') ? from : roleHome(user), { replace: true })
  }, [isAuthenticated, navigate, from, user])

  const onSubmit = async (data: FormData) => {
    try {
      const u = await login(data.username, data.password)
      navigate(from && !from.includes('/login') ? from : roleHome(u), { replace: true })
    } catch (err) {
      const text = apiErrorText(err)
      if (text.includes('username')) setError('username', { message: text })
      else if (text.includes('password')) setError('password', { message: text })
      else toast.error(text)
    }
  }

  return (
    <AuthLayout>
      <div className="glass glass-card" style={{ maxWidth: 420, margin: '0 auto', padding: 32 }}>
        <h2 className="card-title" style={{ fontSize: 24, marginBottom: 4 }}>
          Вход
        </h2>
        <p className="card-desc mb-16" style={{ marginBottom: 24 }}>
          Рады видеть вас снова
        </p>
        <form onSubmit={handleSubmit(onSubmit)} noValidate>
          <div className="field">
            <label htmlFor="username">Логин</label>
            <div className="row" style={{ position: 'relative' }}>
              <UserIcon size={16} style={{ position: 'absolute', left: 12, color: 'var(--txt3)' }} />
              <input
                id="username"
                className="input"
                style={{ paddingLeft: 36 }}
                autoComplete="username"
                aria-invalid={!!errors.username}
                {...register('username')}
              />
            </div>
            {errors.username && <span className="field-error" role="alert">{errors.username.message}</span>}
          </div>
          <div className="field">
            <label htmlFor="password">Пароль</label>
            <div className="row" style={{ position: 'relative' }}>
              <Lock size={16} style={{ position: 'absolute', left: 12, color: 'var(--txt3)' }} />
              <input
                id="password"
                type="password"
                className="input"
                style={{ paddingLeft: 36 }}
                autoComplete="current-password"
                aria-invalid={!!errors.password}
                {...register('password')}
              />
            </div>
            {errors.password && <span className="field-error" role="alert">{errors.password.message}</span>}
          </div>
          <button className="btn btn-primary btn-block btn-lg" disabled={isSubmitting} type="submit">
            {isSubmitting ? 'Входим…' : 'Войти'} <ArrowRight size={17} />
          </button>
        </form>
        <div className="row" style={{ justifyContent: 'center', marginTop: 18, fontSize: 13.5 }}>
          <span className="muted">Нет аккаунта?</span>
          <Link to="/register">Зарегистрироваться</Link>
        </div>
      </div>
    </AuthLayout>
  )
}
