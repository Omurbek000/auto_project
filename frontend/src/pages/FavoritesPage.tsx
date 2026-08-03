import { useState } from 'react'
import { Link } from 'react-router-dom'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { Heart, Star } from 'lucide-react'
import { favoriteApi } from '@/api'
import { apiErrorText } from '@/api/client'
import { CarCard } from '@/components/CarCard'
import { EmptyState, ErrorBox, Pagination, Spinner } from '@/components/ui'
import { SidebarLayout, type SideNavItem } from '@/layouts/Layouts'
import { useToast } from '@/components/Toast'

const PAGE_SIZE = 12
const NAV: SideNavItem[] = [
  { to: '/rentals', label: 'Мои аренды', icon: <Heart size={17} /> },
  { to: '/favorites', label: 'Избранное', icon: <Star size={17} /> },
  { to: '/profile', label: 'Профиль', icon: <Heart size={17} /> },
]

export function FavoritesPage() {
  const [page, setPage] = useState(1)
  const qc = useQueryClient()
  const toast = useToast()

  const { data, isPending, isError, error } = useQuery({
    queryKey: ['favorites', page],
    queryFn: () => favoriteApi.list({ page, page_size: PAGE_SIZE }).then((r) => r.data),
  })

  const remove = useMutation({
    mutationFn: (id: number) => favoriteApi.remove(id),
    onSuccess: () => {
      toast.success('Убрано из избранного')
      void qc.invalidateQueries({ queryKey: ['favorites'] })
    },
    onError: (err) => toast.error(apiErrorText(err)),
  })

  return (
    <SidebarLayout items={NAV} title="Избранное">
      {isPending ? (
        <Spinner />
      ) : isError ? (
        <ErrorBox text={error instanceof Error ? error.message : 'Ошибка загрузки'} />
      ) : data && data.results.length === 0 ? (
        <EmptyState
          text="Пока нет избранных машин. Нажмите на сердечко в карточке, чтобы сохранить её здесь."
        />
      ) : (
        <>
          <div className="grid g3">
            {data?.results.map((f) => (
              <div key={f.id} style={{ position: 'relative' }}>
                <button
                  className="btn btn-sm"
                  style={{ position: 'absolute', top: 10, right: 10, zIndex: 2 }}
                  onClick={() => remove.mutate(f.id)}
                  aria-label="Убрать из избранного"
                >
                  <Heart size={15} fill="currentColor" />
                </button>
                <CarCard car={f.car} />
              </div>
            ))}
          </div>
          <div className="mt-16" style={{ textAlign: 'center' }}>
            <Link to="/" className="btn btn-primary">
              Найти ещё машины
            </Link>
          </div>
          {data && <Pagination count={data.count} page={page} pageSize={PAGE_SIZE} onPage={setPage} />}
        </>
      )}
    </SidebarLayout>
  )
}
