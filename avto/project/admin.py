from django.contrib import admin
from .models import *


@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ('username', 'email', 'role', 'phone_number', 'email_verified', 'phone_verified', 'is_verified')
    list_filter = ('role', 'email_verified', 'phone_verified', 'is_verified')
    search_fields = ('username', 'email', 'phone_number')


@admin.register(Car)
class CarAdmin(admin.ModelAdmin):
    list_display = ('brand', 'model_name', 'year', 'price_per_day', 'location', 'is_available', 'owner')
    list_filter = ('fuel_type', 'transmission', 'is_available')
    search_fields = ('brand', 'model_name', 'description', 'location')
    list_editable = ('is_available',)


@admin.register(CarImage)
class CarImageAdmin(admin.ModelAdmin):
    list_display = ('car', 'image', 'created_date')
    list_filter = ('created_date',)
    search_fields = ('car__brand', 'car__model_name')


@admin.register(CarUnavailableDate)
class CarUnavailableDateAdmin(admin.ModelAdmin):
    list_display = ('car', 'start_date', 'end_date', 'reason')
    list_filter = ('start_date', 'end_date')
    search_fields = ('car__brand', 'car__model_name', 'reason')


@admin.register(Rental)
class RentalAdmin(admin.ModelAdmin):
    list_display = ('car', 'renter', 'start_date', 'end_date', 'total_price', 'status')
    list_filter = ('status', 'start_date', 'end_date')
    search_fields = ('car__brand', 'car__model_name', 'renter__username')


@admin.register(Feedback)
class FeedbackAdmin(admin.ModelAdmin):
    list_display = ('rental', 'feedback_type', 'author', 'rating', 'created_date')
    list_filter = ('rating', 'feedback_type', 'created_date')
    search_fields = ('rental__car__brand', 'rental__car__model_name', 'comment', 'author__username')


@admin.register(Favorite)
class FavoriteAdmin(admin.ModelAdmin):
    list_display = ('user', 'car', 'created_date')
    list_filter = ('created_date',)
    search_fields = ('user__username', 'car__brand', 'car__model_name')


@admin.register(Chat)
class ChatAdmin(admin.ModelAdmin):
    list_display = ('rental', 'created_date')
    list_filter = ('created_date',)
    search_fields = ('rental__car__brand', 'rental__renter__username')


@admin.register(ChatMessage)
class ChatMessageAdmin(admin.ModelAdmin):
    list_display = ('chat', 'sender', 'message', 'is_read', 'created_date')
    list_filter = ('is_read', 'created_date')
    search_fields = ('sender__username', 'message')


@admin.register(Complaint)
class ComplaintAdmin(admin.ModelAdmin):
    list_display = ('author', 'target_user', 'reason', 'status', 'created_date')
    list_filter = ('status', 'created_date')
    search_fields = ('author__username', 'target_user__username', 'reason', 'description')


@admin.register(VerificationCode)
class VerificationCodeAdmin(admin.ModelAdmin):
    list_display = ('user', 'verification_type', 'code', 'is_used', 'expires_at', 'created_date')
    list_filter = ('verification_type', 'is_used', 'created_date')
    search_fields = ('user__username', 'code')
