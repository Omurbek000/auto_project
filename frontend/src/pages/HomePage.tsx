import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { MapPin, Search, SlidersHorizontal } from 'lucide-react'
import { carApi, statsApi } from '@/api'
import { CarCard } from '@/components/CarCard'
import { EmptyState, ErrorBox, Pagination, Spinner } from '@/components/ui'
import { useDebounce } from '@/hooks/useDebounce'

const PAGE_SIZE = 12

export function HomePage() {
  const [search, setSearch] = useState('')
  const [brand, setBrand] = useState('')
  const [fuelType, setFuelType] = useState('')
  const [transmission, setTransmission] = useState('')
  const [maxPrice, setMaxPrice] = useState('')
  const [startDate, setStartDate] = useState('')
  const [endDate, setEndDate] = useState('')
  const [page, setPage] = useState(1)

  const debouncedSearch = useDebounce(search, 350)

  const hasDates = Boolean(startDate && endDate)

  const { data, isPending, isError, error } = useQuery({
    queryKey: ['cars', { debouncedSearch, brand, fuelType, transmission, maxPrice, startDate, endDate, page }],
    queryFn: () => {
      const params: Record<string, string | number> = {
        search: debouncedSearch,
        brand,
        fuel_type: fuelType,
        transmission,
        price_per_day__lte: maxPrice,
        page,
        page_size: PAGE_SIZE,
      }
      if (hasDates) {
        return carApi.available(startDate, endDate, params).then((r) => r.data)
      }
      return carApi.list(params).then((r) => r.data)
    },
  })

  const { data: global } = useQuery({
    queryKey: ['global-stats'],
    queryFn: () => statsApi.global().then((r) => r.data),
    retry: false,
  })

  const filtersDirty =
    search || brand || fuelType || transmission || maxPrice || startDate || endDate

  return (
    <div className="page">
      <div className="container">
        <div className="glass glass-card" style={{ marginBottom: 28, padding: '28px 28px 24px' }}>
          <div className="kicker">Каталог</div>
          <h1 className="page-title">Аренда автомобилей</h1>
          <p className="page-sub" style={{ marginBottom: 20 }}>
            {global && (
              <>
                На площадке уже <b>{global.total_cars}</b> машин, арендаторы оставили{' '}
                <b>{global.total_rentals}</b> заявок. Найдите свою!
              </>
            )}
          </p>

          <div className="glass glass-card" style={{ padding: 18, boxShadow: 'none' }}>
            <div className="grid g2" style={{ gap: 14 }}>
              <div className="row" style={{ position: 'relative' }}>
                <Search size={17} style={{ position: 'absolute', left: 12, color: 'var(--txt3)' }} />
                <input
                  className="input"
                  style={{ paddingLeft: 38 }}
                  placeholder="Поиск по названию, марке, описанию…"
                  value={search}
                  onChange={(e) => {
                    setSearch(e.target.value)
                    setPage(1)
                  }}
                  aria-label="Поиск"
                />
              </div>
              <div className="row" style={{ gap: 10 }}>
                <div className="flex-1" style={{ position: 'relative' }}>
                  <MapPin size={15} style={{ position: 'absolute', left: 12, top: '50%', transform: 'translateY(-50%)', color: 'var(--txt3)', zIndex: 1 }} />
                  <input
                    className="input"
                    style={{ paddingLeft: 34 }}
                    placeholder="Город (например, Москва)"
                    value={brand}
                    onChange={(e) => { setBrand(e.target.value); setPage(1) }}
                    aria-label="Город"
                  />
                </div>
              </div>
            </div>
            <div className="grid g4" style={{ gap: 12, marginTop: 14 }}>
              <select
                className="select"
                value={fuelType}
                onChange={(e) => { setFuelType(e.target.value); setPage(1) }}
                aria-label="Тип топлива"
              >
                <option value="">Топливо: любое</option>
                <option value="petrol">Бензин</option>
                <option value="diesel">Дизель</option>
                <option value="electric">Электро</option>
                <option value="hybrid">Гибрид</option>
              </select>
              <select
                className="select"
                value={transmission}
                onChange={(e) => { setTransmission(e.target.value); setPage(1) }}
                aria-label="Коробка передач"
              >
                <option value="">КПП: любая</option>
                <option value="auto">Автомат</option>
                <option value="manual">Механика</option>
              </select>
              <input
                className="input"
                type="number"
                min={0}
                placeholder="Цена до, ₽/день"
                value={maxPrice}
                onChange={(e) => { setMaxPrice(e.target.value); setPage(1) }}
                aria-label="Максимальная цена"
              />
              <div className="row filter-dates" style={{ gap: 8 }}>
                <input
                  className="input"
                  type="date"
                  value={startDate}
                  onChange={(e) => { setStartDate(e.target.value); setPage(1) }}
                  aria-label="Дата начала"
                />
                <input
                  className="input"
                  type="date"
                  value={endDate}
                  onChange={(e) => { setEndDate(e.target.value); setPage(1) }}
                  aria-label="Дата окончания"
                />
              </div>
            </div>
            <div className="row filter-reset-row" style={{ justifyContent: 'space-between', marginTop: 14 }}>
              <span className="text-sm muted">
                {hasDates ? (
                  <>Показаны машины, свободные с <b>{startDate}</b> по <b>{endDate}</b></>
                ) : (
                  <>Укажите даты, чтобы увидеть только свободные машины</>
                )}
              </span>
              {filtersDirty && (
                <button
                  className="btn btn-ghost btn-sm"
                  onClick={() => {
                    setSearch('')
                    setBrand('')
                    setFuelType('')
                    setTransmission('')
                    setMaxPrice('')
                    setStartDate('')
                    setEndDate('')
                    setPage(1)
                  }}
                >
                  <SlidersHorizontal size={15} /> Сбросить фильтры
                </button>
              )}
            </div>
          </div>
        </div>

        {isPending ? (
          <Spinner label="Загружаем машины…" />
        ) : isError ? (
          <ErrorBox text={error instanceof Error ? error.message : 'Не удалось загрузить каталог'} />
        ) : data && data.results.length === 0 ? (
          <EmptyState text="По вашим фильтрам ничего не найдено. Попробуйте изменить условия поиска." />
        ) : (
          <>
            <div className="grid g3">
              {data?.results.map((car) => <CarCard key={car.id} car={car} />)}
            </div>
            {data && (
              <Pagination count={data.count} page={page} pageSize={PAGE_SIZE} onPage={setPage} />
            )}
          </>
        )}
      </div>
    </div>
  )
}
