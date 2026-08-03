import {
  Area,
  AreaChart,
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  Pie,
  PieChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts'

const COLORS = ['#6C63FF', '#4F8CFF', '#10B981', '#F59E0B', '#F87171', '#A855F7', '#22D3EE']

const tooltipStyle = {
  backgroundColor: 'rgba(20,20,44,0.95)',
  border: '1px solid rgba(255,255,255,0.15)',
  borderRadius: '10px',
  fontSize: '12.5px',
  color: '#fff',
  boxShadow: '0 12px 30px rgba(0,0,0,0.5)',
}

const axisStyle = { fill: 'rgba(255,255,255,0.5)', fontSize: 11 }

export interface BarPoint {
  label: string
  value: number
}

/** Гистограмма: доход/аренды по месяцам. */
export function MonthBarChart({ data, color = '#6C63FF' }: { data: BarPoint[]; color?: string }) {
  if (!data.length) return null
  return (
    <ResponsiveContainer width="100%" height={240}>
      <BarChart data={data} margin={{ top: 6, right: 8, left: -12, bottom: 0 }}>
        <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.06)" />
        <XAxis dataKey="label" tick={axisStyle} tickLine={false} axisLine={false} />
        <YAxis tick={axisStyle} tickLine={false} axisLine={false} width={52} />
        <Tooltip cursor={{ fill: 'rgba(255,255,255,0.04)' }} contentStyle={tooltipStyle} />
        <Bar dataKey="value" radius={[6, 6, 0, 0]} fill={color} maxBarSize={34} />
      </BarChart>
    </ResponsiveContainer>
  )
}

/** Спарклайн для KPI-карточек. */
export function Sparkline({ points, color = '#4F8CFF' }: { points: number[]; color?: string }) {
  const data = points.map((v, i) => ({ i, v }))
  if (!data.length) return null
  return (
    <ResponsiveContainer width="100%" height={44}>
      <AreaChart data={data} margin={{ top: 4, right: 0, left: 0, bottom: 0 }}>
        <defs>
          <linearGradient id="sparkFill" x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%" stopColor={color} stopOpacity={0.5} />
            <stop offset="100%" stopColor={color} stopOpacity={0.02} />
          </linearGradient>
        </defs>
        <Area
          type="monotone"
          dataKey="v"
          stroke={color}
          strokeWidth={2}
          fill="url(#sparkFill)"
          isAnimationActive={false}
        />
      </AreaChart>
    </ResponsiveContainer>
  )
}

export interface PiePoint {
  name: string
  value: number
}

/** Круговая диаграмма: машины по брендам и т.п. */
export function BrandPie({ data }: { data: PiePoint[] }) {
  if (!data.length) return null
  return (
    <div>
      <ResponsiveContainer width="100%" height={220}>
        <PieChart>
          <Pie data={data} dataKey="value" nameKey="name" innerRadius={52} outerRadius={84} paddingAngle={3}>
            {data.map((_, i) => (
              <Cell key={i} fill={COLORS[i % COLORS.length]} stroke="transparent" />
            ))}
          </Pie>
          <Tooltip contentStyle={tooltipStyle} />
        </PieChart>
      </ResponsiveContainer>
      <div className="legend">
        {data.map((p, i) => (
          <span key={p.name} className="lg">
            <span className="sw" style={{ background: COLORS[i % COLORS.length] }} />
            {p.name} — {p.value}
          </span>
        ))}
      </div>
    </div>
  )
}

/** Горизонтальные полосы: топ машин по сдаваемости. */
export function TopBars({ data }: { data: PiePoint[] }) {
  if (!data.length) return null
  const max = Math.max(...data.map((d) => d.value), 1)
  return (
    <div style={{ display: 'grid', gap: 10 }}>
      {data.map((d, i) => (
        <div key={d.name}>
          <div className="row" style={{ justifyContent: 'space-between', marginBottom: 4 }}>
            <span className="text-sm" style={{ color: 'var(--txt2)' }}>{d.name}</span>
            <span className="text-sm" style={{ fontWeight: 700 }}>{d.value} дн.</span>
          </div>
          <div
            style={{
              height: 9,
              borderRadius: 99,
              background: 'rgba(255,255,255,0.06)',
              overflow: 'hidden',
            }}
          >
            <div
              style={{
                height: '100%',
                width: `${(d.value / max) * 100}%`,
                borderRadius: 99,
                background: `linear-gradient(90deg, ${COLORS[i % COLORS.length]}, ${COLORS[(i + 1) % COLORS.length]})`,
              }}
            />
          </div>
        </div>
      ))}
    </div>
  )
}

export { COLORS }
