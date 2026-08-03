import type { ReactNode } from 'react'
import { Link } from 'react-router-dom'
import { Car, ShieldCheck, Star } from 'lucide-react'

export function AuthLayout({ children }: { children: ReactNode }) {
  return (
    <div className="page" style={{ display: 'flex', alignItems: 'center', paddingTop: 40 }}>
      <div className="container">
        <div className="grid g2 auth-layout-grid" style={{ alignItems: 'center', maxWidth: 1000, margin: '0 auto' }}>
          <div style={{ padding: '0 24px' }}>
            <Link to="/" className="logo" style={{ fontSize: 40 }}>
              AVTO<span>.</span>
            </Link>
            <h1 className="page-title mt-16" style={{ fontSize: 30 }}>
              Платформа аренды <span className="grad-text">автомобилей</span>
            </h1>
            <p className="page-sub">
              Сдавайте машины в аренду или берите их у владельцев. Бронирование, отзывы, чат и
              аналитика — всё в одном месте.
            </p>
            <div style={{ display: 'grid', gap: 14, marginTop: 20 }}>
              <div className="glass glass-card" style={{ display: 'flex', gap: 14, alignItems: 'center' }}>
                <div className="ic" style={{ background: 'rgba(108,99,255,0.2)' }}>
                  <Car size={20} />
                </div>
                <div>
                  <div className="card-title">Быстрый поиск</div>
                  <div className="card-desc">Фильтры по цене, марке и типу топлива</div>
                </div>
              </div>
              <div className="glass glass-card" style={{ display: 'flex', gap: 14, alignItems: 'center' }}>
                <div className="ic" style={{ background: 'rgba(79,140,255,0.2)' }}>
                  <ShieldCheck size={20} />
                </div>
                <div>
                  <div className="card-title">Безопасная сделка</div>
                  <div className="card-desc">Проверка дат и защита от двойного бронирования</div>
                </div>
              </div>
              <div className="glass glass-card" style={{ display: 'flex', gap: 14, alignItems: 'center' }}>
                <div className="ic" style={{ background: 'rgba(16,185,129,0.2)' }}>
                  <Star size={20} />
                </div>
                <div>
                  <div className="card-title">Отзывы и рейтинги</div>
                  <div className="card-desc">Только реальные участники аренды</div>
                </div>
              </div>
            </div>
          </div>
          <div>{children}</div>
        </div>
      </div>
    </div>
  )
}
