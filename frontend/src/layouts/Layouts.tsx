import { useEffect, useRef, useState, type ReactNode } from 'react'
import { Link, NavLink, Outlet, useNavigate } from 'react-router-dom'
import {
  BarChart3,
  Car,
  ChevronDown,
  FolderHeart,
  Heart,
  LayoutDashboard,
  MessageSquare,
  ShieldAlert,
  ShieldCheck,
  User as UserIcon,
  LogOut,
} from 'lucide-react'
import { useAuth } from '@/features/auth/AuthContext'
import { mediaUrl } from '@/api/client'

function ProfileDropdown() {
  const { user, isAdmin, isOwner, logout } = useAuth()
  const navigate = useNavigate()
  const [open, setOpen] = useState(false)
  const ref = useRef<HTMLDivElement>(null)

  useEffect(() => {
    function onClick(e: MouseEvent) {
      if (ref.current && !ref.current.contains(e.target as Node)) setOpen(false)
    }
    document.addEventListener('mousedown', onClick)
    return () => document.removeEventListener('mousedown', onClick)
  }, [])

  if (!user) {
    return (
      <Link to="/login" className="btn btn-primary btn-sm">
        Войти
      </Link>
    )
  }

  return (
    <div className="profile-menu" ref={ref}>
      <button
        className="profile-btn"
        onClick={() => setOpen((o) => !o)}
        aria-expanded={open}
        aria-haspopup="menu"
      >
        {user.avatar ? (
          <span className="avatar">
            <img src={mediaUrl(user.avatar)} alt="" />
          </span>
        ) : (
          <span className="avatar">{user.username.slice(0, 1).toUpperCase()}</span>
        )}
        <span className="p-name">{user.username}</span>
        <ChevronDown size={15} style={{ color: 'var(--txt3)' }} />
      </button>
      {open && (
        <div className="dropdown" role="menu">
          <Link to="/profile" className="dropdown-item" onClick={() => setOpen(false)}>
            <UserIcon size={16} /> Профиль
          </Link>
          <Link to="/rentals" className="dropdown-item" onClick={() => setOpen(false)}>
            <FolderHeart size={16} /> Мои аренды
          </Link>
          <Link to="/favorites" className="dropdown-item" onClick={() => setOpen(false)}>
            <Heart size={16} /> Избранное
          </Link>
          {isOwner && (
            <>
              <Link to="/my-cars" className="dropdown-item" onClick={() => setOpen(false)}>
                <Car size={16} /> Мои машины
              </Link>
              <Link to="/owner/stats" className="dropdown-item" onClick={() => setOpen(false)}>
                <BarChart3 size={16} /> Статистика
              </Link>
            </>
          )}
          {isAdmin && (
            <Link to="/admin/dashboard" className="dropdown-item" onClick={() => setOpen(false)}>
              <ShieldCheck size={16} /> Админ-панель
            </Link>
          )}
          <div className="dropdown-sep" />
          <button
            className="dropdown-item"
            onClick={() => {
              setOpen(false)
              void logout().then(() => navigate('/'))
            }}
          >
            <LogOut size={16} /> Выйти
          </button>
        </div>
      )}
    </div>
  )
}

export function MainLayout() {
  const { isAuthenticated, isOwner, isAdmin } = useAuth()
  return (
    <>
      <header className="topbar">
        <Link to="/" className="logo">
          AVTO<span>.</span>
        </Link>
        <nav className="nav-links" aria-label="Основная навигация">
          <NavLink to="/" end className={({ isActive }) => `nav-link${isActive ? ' active' : ''}`}>
            Каталог
          </NavLink>
          {isAuthenticated && (
            <>
              <NavLink to="/rentals" className={({ isActive }) => `nav-link${isActive ? ' active' : ''}`}>
                Аренды
              </NavLink>
              <NavLink to="/chat" className={({ isActive }) => `nav-link${isActive ? ' active' : ''}`}>
                Чат
              </NavLink>
              {isOwner && (
                <NavLink to="/my-cars" className={({ isActive }) => `nav-link${isActive ? ' active' : ''}`}>
                  Мои машины
                </NavLink>
              )}
              {isAdmin && (
                <NavLink to="/admin/dashboard" className={({ isActive }) => `nav-link${isActive ? ' active' : ''}`}>
                  Админ
                </NavLink>
              )}
            </>
          )}
        </nav>
        <div className="topbar-spacer" />
        <ProfileDropdown />
      </header>
      <main>
        <Outlet />
      </main>
    </>
  )
}

export interface SideNavItem {
  to: string
  label: string
  icon: ReactNode
  end?: boolean
}

interface SidebarLayoutProps {
  items: SideNavItem[]
  title?: string
  children?: ReactNode
}

export function SidebarLayout({ items, title, children }: SidebarLayoutProps) {
  return (
    <div className="container page">
      {title && (
        <div style={{ marginBottom: 20 }}>
          <div className="kicker">Личный кабинет</div>
          <h1 className="page-title">{title}</h1>
        </div>
      )}
      <div className="dash-layout">
        <aside className="glass sidebar" aria-label="Меню">
          {items.map((item) => (
            <NavLink
              key={item.to}
              to={item.to}
              end={item.end}
              className={({ isActive }) => `nav-link${isActive ? ' active' : ''}`}
            >
              {item.icon}
              {item.label}
            </NavLink>
          ))}
        </aside>
        <div className="dash-content flex-1">{children}</div>
      </div>
    </div>
  )
}

export function AdminSidebar({ children }: { children: ReactNode }) {
  const items: SideNavItem[] = [
    { to: '/admin/dashboard', label: 'Дашборд', icon: <LayoutDashboard size={17} /> },
    { to: '/admin/users', label: 'Пользователи', icon: <ShieldAlert size={17} /> },
    { to: '/admin/complaints', label: 'Жалобы', icon: <ShieldAlert size={17} /> },
    { to: '/admin/audit', label: 'Аудит', icon: <MessageSquare size={17} /> },
  ]
  return (
    <div className="container page">
      <div style={{ marginBottom: 20 }}>
        <div className="kicker">Администрирование</div>
        <h1 className="page-title">Админ-панель</h1>
      </div>
      <div className="dash-layout">
        <aside className="glass sidebar" aria-label="Меню админа">
          {items.map((item) => (
            <NavLink
              key={item.to}
              to={item.to}
              end={item.end}
              className={({ isActive }) => `nav-link${isActive ? ' active' : ''}`}
            >
              {item.icon}
              {item.label}
            </NavLink>
          ))}
        </aside>
        <div className="dash-content flex-1">{children}</div>
      </div>
    </div>
  )
}
