from django.urls import path, include
from rest_framework import routers
from rest_framework_simplejwt.views import TokenRefreshView
from .views import *

router = routers.DefaultRouter()

router.register(r'feedback', FeedbackViewSet, basename='feedbacks')

urlpatterns = [
    path('', include(router.urls)),

    # Auth
    path('register/', RegisterView.as_view(), name='register'),
    path('login/', CustomLoginView.as_view(), name='login'),
    path('logout/', LogoutView.as_view(), name='logout'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),

    # Users
    path('users/', UserProfileListAPIView.as_view(), name='users_list'),
    path('users/<int:pk>/', UserProfileDetailAPIView.as_view(), name='users_detail'),

    # Verification
    path('verification/send/', SendVerificationCodeAPIView.as_view(), name='send_verification'),
    path('verification/confirm/', ConfirmVerificationCodeAPIView.as_view(), name='confirm_verification'),

    # Cars
    path('car/', CarListAPIView.as_view(), name='car_list'),
    path('car/my/', CarOwnerListAPIView.as_view(), name='car_owner_list'),
    path('car/available/', CarAvailableAPIView.as_view(), name='car_available'),
    path('car/<int:pk>/', CarDetailAPIView.as_view(), name='car_detail'),
    path('car/<int:car_id>/unavailable/', CarUnavailableDateAPIView.as_view(), name='car_unavailable_dates'),
    path('car/image/upload/', CarImageUploadAPIView.as_view(), name='car_image_upload'),

    # Favorites
    path('favorites/', FavoriteListAPIView.as_view(), name='favorites_list'),
    path('favorites/<int:pk>/', FavoriteDeleteAPIView.as_view(), name='favorites_delete'),

    # Rentals
    path('rental/', RentalListAPIView.as_view(), name='rental_list'),
    path('rental/<int:pk>/', RentalDetailAPIView.as_view(), name='rental_detail'),
    path('rental/<int:pk>/confirm/', RentalConfirmAPIView.as_view(), name='rental_confirm'),
    path('rental/<int:pk>/reject/', RentalRejectAPIView.as_view(), name='rental_reject'),

    # Chat
    path('chat/', ChatListAPIView.as_view(), name='chat_list'),
    path('chat/<int:pk>/', ChatDetailAPIView.as_view(), name='chat_detail'),
    path('chat/message/', ChatMessageCreateAPIView.as_view(), name='chat_message_create'),

    # Complaints
    path('complaints/', ComplaintListAPIView.as_view(), name='complaints_list'),
    path('complaints/<int:pk>/', ComplaintDetailAPIView.as_view(), name='complaints_detail'),

    # Stats
    path('stats/', StatsAPIView.as_view(), name='stats'),
    path('owner/stats/', OwnerStatsAPIView.as_view(), name='owner_stats'),
]
