import { useEffect, useRef, useState } from 'react'
import { Link, useParams } from 'react-router-dom'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { ArrowLeft, Send } from 'lucide-react'
import { chatApi } from '@/api'
import { apiErrorText } from '@/api/client'
import { useAuth } from '@/features/auth/AuthContext'
import { ErrorBox, Spinner } from '@/components/ui'
import { useToast } from '@/components/Toast'
import dayjs from 'dayjs'

export function ChatPage() {
  const { id } = useParams()
  const chatId = Number(id)
  const { user } = useAuth()
  const toast = useToast()
  const qc = useQueryClient()
  const [text, setText] = useState('')
  const bottomRef = useRef<HTMLDivElement>(null)

  const { data: chat, isPending, isError, error } = useQuery({
    queryKey: ['chat', chatId],
    queryFn: () => chatApi.detail(chatId).then((r) => r.data),
    enabled: Number.isFinite(chatId),
    refetchInterval: 4000,
  })

  useEffect(() => {
    if (Number.isFinite(chatId)) void chatApi.markRead(chatId).catch(() => undefined)
  }, [chatId])

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [chat?.messages.length])

  const send = useMutation({
    mutationFn: () => chatApi.send(chatId, text.trim()),
    onSuccess: () => {
      setText('')
      void qc.invalidateQueries({ queryKey: ['chat', chatId] })
      void qc.invalidateQueries({ queryKey: ['chats'] })
    },
    onError: (err) => toast.error(apiErrorText(err)),
  })

  if (isPending) return <Spinner />
  if (isError || !chat)
    return <ErrorBox text={error instanceof Error ? error.message : 'Чат не найден'} />

  const other = user?.id === chat.rental.renter.id ? chat.rental.car.owner : chat.rental.renter

  return (
    <div className="container page page-tight">
      <div className="row" style={{ marginBottom: 16, gap: 14 }}>
        <Link to="/chat" className="btn btn-ghost btn-sm" aria-label="Назад к чатам">
          <ArrowLeft size={17} />
        </Link>
        <div>
          <div style={{ fontWeight: 800, fontSize: 18 }}>
            {chat.rental.car.brand} {chat.rental.car.model_name}
          </div>
          <div className="muted text-sm">
            {other.username} · аренда {chat.rental.start_date} — {chat.rental.end_date}
          </div>
        </div>
      </div>

      <div className="glass chat-thread">
        <div className="msg-list" aria-live="polite">
          {chat.messages.length === 0 && (
            <p className="muted text-sm" style={{ textAlign: 'center', margin: 'auto' }}>
              Напишите первое сообщение по этой аренде
            </p>
          )}
          {chat.messages.map((m) => (
            <div key={m.id} className={`msg${m.sender.id === user?.id ? ' mine' : ''}`}>
              {m.message}
              <div className="m-time">
                {dayjs(m.created_date).format('DD.MM HH:mm')}
                {m.sender.id === user?.id && (m.is_read ? ' · прочитано' : '')}
              </div>
            </div>
          ))}
          <div ref={bottomRef} />
        </div>
        <form
          className="msg-form"
          onSubmit={(e) => {
            e.preventDefault()
            if (text.trim()) send.mutate()
          }}
        >
          <input
            className="input"
            value={text}
            onChange={(e) => setText(e.target.value)}
            placeholder="Сообщение…"
            aria-label="Текст сообщения"
          />
          <button className="btn btn-primary" disabled={!text.trim() || send.isPending} aria-label="Отправить">
            <Send size={17} />
          </button>
        </form>
      </div>
    </div>
  )
}
