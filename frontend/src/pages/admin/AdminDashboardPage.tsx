import { useQuery } from '@tanstack/react-query'
import { AlertTriangle, Car, Download, Star, UserRound, Zap } from 'lucide-react'
import { adminApi } from '@/api'
import { AdminSidebar } from '@/layouts/Layouts'
import { KpiCard } from '@/components/KpiCard'
import { BrandPie, MonthBarChart, TopBars, type BarPoint, type PiePoint } from '@/components/Charts'
import { ErrorBox, RentStatusBadge, Spinner } from '@/components/ui'
import { exportCsv } from '@/components/exportCsv'
import type { RentalStatus } from '@/types/api'

function monthDelta(points: number[]): number | null {
  if (points.length < 2) return null
  const last = points[points.length - 1]
  const prev = points[points.length - 2]
  if (prev === 0) return last > 0 ? 100 : 0
  return Math.round(((last - prev) / prev) * 100)
}

export function AdminDashboardPage() {
  const { data: analytics, isPending: aPending, isError: aError } = useQuery({
    queryKey: ['admin-analytics'],
    queryFn: () => adminApi.analytics().then((r) => r.data),
  })

  const { data: ops } = useQuery({
    queryKey: ['admin-operations'],
    queryFn: () => adminApi.operations({ page_size: 10 }).then((r) => r.data),
  })

  if (aPending) return <Spinner />
  if (aError || !analytics)
    return <ErrorBox text="Не удалось загрузить аналитику платформы" />

  const rentalPoints = (analytics.rentals_by_month ?? []).map((m) => m.count)
  const rentalBars: BarPoint[] = (analytics.rentals_by_month ?? []).map((m) => ({
    label: m.month,
    value: m.count,
  }))
  const brandPoints: PiePoint[] = (analytics.cars_by_brand ?? []).map((b) => ({ name: b.brand, value: b.count }))
  const topCars: PiePoint[] = (analytics.top_cars_by_days ?? []).map((c) => ({
    name: `${c.brand} ${c.model_name}`,
    value: c.rental_days,
  }))

  const exportOps = () =>
    exportCsv(
      'platform-operations',
      ops?.results.map((o) => ({ date: o.date, user: o.username ?? '', type: o.type, status: o.status ?? '', description: o.description })) ?? [],
    )

  return (
    <AdminSidebar>
      <div className="grid g4" style={{ marginBottom: 24 }}>
        <KpiCard label="Пользователей" value={analytics.total_users} icon={<UserRound size={16} />} />
        <KpiCard label="Машин" value={analytics.total_cars} icon={<Car size={16} />} />
        <KpiCard
          label="Аренд за всё время"
          value={analytics.total_rentals}
          icon={<Zap size={16} />}
          points={rentalPoints}
          delta={monthDelta(rentalPoints)}
          color="#6C63FF"
        />
        <KpiCard
          label="Ожидают жалоб"
          value={analytics.pending_complaints}
          icon={<AlertTriangle size={16} />}
          color="#EF4444"
        />
      </div>

      <div className="grid g3" style={{ marginBottom: 24 }}>
        <div className="glass chart-card">
          <h3>Аренды по месяцам</h3>
          {rentalBars.length ? <MonthBarChart data={rentalBars} /> : <p className="muted text-sm">Данных нет</p>}
        </div>
        <div className="glass chart-card">
          <h3>Машины по брендам</h3>
          {brandPoints.length ? <BrandPie data={brandPoints} /> : <p className="muted text-sm">Данных нет</p>}
        </div>
        <div className="glass chart-card">
          <h3>Топ машин по сдаваемости</h3>
          {topCars.length ? <TopBars data={topCars} /> : <p className="muted text-sm">Данных нет</p>}
        </div>
      </div>

      <div className="glass glass-card">
        <div className="row" style={{ justifyContent: 'space-between', marginBottom: 16 }}>
          <div className="card-title" style={{ margin: 0 }}>Последние операции платформы</div>
          <button className="btn btn-sm" onClick={exportOps}>
            <Download size={15} /> Экспорт CSV
          </button>
        </div>
        {ops && ops.results.length ? (
          <div className="table-wrap">
            <table className="table">
              <thead>
                <tr>
                  <th>Дата</th>
                  <th>Пользователь</th>
                  <th>Тип</th>
                  <th>Статус</th>
                  <th>Описание</th>
                </tr>
              </thead>
              <tbody>
                {ops.results.map((o) => (
                  <tr key={o.id}>
                    <td className="num">{o.date.slice(0, 16).replace('T', ' ')}</td>
                    <td>{o.username ?? '—'}</td>
                    <td>{o.type}</td>
                    <td>
                      {['pending', 'confirmed', 'active', 'completed', 'canceled'].includes(String(o.status)) ? (
                        <RentStatusBadge status={o.status as RentalStatus} />
                      ) : (
                        <span className="badge st-default">{o.status ?? '—'}</span>
                      )}
                    </td>
                    <td>{o.description}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : (
          <p className="muted text-sm" style={{ padding: 20, textAlign: 'center' }}>Операций пока нет</p>
        )}
      </div>

      <p className="muted text-sm mt-16">
        <Star size={13} style={{ verticalAlign: '-2px' }} /> Финансы пользователей анонимны: суммы не показываются админу.
      </p>
    </AdminSidebar>
  )
}
