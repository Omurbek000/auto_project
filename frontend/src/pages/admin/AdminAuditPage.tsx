import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { ScrollText } from 'lucide-react'
import { adminApi } from '@/api'
import { AdminSidebar } from '@/layouts/Layouts'
import { EmptyState, ErrorBox, Pagination, Spinner } from '@/components/ui'
import { exportCsv } from '@/components/exportCsv'
import dayjs from 'dayjs'

const PAGE_SIZE = 25

export function AdminAuditPage() {
  const [page, setPage] = useState(1)

  const { data, isPending, isError, error } = useQuery({
    queryKey: ['admin-audit', page],
    queryFn: () => adminApi.audit({ page, page_size: PAGE_SIZE }).then((r) => r.data),
  })

  const exportAudit = () =>
    exportCsv(
      'audit-log',
      data?.results.map((a) => ({
        created: dayjs(a.created_date).format('YYYY-MM-DD HH:mm'),
        user: a.username ?? a.user ?? '',
        action: a.action,
        model: a.model_name,
        object_id: a.object_id ?? '',
        details: a.details ? JSON.stringify(a.details) : '',
      })) ?? [],
    )

  return (
    <AdminSidebar>
      <div className="row" style={{ justifyContent: 'space-between', marginBottom: 18 }}>
        <div>
          <div className="kicker">Безопасность</div>
          <h1 className="page-title" style={{ fontSize: 22, margin: 0 }}>Журнал аудита</h1>
        </div>
        <button className="btn btn-sm" onClick={exportAudit}>
          Экспорт CSV
        </button>
      </div>
      <p className="page-sub" style={{ fontSize: 14 }}>
        Кто, что и когда делал: блокировки, верификация, роли, жалобы.
      </p>

      {isPending ? (
        <Spinner />
      ) : isError ? (
        <ErrorBox text={error instanceof Error ? error.message : 'Ошибка загрузки'} />
      ) : data && data.results.length === 0 ? (
        <EmptyState text="Записей пока нет" />
      ) : (
        <div className="glass glass-card">
          <div className="table-wrap">
            <table className="table">
              <thead>
                <tr>
                  <th>Дата</th>
                  <th>Пользователь</th>
                  <th>Действие</th>
                  <th>Объект</th>
                  <th>Детали</th>
                </tr>
              </thead>
              <tbody>
                {data?.results.map((a) => (
                  <tr key={a.id}>
                    <td className="num" style={{ whiteSpace: 'nowrap' }}>
                      {dayjs(a.created_date).format('DD.MM.YYYY HH:mm')}
                    </td>
                    <td style={{ fontWeight: 600 }}>{a.username ?? a.user ?? 'система'}</td>
                    <td>
                      <span className="badge st-confirmed">
                        <ScrollText size={11} /> {a.action}
                      </span>
                    </td>
                    <td className="muted">
                      {a.model_name}
                      {a.object_id ? ` #${a.object_id}` : ''}
                    </td>
                    <td className="muted text-sm">
                      {a.details ? (
                        <details>
                          <summary style={{ cursor: 'pointer' }}>подробнее</summary>
                          <pre className="mono" style={{ marginTop: 6, fontSize: 11.5, color: 'var(--txt2)' }}>
                            {JSON.stringify(a.details, null, 2)}
                          </pre>
                        </details>
                      ) : (
                        '—'
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
      {data && <Pagination count={data.count} page={page} pageSize={PAGE_SIZE} onPage={setPage} />}
    </AdminSidebar>
  )
}
