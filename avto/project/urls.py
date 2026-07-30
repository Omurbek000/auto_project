# Маршруты API. Каждый path связывает URL с View-классом
# Все эндпоинты доступны после /, например /register/, /car/ и тд

from django.urls import path, include
from rest_framework import routers
from rest_framework_simplejwt.views import TokenRefreshView
from .views import *

# Router для ViewSet (один класс — несколько эндпоинтов)
router = routers.DefaultRouter()
router.register(r'feedback', FeedbackViewSet, basename='feedbacks')

urlpatterns = [
    path('', include(router.urls)),

    # Авторизация
    path('register/', RegisterView.as_view(), name='register'),
    path('login/', CustomLoginView.as_view(), name='login'),
    path('logout/', LogoutView.as_view(), name='logout'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),

    # Пользователи
    path('users/', UserProfileListAPIView.as_view(), name='users_list'),
    path('users/<int:pk>/', UserProfileDetailAPIView.as_view(), name='users_detail'),

    # Верификация email/телефона
    path('verification/send/', SendVerificationCodeAPIView.as_view(), name='send_verification'),
    path('verification/confirm/', ConfirmVerificationCodeAPIView.as_view(), name='confirm_verification'),

    # Автомобили
    path('car/', CarListAPIView.as_view(), name='car_list'),
    path('car/my/', CarOwnerListAPIView.as_view(), name='car_owner_list'),
    path('car/available/', CarAvailableAPIView.as_view(), name='car_available'),
    path('car/<int:pk>/', CarDetailAPIView.as_view(), name='car_detail'),
    path('car/<int:car_id>/unavailable/', CarUnavailableDateAPIView.as_view(), name='car_unavailable_dates'),
    path('car/image/upload/', CarImageUploadAPIView.as_view(), name='car_image_upload'),
    path('car/image/<int:pk>/', CarImageDeleteAPIView.as_view(), name='car_image_delete'),

    # Календарь доступности
    path('car/<int:pk>/calendar/', CarCalendarAPIView.as_view(), name='car_calendar'),

    # Избранное
    path('favorites/', FavoriteListAPIView.as_view(), name='favorites_list'),
    path('favorites/<int:pk>/', FavoriteDeleteAPIView.as_view(), name='favorites_delete'),

    # Аренда
    path('rental/', RentalListAPIView.as_view(), name='rental_list'),
    path('rental/<int:pk>/', RentalDetailAPIView.as_view(), name='rental_detail'),
    path('rental/<int:pk>/confirm/', RentalConfirmAPIView.as_view(), name='rental_confirm'),
    path('rental/<int:pk>/reject/', RentalRejectAPIView.as_view(), name='rental_reject'),
    path('rental/<int:pk>/complete/', RentalCompleteAPIView.as_view(), name='rental_complete'),

    # Чат
    path('chat/', ChatListAPIView.as_view(), name='chat_list'),
    path('chat/<int:pk>/', ChatDetailAPIView.as_view(), name='chat_detail'),
    path('chat/message/', ChatMessageCreateAPIView.as_view(), name='chat_message_create'),

    # Жалобы
    path('complaints/', ComplaintListAPIView.as_view(), name='complaints_list'),
    path('complaints/<int:pk>/', ComplaintDetailAPIView.as_view(), name='complaints_detail'),

    # Сброс пароля
    path('password/reset/', PasswordResetRequestAPIView.as_view(), name='password_reset'),
    path('password/reset/confirm/', PasswordResetConfirmAPIView.as_view(), name='password_reset_confirm'),

    # Статистика
    path('stats/', StatsAPIView.as_view(), name='stats'),
    path('owner/stats/', OwnerStatsAPIView.as_view(), name='owner_stats'),
]
