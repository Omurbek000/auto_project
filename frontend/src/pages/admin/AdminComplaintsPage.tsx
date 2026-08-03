import { useState } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { complaintApi } from '@/api'
import { apiErrorText } from '@/api/client'
import { AdminSidebar } from '@/layouts/Layouts'
import { ComplaintStatusBadge, EmptyState, ErrorBox, Pagination, Spinner } from '@/components/ui'
import { useToast } from '@/components/Toast'
import dayjs from 'dayjs'
import type { Complaint, ComplaintStatus } from '@/types/api'

const PAGE_SIZE = 15
const STATUSES: ComplaintStatus[] = ['pending', 'reviewing', 'resolved', 'rejected']

function Row({ complaint }: { complaint: Complaint }) {
  const toast = useToast()
  const qc = useQueryClient()
  const [status, setStatus] = useState<ComplaintStatus>(complaint.status)
  const [response, setResponse] = useState(complaint.admin_response ?? '')

  const mutate = useMutation({
    mutationFn: () =>
      complaintApi.update(complaint.id, {
        status,
        admin_response: response || undefined,
      }),
    onSuccess: () => {
      toast.success('Жалоба обновлена')
      void qc.invalidateQueries({ queryKey: ['admin-complaints'] })
    },
    onError: (err) => toast.error(apiErrorText(err)),
  })

  return (
    <div className="glass glass-card">
      <div className="row row-wrap" style={{ justifyContent: 'space-between' }}>
        <div>
          <div style={{ fontWeight: 700 }}>
            {complaint.reason}
            {complaint.target_user && (
              <span className="muted" style={{ fontWeight: 400 }}> — на {complaint.target_user.username}</span>
            )}
          </div>
          <div className="muted text-sm">
            от {complaint.author.username} · {dayjs(complaint.created_date).format('DD.MM.YYYY HH:mm')}
          </div>
        </div>
        <ComplaintStatusBadge status={complaint.status} />
      </div>
      {complaint.description && (
        <p className="card-desc mt-12" style={{ padding: '10px 14px', background: 'rgba(255,255,255,0.04)', borderRadius: 10 }}>
          {complaint.description}
        </p>
      )}
      <div className="row row-wrap mt-16" style={{ gap: 10, alignItems: 'flex-end' }}>
        <div style={{ flex: 1, minWidth: 200 }}>
          <label htmlFor={`st-${complaint.id}`} className="muted text-sm" style={{ display: 'block', marginBottom: 6 }}>
            Статус
          </label>
          <select
            id={`st-${complaint.id}`}
            className="select"
            value={status}
            onChange={(e) => setStatus(e.target.value as ComplaintStatus)}
          >
            {STATUSES.map((s) => (
              <option key={s} value={s}>{s}</option>
            ))}
          </select>
        </div>
        <div style={{ flex: 2, minWidth: 260 }}>
          <label htmlFor={`rs-${complaint.id}`} className="muted text-sm" style={{ display: 'block', marginBottom: 6 }}>
            Ответ администратора
          </label>
          <input
            id={`rs-${complaint.id}`}
            className="input"
            value={response}
            onChange={(e) => setResponse(e.target.value)}
            placeholder="Ответ пользователю…"
          />
        </div>
        <button className="btn btn-primary" disabled={mutate.isPending} onClick={() => mutate.mutate()}>
          Сохранить
        </button>
      </div>
    </div>
  )
}

export function AdminComplaintsPage() {
  const [page, setPage] = useState(1)

  const { data, isPending, isError, error } = useQuery({
    queryKey: ['admin-complaints', page],
    queryFn: () => complaintApi.list({ page, page_size: PAGE_SIZE }).then((r) => r.data),
  })

  return (
    <AdminSidebar>
      <div className="kicker">Поддержка</div>
      <h1 className="page-title" style={{ fontSize: 22, marginBottom: 18 }}>Жалобы пользователей</h1>
      <p className="page-sub" style={{ fontSize: 14 }}>
        Меняйте статус и отвечайте пользователям. Все действия записываются в аудит.
      </p>

      {isPending ? (
        <Spinner />
      ) : isError ? (
        <ErrorBox text={error instanceof Error ? error.message : 'Ошибка загрузки'} />
      ) : data && data.results.length === 0 ? (
        <EmptyState text="Жалоб нет. Отлично!" />
      ) : (
        <div style={{ display: 'grid', gap: 14 }}>
          {data?.results.map((c) => <Row key={c.id} complaint={c} />)}
        </div>
      )}
      {data && <Pagination count={data.count} page={page} pageSize={PAGE_SIZE} onPage={setPage} />}
    </AdminSidebar>
  )
}
