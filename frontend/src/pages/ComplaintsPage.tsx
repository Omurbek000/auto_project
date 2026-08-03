import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { complaintApi } from '@/api'
import { ComplaintStatusBadge, EmptyState, ErrorBox, Pagination, Spinner } from '@/components/ui'
import dayjs from 'dayjs'

const PAGE_SIZE = 10

export function ComplaintsPage() {
  const [page, setPage] = useState(1)

  const { data, isPending, isError, error } = useQuery({
    queryKey: ['complaints', page],
    queryFn: () => complaintApi.list({ page, page_size: PAGE_SIZE }).then((r) => r.data),
  })

  return (
    <div className="container page">
      <div className="kicker">Поддержка</div>
      <h1 className="page-title">Жалобы</h1>
      <p className="page-sub">
        Подать жалобу можно из карточки аренды. Администрация рассмотрит и ответит здесь.
      </p>

      {isPending ? (
        <Spinner />
      ) : isError ? (
        <ErrorBox text={error instanceof Error ? error.message : 'Ошибка загрузки'} />
      ) : data && data.results.length === 0 ? (
        <EmptyState text="Жалоб пока нет. Если возникла проблема с арендой — нажмите «Пожаловаться» в списке аренд." />
      ) : (
        <div style={{ display: 'grid', gap: 14 }}>
          {data?.results.map((c) => (
            <div key={c.id} className="glass glass-card">
              <div className="row row-wrap" style={{ justifyContent: 'space-between' }}>
                <div>
                  <div style={{ fontWeight: 700 }}>
                    {c.reason}
                    {c.target_user && (
                      <span className="muted" style={{ fontWeight: 400 }}> — на {c.target_user.username}</span>
                    )}
                  </div>
                  {c.description && <p className="card-desc mt-8">{c.description}</p>}
                </div>
                <ComplaintStatusBadge status={c.status} />
              </div>
              <div className="row row-wrap mt-12" style={{ justifyContent: 'space-between' }}>
                <span className="muted text-sm">{dayjs(c.created_date).format('DD.MM.YYYY HH:mm')}</span>
                {c.admin_response && (
                  <span className="text-sm" style={{ color: 'var(--txt2)' }}>
                    <b>Ответ админа:</b> {c.admin_response}
                  </span>
                )}
              </div>
            </div>
          ))}
        </div>
      )}
      {data && <Pagination count={data.count} page={page} pageSize={PAGE_SIZE} onPage={setPage} />}
    </div>
  )
}
