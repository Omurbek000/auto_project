import { useMemo } from 'react'
import dayjs from 'dayjs'
import type { CarCalendar } from '@/types/api'

interface CalendarProps {
  data: CarCalendar
  selected?: string[]
  onPick?: (date: string) => void
}

const DAYS = ['Пн', 'Вт', 'Ср', 'Чт', 'Пт', 'Сб', 'Вс']

/** Календарь доступности машины. status: free | booked | blocked | past */
export function AvailabilityCalendar({ data, selected = [], onPick }: CalendarProps) {
  const firstDay = useMemo(() => dayjs(`${data.year}-${data.month}-01`), [data.year, data.month])
  const offset = (firstDay.day() + 6) % 7 // понедельник = 0
  const cells: (string | null)[] = [
    ...Array.from({ length: offset }).map(() => null),
    ...data.days.map((d) => d.date),
  ]

  const byDate = useMemo(() => {
    const m = new Map<string, string>()
    data.days.forEach((d) => m.set(d.date, d.status))
    return m
  }, [data.days])

  return (
    <div>
      <div className="cal-grid">
        {DAYS.map((d) => (
          <div key={d} className="cal-dow">
            {d}
          </div>
        ))}
        {cells.map((date, i) => {
          if (!date) return <div key={`e${i}`} />
          const status = byDate.get(date) ?? 'past'
          const isSelected = selected.includes(date)
          const className = ['cal-day', status, isSelected ? 'selected' : ''].join(' ')
          return (
            <button
              key={date}
              type="button"
              className={className}
              disabled={status !== 'free'}
              aria-label={`${date} — ${status}`}
              onClick={() => onPick?.(date)}
            >
              {dayjs(date).date()}
            </button>
          )
        })}
      </div>
      <div className="cal-legend">
        <span className="lg"><span className="sw" style={{ background: 'rgba(16,185,129,0.5)' }} /> свободно</span>
        <span className="lg"><span className="sw" style={{ background: 'rgba(245,158,11,0.5)' }} /> занято</span>
        <span className="lg"><span className="sw" style={{ background: 'rgba(239,68,68,0.5)' }} /> заблокировано</span>
      </div>
    </div>
  )
}
