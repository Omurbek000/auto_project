import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { Banknote, CalendarClock, Car, Download, Star } from 'lucide-react'
import { statsApi } from '@/api'
import { KpiCard } from '@/components/KpiCard'
import { BrandPie, MonthBarChart, TopBars, type BarPoint, type PiePoint } from '@/components/Charts'
import { ErrorBox, Pagination, RentStatusBadge, Spinner } from '@/components/ui'
import { exportCsv } from '@/components/exportCsv'
import { SidebarLayout, type SideNavItem } from '@/layouts/Layouts'
import { useAuth } from '@/features/auth/AuthContext'
import type { Operation, RentalStatus } from '@/types/api'

const PAGE_SIZE = 10
const NAV: SideNavItem[] = [
  { to: '/my-cars', label: 'Мои машины', icon: <Car size={17} /> },
  { to: '/owner/stats', label: 'Статистика', icon: <Star size={17} /> },
  { to: '/profile', label: 'Профиль', icon: <Star size={17} /> },
]

function monthDelta(points: number[]): number | null {
  if (points.length < 2) return null
  const last = points[points.length - 1]
  const prev = points[points.length - 2]
  if (prev === 0) return last > 0 ? 100 : 0
  return Math.round(((last - prev) / prev) * 100)
}

export function OwnerStatsPage() {
  const { user } = useAuth()
  const [page, setPage] = useState(1)

  const { data: owner, isPending: oPending, isError: oError } = useQuery({
    queryKey: ['owner-stats'],
    queryFn: () => statsApi.owner().then((r) => r.data),
  })

  const { data: analytics, isPending: aPending } = useQuery({
    queryKey: ['analytics'],
    queryFn: () => statsApi.analytics().then((r) => r.data),
  })

  const { data: ops, isPending: opsPending } = useQuery({
    queryKey: ['operations', page],
    queryFn: () => statsApi.operations({ page, page_size: PAGE_SIZE }).then((r) => r.data),
  })

  if (oPending || aPending) return <Spinner />
  if (oError || !owner)
    return <ErrorBox text="Не удалось загрузить статистику владельца. Нужна роль владельца." />

  const revenuePoints = (analytics?.revenue_by_month ?? []).map((m) => Number(m.revenue))
  const revenueBars: BarPoint[] = (analytics?.revenue_by_month ?? []).map((m) => ({
    label: m.month,
    value: Number(m.revenue),
  }))
  const brandPoints: PiePoint[] = (analytics?.cars_by_brand ?? []).map((b) => ({
    name: b.brand,
    value: b.count,
  }))
  const rentalDays: PiePoint[] = (analytics?.cars_rental_days ?? []).map((c) => ({
    name: `${c.brand} ${c.model_name}`,
    value: c.rental_days,
  }))

  const exportOps = () =>
    exportCsv(
      'operations',
      ops?.results.map((o: Operation) => ({
        date: o.date,
        type: o.type,
        status: o.status ?? '',
        amount: o.amount ?? '',
        description: o.description,
      })) ?? [],
    )

  return (
    <SidebarLayout items={NAV} title={`Статистика — ${user?.username ?? ''}`}>
      <div className="grid g4" style={{ marginBottom: 24 }}>
        <KpiCard
          label="Доход от аренды"
          value={`${Number(owner.total_earnings).toLocaleString('ru-RU')} ₽`}
          icon={<Banknote size={16} />}
          points={revenuePoints}
          delta={monthDelta(revenuePoints)}
          color="#10B981"
        />
        <KpiCard
          label="Доход за месяц"
          value={`${Number(owner.monthly_revenue).toLocaleString('ru-RU')} ₽`}
          icon={<CalendarClock size={16} />}
        />
        <KpiCard label="Всего аренд" value={owner.total_rentals} icon={<Car size={16} />} />
        <KpiCard
          label="Рейтинг владельца"
          value={owner.average_rating ? owner.average_rating.toFixed(1) : '—'}
          icon={<Star size={16} />}
          color="#F59E0B"
        />
      </div>

      <div className="grid g2" style={{ marginBottom: 24 }}>
        <div className="glass chart-card">
          <h3>Доход по месяцам</h3>
          {revenueBars.length ? <MonthBarChart data={revenueBars} color="#10B981" /> : <p className="muted text-sm">Данных пока нет</p>}
        </div>
        <div className="glass chart-card">
          <h3>Машины по брендам</h3>
          {brandPoints.length ? <BrandPie data={brandPoints} /> : <p className="muted text-sm">Данных пока нет</p>}
        </div>
      </div>

      <div className="glass chart-card" style={{ marginBottom: 24 }}>
        <h3>Сдаваемость машин (дни в аренде)</h3>
        {rentalDays.length ? <TopBars data={rentalDays} /> : <p className="muted text-sm">Данных пока нет</p>}
      </div>

      <div className="glass glass-card">
        <div className="row" style={{ justifyContent: 'space-between', marginBottom: 16 }}>
          <div className="card-title" style={{ margin: 0 }}>Журнал операций</div>
          <button className="btn btn-sm" onClick={exportOps}>
            <Download size={15} /> Экспорт CSV
          </button>
        </div>
        {opsPending ? (
          <Spinner />
        ) : ops && ops.results.length === 0 ? (
          <p className="muted text-sm" style={{ padding: 20, textAlign: 'center' }}>Операций пока нет</p>
        ) : (
          <div className="table-wrap">
            <table className="table">
              <thead>
                <tr>
                  <th>Дата</th>
                  <th>Тип</th>
                  <th>Статус</th>
                  <th>Сумма</th>
                  <th>Описание</th>
                </tr>
              </thead>
              <tbody>
                {ops?.results.map((o) => (
                  <tr key={o.id}>
                    <td className="num">{o.date.slice(0, 16).replace('T', ' ')}</td>
                    <td>{o.type}</td>
                    <td>
                      {['pending', 'confirmed', 'active', 'completed', 'canceled'].includes(String(o.status)) ? (
                        <RentStatusBadge status={o.status as RentalStatus} />
                      ) : (
                        <span className="badge st-default">{o.status ?? '—'}</span>
                      )}
                    </td>
                    <td className="num">{o.amount ?? '—'}</td>
                    <td>{o.description}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
        {ops && <Pagination count={ops.count} page={page} pageSize={PAGE_SIZE} onPage={setPage} />}
      </div>
    </SidebarLayout>
  )
}
