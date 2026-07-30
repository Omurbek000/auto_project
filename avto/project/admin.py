# Административная панель Django (/admin/)
# Регистрируем модели, чтобы ими можно было управлять через веб-интерфейс

from django.contrib import admin
from django.db.models import Sum, Count, Avg
from django.utils import timezone
from datetime import timedelta
from .models import *


@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ('username', 'email', 'is_owner', 'is_renter', 'is_staff', 'phone_number', 'email_verified', 'is_verified')
    list_filter = ('is_owner', 'is_renter', 'is_staff', 'email_verified', 'is_verified')
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


# Дашборд для админа — страница /admin/dashboard/
# Показывает сводку по платформе: статистику, топ машин, доход
from django.template.response import TemplateResponse


def dashboard_view(request):
    today = timezone.now()
    month_ago = today - timedelta(days=30)

    total_users = User.objects.count()
    total_cars = Car.objects.count()
    total_rentals = Rental.objects.count()
    active_rentals = Rental.objects.filter(status='active').count()
    pending_rentals = Rental.objects.filter(status='pending').count()
    total_feedbacks = Feedback.objects.count()
    pending_complaints = Complaint.objects.filter(status='pending').count()

    monthly_revenue = Rental.objects.filter(
        status='completed',
        created_date__gte=month_ago
    ).aggregate(Sum('total_price'))['total_price__sum'] or 0

    popular_cars = Car.objects.annotate(
        rental_count=Count('rentals')
    ).order_by('-rental_count')[:5]

    context = {
        'title': 'Дашборд',
        'total_users': total_users,
        'total_cars': total_cars,
        'total_rentals': total_rentals,
        'active_rentals': active_rentals,
        'pending_rentals': pending_rentals,
        'total_feedbacks': total_feedbacks,
        'pending_complaints': pending_complaints,
        'monthly_revenue': monthly_revenue,
        'popular_cars': popular_cars,
        'is_nav_sidebar_enabled': True,
    }
    return TemplateResponse(request, 'admin/dashboard.html', context)


admin.site.index_title = 'Avto Admin'
