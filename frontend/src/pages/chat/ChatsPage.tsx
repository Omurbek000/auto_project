import { Link } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import { MessageSquare } from 'lucide-react'
import { chatApi } from '@/api'
import { mediaUrl } from '@/api/client'
import { useAuth } from '@/features/auth/AuthContext'
import { EmptyState, ErrorBox, Spinner } from '@/components/ui'
import dayjs from 'dayjs'

export function ChatsPage() {
  const { user } = useAuth()

  const { data, isPending, isError, error } = useQuery({
    queryKey: ['chats'],
    queryFn: () => chatApi.list({ page_size: 100 }).then((r) => r.data),
    refetchInterval: 10_000,
  })

  if (isPending) return <Spinner />
  if (isError) return <ErrorBox text={error instanceof Error ? error.message : 'Ошибка загрузки'} />

  return (
    <div className="container page">
      <div className="kicker">Сообщения</div>
      <h1 className="page-title">Чаты</h1>
      <p className="page-sub">Переписка с владельцами и арендаторами по каждой аренде.</p>

      {data && data.results.length === 0 ? (
        <EmptyState text="Чаты появляются автоматически при бронировании машины." />
      ) : (
        <div className="grid g3">
          {data?.results.map((chat) => {
            const other = user?.id === chat.rental.renter.id ? chat.rental.car.owner : chat.rental.renter
            const carImg = chat.rental.car.image ?? chat.rental.car.images[0]?.image
            const last = chat.messages[chat.messages.length - 1]
            return (
              <Link key={chat.id} to={`/chat/${chat.id}`} className="glass hoverable chat-item">
                {carImg ? (
                  <img src={mediaUrl(carImg)} alt="" style={{ width: 52, height: 52, borderRadius: 12, objectFit: 'cover', flex: 'none' }} />
                ) : (
                  <span className="avatar" style={{ width: 52, height: 52 }}>
                    <MessageSquare size={20} />
                  </span>
                )}
                <div style={{ minWidth: 0 }}>
                  <div style={{ fontWeight: 700 }}>
                    {chat.rental.car.brand} {chat.rental.car.model_name}
                  </div>
                  <div className="text-sm" style={{ color: 'var(--txt2)' }}>
                    {other.username}
                  </div>
                  <div className="last">
                    {last ? (
                      <>
                        <b>{last.sender.id === user?.id ? 'Вы: ' : ''}</b>
                        {last.message}
                      </>
                    ) : (
                      'Нет сообщений'
                    )}
                  </div>
                  {last && (
                    <div className="text-sm muted">{dayjs(last.created_date).format('DD.MM HH:mm')}</div>
                  )}
                </div>
              </Link>
            )
          })}
        </div>
      )}
    </div>
  )
}
