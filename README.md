<p align="center">
  <img src="https://img.shields.io/badge/Django-5.2-092E20?style=for-the-badge&logo=django&logoColor=white" alt="Django 5.2" />
  <img src="https://img.shields.io/badge/DRF-3.15-FF1709?style=for-the-badge&logo=django&logoColor=white" alt="DRF" />
  <img src="https://img.shields.io/badge/React-18-61DAFB?style=for-the-badge&logo=react&logoColor=black" alt="React 18" />
  <img src="https://img.shields.io/badge/TypeScript-5-3178C6?style=for-the-badge&logo=typescript&logoColor=white" alt="TypeScript" />
  <img src="https://img.shields.io/badge/Vite-6-646CFF?style=for-the-badge&logo=vite&logoColor=white" alt="Vite" />
  <img src="https://img.shields.io/badge/TanStack_Query-5-FF4154?style=for-the-badge&logo=react-query&logoColor=white" alt="TanStack Query" />
</p>

<h1 align="center">🚗 AVTO · Car Rental Platform</h1>

<p align="center">
  <b>Маркетплейс аренды автомобилей</b> между владельцами и арендаторами.
  Полный цикл: от регистрации до админ-аналитики.
</p>

<p align="center">
  <img src="https://img.shields.io/badge/status-production_ready-10B981?style=flat-square" />
  <img src="https://img.shields.io/badge/tests-128_passing-10B981?style=flat-square" />
  <img src="https://img.shields.io/badge/endpoints-60+-4F8CFF?style=flat-square" />
  <img src="https://img.shields.io/badge/pages-15-4F8CFF?style=flat-square" />
</p>

---

## ✨ Стек

### 🐍 Бекенд — `avto/`

| | Технология | Зачем |
|---:|---|---|
| 🐍 | **Python 3 · Django 5.2** | Модели, миграции, сигналы, админка |
| 🧩 | **Django REST Framework** | Сериализаторы, views, права, пагинация |
| 🔐 | **SimpleJWT** | Access 5 ч + refresh 30 дн, ротация, blacklist |
| 🗄️ | **SQLite** | БД по умолчанию (PostgreSQL/MySQL — на проде) |
| 🔎 | **django-filter** | Фильтры списков: цена, топливо, статусы, даты |
| 📖 | **drf-yasg** | Интерактивный Swagger на `/docs/` |
| 📧 | **SMTP · Twilio** | Email/SMS-уведомления (в dev — в консоль) |
| 🌐 | **CORS** | Доступ Vite-порта `localhost:5173` |

### ⚛️ Фронтенд — `frontend/`

| | Технология | Зачем |
|---:|---|---|
| ⚛️ | **React 18 + Vite** | SPA, HMR, быстрая сборка |
| 🔷 | **TypeScript** | Строгая типизация всех моделей API |
| 🗂️ | **TanStack Query** | Кэш, рефетчинг, инвалидация, мутации |
| 🧭 | **React Router** | Маршрутизация + защита приватных страниц |
| 📋 | **react-hook-form + zod** | Формы с валидацией |
| 🔌 | **axios** | API-клиент: Bearer-токен, авто-refresh на 401 |
| 🎨 | **lucide-react** | Иконки outline-стиля |
| 📊 | **recharts** | Графики дашбордов |
| 📅 | **dayjs** | Даты аренды, календарь |

---

## 📦 Структура проекта

```
auto_project/
│
├── 🐍 avto/                          # Бекенд (Django)
│   ├── avto/                         # Настройки: settings, urls
│   └── project/                      # Приложение
│       ├── models.py                 # User, Car, Rental, Feedback, Chat…
│       ├── views.py                  # 60+ эндпоинтов
│       ├── serializers.py            # Валидация дат аренды
│       ├── permissions.py            # Права доступа
│       ├── signals.py                # Автоматика: доступность, уведомления
│       ├── services.py               # Email/SMS, журнал аудита
│       ├── filters.py · pagination.py
│       ├── admin.py                  # Админка + read-only аудит
│       └── tests.py                  # 128 автотестов
│
├── ⚛️ frontend/                      # Фронтенд (React)
│   └── src/
│       ├── api/                      # axios-клиент + методы эндпоинтов
│       ├── types/api.ts              # Типы моделей API
│       ├── pages/                    # 15 страниц
│       ├── components/               # ui, CarCard, Calendar, Charts…
│       ├── layouts/                  # Шапка, сайдбар, админ-оболочка
│       ├── features/auth/            # AuthContext + RequireAuth
│       └── index.css                 # Вся тема (glassmorphism, адаптив)
│
├── 🎬 presentation*.html             # Презентации: меню · бекенд · фронтенд
├── 📄 STYLES_GUIDE.txt               # Справочник по стилям и компонентам
└── 📄 requirements.txt               # Зависимости Python
```

---

## 🚀 Быстрый старт

### 1️⃣ Бекенд

```bash
python -m venv venv
venv\Scripts\activate            # Windows
source venv/bin/activate         # macOS/Linux

pip install -r requirements.txt
copy .env.example .env           # Windows
cp .env.example .env             # macOS/Linux

cd avto
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver       # → http://127.0.0.1:8000/
```

### 2️⃣ Фронтенд

```bash
cd frontend
npm install
npm run dev                      # → http://localhost:5173/
```

> 💡 Vite проксирует запросы на бекенд. Подробности — `SETUP_GUIDE.txt`, `.env`.

---

## 🎯 Возможности

| | Возможность | Детали |
|---:|---|---|
| 🔍 | **Каталог** | Поиск с debounce, фильтры (город, топливо, КПП, цена, даты), серверная пагинация |
| 🖼️ | **Лайтбокс фото** | Просмотр как на маркетплейсах: листание `← →`, `ESC`, счётчик |
| 📸 | **Менеджер фото** | Пакетная загрузка нескольких файлов, выбор основного фото (`is_main`) |
| 📅 | **Календарь брони** | Дни: свободно / занято / заблокировано, автоподсчёт цены |
| 🔄 | **Цикл аренды** | `pending → confirmed → active → completed`, продление, защита от двойного бронирования |
| 💬 | **Чат** | По каждой аренде, отметки прочитанного, автообновление |
| ⭐ | **Отзывы** | Только участники завершённой аренды |
| 👥 | **Роли** | Арендатор / владелец / админ с раздельным UI |
| 📊 | **Дашборды** | KPI, графики, экспорт CSV, журнал операций, аудит |
| 🔒 | **Безопасность** | JWT, `is_staff` не выдаётся через API, финансы анонимны для админа |

---

## 🧪 Тесты

```bash
python manage.py test
```

✅ **128 автотестов** — модели, авторизация, CRUD, права, полный цикл аренды,
конфликты дат, гонка бронирования, отзывы, чат, календарь, пагинация, аудит.

---

## 🎬 Презентации

Открой `presentation_menu.html` и выбери раздел:

| Файл | Что это |
|---|---|
| 🎬 `presentation_menu.html` | Меню: выбор бекенд / фронтенд |
| 🐍 `presentation.html` | Презентация бекенда |
| ⚛️ `presentation_frontend.html` | Презентация фронтенда |

Управление слайдами: `← →`, `F` — полный экран.

---

## 🔗 Полезные URL

| URL | Что это |
|---|---|
| 🐍 `http://127.0.0.1:8000/docs/` | Swagger — интерактивная документация |
| 🛠️ `http://127.0.0.1:8000/admin/` | Админка Django |
| ⚛️ `http://localhost:5173/` | Фронтенд (Vite) |

---

## 📝 Заметки

- 📧 Email/SMS в dev-режиме выводятся в консоль (см. `.env.example`).
- 👤 При регистрации пользователь сразу `renter`; чтобы сдавать машины — `is_owner: true`.
- 🛡️ Админ создаётся через `createsuperuser` (`is_staff=True`, `is_superuser=True`).

---

<p align="center">
  <b>AVTO</b> · Car Rental Platform · 2026 · Django + React
</p>
