import { Link } from 'react-router-dom'
import { Car, Fuel, Gauge, MapPin } from 'lucide-react'
import type { Car as CarType } from '@/types/api'
import { mediaUrl } from '@/api/client'
import { Stars } from './ui'

const FUEL: Record<string, string> = {
  petrol: 'Бензин',
  diesel: 'Дизель',
  electric: 'Электро',
  hybrid: 'Гибрид',
}

export function CarCard({ car }: { car: CarType }) {
  const image = car.image ?? car.images[0]?.image ?? null
  return (
    <article className="glass hoverable car-card">
      <Link to={`/car/${car.id}`} className="thumb" aria-label={`${car.brand} ${car.model_name}`}>
        {image ? (
          <img src={mediaUrl(image)} alt={`${car.brand} ${car.model_name}`} loading="lazy" />
        ) : (
          <div className="no-img">
            <Car size={44} />
          </div>
        )}
      </Link>
      <div className="body">
        <Link to={`/car/${car.id}`} className="name" style={{ color: 'var(--txt)' }}>
          {car.brand} {car.model_name}
        </Link>
        <div className="row" style={{ gap: 8 }}>
          <Stars rating={car.average_rating} />
          <span className="muted text-sm">({car.feedbacks_count})</span>
        </div>
        <div className="meta">
          <span className="chip" style={{ gap: 5 }}>
            <Fuel size={13} /> {FUEL[car.fuel_type] ?? car.fuel_type}
          </span>
          <span className="chip" style={{ gap: 5 }}>
            <Gauge size={13} /> {car.mileage.toLocaleString('ru-RU')} км
          </span>
          <span className="chip" style={{ gap: 5 }}>
            <MapPin size={13} /> {car.location}
          </span>
        </div>
        <div className="foot">
          <span className="price">
            {car.price_per_day} <small>₽/день</small>
          </span>
          <Link to={`/car/${car.id}`} className="btn btn-primary btn-sm">
            Подробнее
          </Link>
        </div>
      </div>
    </article>
  )
}
