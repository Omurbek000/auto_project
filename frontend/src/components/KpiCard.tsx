import type { ReactNode } from 'react'
import { TrendingDown, TrendingUp } from 'lucide-react'
import { Sparkline } from './Charts'

interface KpiCardProps {
  label: string
  value: ReactNode
  icon?: ReactNode
  points?: number[]
  delta?: number | null
  color?: string
}

export function KpiCard({ label, value, icon, points, delta, color = '#4F8CFF' }: KpiCardProps) {
  return (
    <div className="glass glass-card">
      <div className="row" style={{ justifyContent: 'space-between', marginBottom: 10 }}>
        <span className="muted text-sm" style={{ fontWeight: 600 }}>{label}</span>
        {icon && <span className="ic" style={{ width: 34, height: 34, margin: 0, fontSize: 15 }}>{icon}</span>}
      </div>
      <div style={{ fontSize: 26, fontWeight: 800, lineHeight: 1.1 }}>{value}</div>
      {delta !== undefined && delta !== null && (
        <div className={`text-sm mt-8 ${delta >= 0 ? 'text-ok' : 'text-bad'}`} style={{ display: 'flex', alignItems: 'center', gap: 5, fontWeight: 600 }}>
          {delta >= 0 ? <TrendingUp size={15} /> : <TrendingDown size={15} />}
          {delta >= 0 ? '+' : ''}{delta}% за месяц
        </div>
      )}
      {points && points.length > 0 && (
        <div className="mt-12" style={{ opacity: 0.9 }}>
          <Sparkline points={points} color={color} />
        </div>
      )}
    </div>
  )
}
