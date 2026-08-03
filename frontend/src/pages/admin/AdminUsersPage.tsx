import { useMemo, useState } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { Ban, BadgeCheck, Car, ShieldCheck, UserRound } from 'lucide-react'
import { adminApi } from '@/api'
import { apiErrorText } from '@/api/client'
import { AdminSidebar } from '@/layouts/Layouts'
import { EmptyState, ErrorBox, Pagination, Spinner } from '@/components/ui'
import { exportCsv } from '@/components/exportCsv'
import { useToast } from '@/components/Toast'
import { useDebounce } from '@/hooks/useDebounce'

const PAGE_SIZE = 20

export function AdminUsersPage() {
  const toast = useToast()
  const qc = useQueryClient()
  const [search, setSearch] = useState('')
  const [filter, setFilter] = useState('')
  const [page, setPage] = useState(1)
  const debounced = useDebounce(search, 350)

  const { data, isPending, isError, error } = useQuery({
    queryKey: ['admin-users', { debounced, filter, page }],
    queryFn: () =>
      adminApi.users({ search: debounced, ...(filter ? { [filter]: 'true' } : {}), page, page_size: PAGE_SIZE }).then((r) => r.data),
  })

  const mutate = useMutation({
    mutationFn: ({ id, patch }: { id: number; patch: Record<string, unknown> }) => adminApi.updateUser(id, patch),
    onSuccess: () => {
      toast.success('Сохранено')
      void qc.invalidateQueries({ queryKey: ['admin-users'] })
    },
    onError: (err) => toast.error(apiErrorText(err)),
  })

  const rows = useMemo(
    () =>
      data?.results.map((u) => ({
        id: u.id,
        username: u.username,
        email: u.email,
        phone: u.phone_number ?? '',
        roles: [u.is_owner ? 'owner' : '', u.is_renter ? 'renter' : ''].filter(Boolean).join(', '),
        verified: u.is_verified ? 'да' : 'нет',
        active: u.is_active ? 'активен' : 'заблокирован',
      })) ?? [],
    [data],
  )

  return (
    <AdminSidebar>
      <div className="row row-wrap" style={{ marginBottom: 18, gap: 12 }}>
        <input
          className="input"
          style={{ maxWidth: 320 }}
          placeholder="Поиск: имя, email, телефон…"
          value={search}
          onChange={(e) => { setSearch(e.target.value); setPage(1) }}
          aria-label="Поиск пользователей"
        />
        <select className="select" style={{ maxWidth: 220 }} value={filter} onChange={(e) => { setFilter(e.target.value); setPage(1) }} aria-label="Фильтр">
          <option value="">Все пользователи</option>
          <option value="is_owner">Владельцы</option>
          <option value="is_renter">Арендаторы</option>
          <option value="is_active">Активные</option>
        </select>
        <button
          className="btn btn-sm btn-danger"
          onClick={() => exportCsv('users', rows)}
        >
          Экспорт CSV
        </button>
      </div>

      {isPending ? (
        <Spinner />
      ) : isError ? (
        <ErrorBox text={error instanceof Error ? error.message : 'Ошибка загрузки'} />
      ) : data && data.results.length === 0 ? (
        <EmptyState text="Пользователи не найдены" />
      ) : (
        <>
          <div className="glass glass-card">
            <div className="table-wrap">
              <table className="table">
                <thead>
                  <tr>
                    <th>Пользователь</th>
                    <th>Роли</th>
                    <th>Верифицирован</th>
                    <th>Статус</th>
                    <th style={{ textAlign: 'right' }}>Действия</th>
                  </tr>
                </thead>
                <tbody>
                  {data?.results.map((u) => (
                    <tr key={u.id}>
                      <td>
                        <div style={{ fontWeight: 700 }}>{u.username}</div>
                        <div className="muted text-sm">{u.email}{u.phone_number ? ` · ${u.phone_number}` : ''}</div>
                      </td>
                      <td>
                        <div className="row" style={{ gap: 6 }}>
                          {u.is_owner && <span className="badge st-completed"><Car size={11} /> owner</span>}
                          {u.is_renter && <span className="badge st-confirmed"><UserRound size={11} /> renter</span>}
                        </div>
                      </td>
                      <td>
                        <span className={`badge ${u.is_verified ? 'st-active' : 'st-default'}`}>
                          <BadgeCheck size={12} /> {u.is_verified ? 'да' : 'нет'}
                        </span>
                      </td>
                      <td>
                        <span className={`badge ${u.is_active ? 'st-active' : 'st-canceled'}`}>
                          {u.is_active ? 'активен' : 'заблокирован'}
                        </span>
                      </td>
                      <td>
                        <div className="row" style={{ gap: 6, justifyContent: 'flex-end' }}>
                          {u.is_verified ? (
                            <button className="btn btn-sm btn-ghost" onClick={() => mutate.mutate({ id: u.id, patch: { is_verified: false } })}>
                              Снять проверку
                            </button>
                          ) : (
                            <button className="btn btn-sm btn-success" onClick={() => mutate.mutate({ id: u.id, patch: { is_verified: true } })}>
                              <BadgeCheck size={13} /> Проверить
                            </button>
                          )}
                          <button className="btn btn-sm btn-ghost" onClick={() => mutate.mutate({ id: u.id, patch: { is_owner: !u.is_owner } })}>
                            {u.is_owner ? '− owner' : '+ owner'}
                          </button>
                          {u.is_active ? (
                            <button className="btn btn-sm btn-danger" onClick={() => mutate.mutate({ id: u.id, patch: { is_active: false } })}>
                              <Ban size={13} /> Блокировать
                            </button>
                          ) : (
                            <button className="btn btn-sm btn-success" onClick={() => mutate.mutate({ id: u.id, patch: { is_active: true } })}>
                              <ShieldCheck size={13} /> Разблокировать
                            </button>
                          )}
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
          {data && <Pagination count={data.count} page={page} pageSize={PAGE_SIZE} onPage={setPage} />}
        </>
      )}
    </AdminSidebar>
  )
}
