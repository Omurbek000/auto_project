# View (представления) — обработчики HTTP-запросов
# Каждый класс — это один endpoint API (или несколько, если ViewSet)
# DRF-generic классы берут на себя 90% шаблонного кода

import random
from datetime import date, datetime, timedelta
from django.utils import timezone
from calendar import monthrange

from django.contrib.auth.models import AnonymousUser
from django.db.models import Sum, Count, Avg, Q
from django.db.models.functions import TruncMonth
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import viewsets, generics, permissions, status
from rest_framework.exceptions import ValidationError, PermissionDenied
from rest_framework.filters import SearchFilter
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken

from .filters import CarFilter, RentalFilter, FeedbackFilter
from .models import Car, CarImage, CarUnavailableDate, Rental, Feedback, VerificationCode, User, Complaint, Chat, ChatMessage, Favorite, AuditLog
from .pagination import CarPagination, RentalPagination, FeedbackPagination, ChatPagination, ComplaintPagination, AuditLogPagination
from .permissions import IsOwnerOrAdmin, IsOwnerOrReadOnly, IsRentalParticipant
from .serializers import (
    RegisterSerializer, CustomLoginSerializer, LogoutSerializer,
    UserSerializer, CarListSerializer, CarDetailSerializer,
    CarImageSerializer, CarImageBulkUploadSerializer,
    CarUnavailableDateSerializer, RentalListSerializer, RentalDetailSerializer,
    FeedbackSerializer, FavoriteSerializer, ChatSerializer, ChatMessageSerializer,
    ComplaintSerializer, VerificationCodeSerializer, VerificationConfirmSerializer,
    PasswordResetRequestSerializer, PasswordResetConfirmSerializer,
    AdminUserSerializer, AdminComplaintSerializer, AuditLogSerializer,
)
from .services import send_sms, send_email, log_action


# Вспомогательная функция: сколько дней сдавалась каждая машина (без учёта цены).
# Считает все неотменённые аренды из переданного queryset.
# Возвращает список словарей {car_id, car, rental_days, rentals_count},
# отсортированный от самой сдаваемой машины к менее сдаваемой.
def _rental_days_by_car(queryset):
    days_per_car = {}
    for rental in queryset.exclude(status='canceled'):
        days = (rental.end_date - rental.start_date).days + 1
        entry = days_per_car.setdefault(rental.car_id, {
            'car_id': rental.car_id,
            'car': f'{rental.car.brand} {rental.car.model_name} ({rental.car.year})',
            'rental_days': 0,
            'rentals_count': 0,
        })
        entry['rental_days'] += days
        entry['rentals_count'] += 1
    return sorted(days_per_car.values(), key=lambda x: x['rental_days'], reverse=True)


# Регистрация нового пользователя
# CreateAPIView — только POST (создание)
class RegisterView(generics.CreateAPIView):
    serializer_class = RegisterSerializer

    def create(self, request, *args, **kwargs):
        # Принимает данные, валидирует, создаёт пользователя, возвращает 201
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()

        # Фиксируем регистрацию в журнале аудита (кто зарегистрировался)
        log_action(user, 'user.registered', obj=user, details={'username': user.username})

        return Response(serializer.data, status=status.HTTP_201_CREATED)


# Логин. Принимает username + password, возвращает JWT-токены
class CustomLoginView(generics.GenericAPIView):
    serializer_class = CustomLoginSerializer

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


# Логаут. Добавляет refresh-токен в чёрный список (больше не действителен)
class LogoutView(generics.GenericAPIView):
    serializer_class = LogoutSerializer

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            refresh_token = serializer.validated_data["refresh"]
            token = RefreshToken(refresh_token)
            token.blacklist()
            return Response(status=status.HTTP_205_RESET_CONTENT)
        except Exception:
            return Response({'detail': 'Невалидный токен'}, status=status.HTTP_400_BAD_REQUEST)


# Профиль пользователя (GET — получить свои данные)
class UserProfileListAPIView(generics.ListAPIView):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return User.objects.filter(id=self.request.user.id)


# Профиль пользователя (GET/PUT/PATCH/DELETE — редактирование)
class UserProfileDetailAPIView(generics.RetrieveUpdateDestroyAPIView):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        # Только свой профиль
        return User.objects.filter(id=self.request.user.id)


# Список автомобилей (GET — все, POST — создать новый)
# Фильтрация: по марке, модели, цене, году и тд (через CarFilter)
# Поиск: по бренду, модели, описанию, локации (через SearchFilter)
class CarListAPIView(generics.ListCreateAPIView):
    queryset = Car.objects.all()
    serializer_class = CarListSerializer
    filter_backends = [DjangoFilterBackend, SearchFilter]
    filterset_class = CarFilter
    search_fields = ["brand", "model_name", "description", "location"]
    pagination_class = CarPagination
    permission_classes = [permissions.IsAuthenticatedOrReadOnly, IsOwnerOrAdmin]

    def perform_create(self, serializer):
        # Проверка: создавать машины могут только владельцы (is_owner)
        if not self.request.user.is_owner:
            raise permissions.PermissionDenied('Только владельцы могут создавать автомобили')
        serializer.save(owner=self.request.user)


# Детальная страница автомобиля (GET/PUT/PATCH/DELETE)
class CarDetailAPIView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Car.objects.all()
    serializer_class = CarDetailSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly, IsOwnerOrReadOnly]


# Список автомобилей текущего пользователя (GET — только свои)
class CarOwnerListAPIView(generics.ListAPIView):
    serializer_class = CarListSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Car.objects.filter(owner=self.request.user)


# Загрузка фото к автомобилю (POST — добавить фото)
class CarImageUploadAPIView(generics.CreateAPIView):
    queryset = CarImage.objects.all()
    serializer_class = CarImageSerializer
    permission_classes = [permissions.IsAuthenticated]

    def perform_create(self, serializer):
        car_id = self.request.data.get('car_id')
        try:
            car = Car.objects.get(id=car_id, owner=self.request.user)
            serializer.save(car=car)
        except Car.DoesNotExist:
            raise ValidationError({'detail': 'Автомобиль не найден или вы не владелец'})


# Массовая загрузка нескольких фото к автомобилю (POST)
class CarImageBulkUploadAPIView(generics.CreateAPIView):
    serializer_class = CarImageBulkUploadSerializer
    permission_classes = [permissions.IsAuthenticated]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        images = serializer.save()
        result_serializer = CarImageSerializer(images, many=True)
        return Response(result_serializer.data, status=status.HTTP_201_CREATED)


# Управление заблокированными датами (владелец вручную блокирует дни)
class CarUnavailableDateAPIView(generics.ListCreateAPIView):
    serializer_class = CarUnavailableDateSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        # Только для своего автомобиля
        car_id = self.kwargs.get('car_id')
        return CarUnavailableDate.objects.filter(car_id=car_id, car__owner=self.request.user)

    def perform_create(self, serializer):
        car_id = self.kwargs.get('car_id')
        try:
            car = Car.objects.get(id=car_id, owner=self.request.user)
            serializer.save(car=car)
        except Car.DoesNotExist:
            raise ValidationError({'detail': 'Автомобиль не найден или вы не владелец'})


# Аренда. GET — список аренд (своих или по своим машинам), POST — создать запрос
class RentalListAPIView(generics.ListCreateAPIView):
    queryset = Rental.objects.all()
    serializer_class = RentalListSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_class = RentalFilter
    pagination_class = RentalPagination
    permission_classes = [permissions.IsAuthenticated, IsRentalParticipant]

    def get_queryset(self):
        # Админ видит всё
        # Владелец видит аренды своих машин
        # Арендатор видит свои аренды
        # Если юзер и owner и renter — видит и те и те
        if isinstance(self.request.user, AnonymousUser):
            return Rental.objects.none()

        if self.request.user.is_staff:
            return Rental.objects.all()

        as_owner = Rental.objects.filter(car__owner=self.request.user)
        as_renter = Rental.objects.filter(renter=self.request.user)
        return (as_owner | as_renter).distinct()

    def perform_create(self, serializer):
        serializer.save(renter=self.request.user)


# Детальная страница аренды
class RentalDetailAPIView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Rental.objects.all()
    serializer_class = RentalDetailSerializer
    permission_classes = [permissions.IsAuthenticated, IsRentalParticipant]


# Подтверждение аренды владельцем (pending → confirmed)
class RentalConfirmAPIView(generics.GenericAPIView):
    queryset = Rental.objects.all()
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, pk):
        try:
            rental = Rental.objects.get(pk=pk)
        except Rental.DoesNotExist:
            return Response({'detail': 'Аренда не найдена'}, status=status.HTTP_404_NOT_FOUND)

        if rental.car.owner != request.user:
            return Response({'detail': 'Только владелец может подтверждать аренду'}, status=status.HTTP_403_FORBIDDEN)

        if rental.status != 'pending':
            return Response({'detail': 'Можно подтверждать только заявки со статусом pending'}, status=status.HTTP_400_BAD_REQUEST)

        rental.status = 'confirmed'
        rental.save()
        serializer = RentalDetailSerializer(rental)
        return Response(serializer.data, status=status.HTTP_200_OK)


# Отклонение аренды владельцем (pending → canceled)
class RentalRejectAPIView(generics.GenericAPIView):
    queryset = Rental.objects.all()
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, pk):
        try:
            rental = Rental.objects.get(pk=pk)
        except Rental.DoesNotExist:
            return Response({'detail': 'Аренда не найдена'}, status=status.HTTP_404_NOT_FOUND)

        if rental.car.owner != request.user:
            return Response({'detail': 'Только владелец может отклонять аренду'}, status=status.HTTP_403_FORBIDDEN)

        if rental.status != 'pending':
            return Response({'detail': 'Можно отклонять только заявки со статусом pending'}, status=status.HTTP_400_BAD_REQUEST)

        rental.status = 'canceled'
        rental.save()
        serializer = RentalDetailSerializer(rental)
        return Response(serializer.data, status=status.HTTP_200_OK)


# Завершение аренды арендатором (active → completed)
class RentalCompleteAPIView(generics.GenericAPIView):
    queryset = Rental.objects.all()
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, pk):
        try:
            rental = Rental.objects.get(pk=pk)
        except Rental.DoesNotExist:
            return Response({'detail': 'Аренда не найдена'}, status=status.HTTP_404_NOT_FOUND)

        if rental.renter != request.user:
            return Response({'detail': 'Только арендатор может завершить аренду'}, status=status.HTTP_403_FORBIDDEN)

        if rental.status != 'active':
            return Response({'detail': 'Можно завершить только активную аренду'}, status=status.HTTP_400_BAD_REQUEST)

        rental.status = 'completed'
        rental.save()
        serializer = RentalDetailSerializer(rental)
        return Response(serializer.data, status=status.HTTP_200_OK)


# Отзывы. ViewSet — сразу GET, POST, PUT, PATCH, DELETE
class FeedbackViewSet(viewsets.ModelViewSet):
    queryset = Feedback.objects.all()
    serializer_class = FeedbackSerializer
    pagination_class = FeedbackPagination
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_class = FeedbackFilter

    def get_queryset(self):
        # Админ видит все отзывы
        # Обычный пользователь — только те, где он участник (владелец или арендатор)
        if isinstance(self.request.user, AnonymousUser):
            return Feedback.objects.none()

        if self.request.user.is_staff:
            return Feedback.objects.all()

        return Feedback.objects.filter(rental__car__owner=self.request.user) | Feedback.objects.filter(rental__renter=self.request.user)

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)

    def perform_update(self, serializer):
        # Редактировать отзыв может только его автор или админ
        # (participant может видеть чужой отзыв, но менять — нет)
        instance = self.get_object()
        if instance.author != self.request.user and not self.request.user.is_staff:
            raise PermissionDenied('Только автор отзыва или администратор может редактировать его')
        serializer.save()

    def perform_destroy(self, instance):
        # Удалять отзыв может только его автор или админ
        # Раньше любой участник аренды мог удалить чужой отзыв — это дыра в правах
        if instance.author != self.request.user and not self.request.user.is_staff:
            raise PermissionDenied('Только автор отзыва или администратор может удалить его')
        instance.delete()


# Удаление фото автомобиля (DELETE — только владелец машины)
class CarImageDeleteAPIView(generics.DestroyAPIView):
    queryset = CarImage.objects.all()
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        # Только фото своих машин
        return CarImage.objects.filter(car__owner=self.request.user)


# Доступные автомобили на конкретные даты (GET)
# Учитывает уже забронированные и заблокированные даты
class CarAvailableAPIView(generics.ListAPIView):
    queryset = Car.objects.filter(is_available=True)
    serializer_class = CarListSerializer
    filter_backends = [DjangoFilterBackend, SearchFilter]
    filterset_class = CarFilter
    search_fields = ['brand', 'model_name', 'description', 'location']
    pagination_class = CarPagination

    def get_queryset(self):
        queryset = Car.objects.filter(is_available=True)
        start_date = self.request.query_params.get('start_date')
        end_date = self.request.query_params.get('end_date')

        if start_date and end_date:
            try:
                start = datetime.strptime(start_date, '%Y-%m-%d').date()
                end = datetime.strptime(end_date, '%Y-%m-%d').date()

                # Исключаем машины, которые забронированы на эти даты
                unavailable_car_ids = Rental.objects.filter(
                    status__in=['pending', 'confirmed', 'active']
                ).exclude(end_date__lt=start).exclude(start_date__gt=end
                ).values_list('car_id', flat=True)

                queryset = queryset.exclude(id__in=unavailable_car_ids)
            except ValueError:
                pass

        return queryset


# Глобальная статистика платформы (GET — доступна всем)
class StatsAPIView(generics.GenericAPIView):
    def get(self, request, *args, **kwargs):
        return Response({
            'cars_total': Car.objects.count(),
            'cars_available': Car.objects.filter(is_available=True).count(),
            'rentals_active': Rental.objects.filter(status='active').count(),
            'rentals_total': Rental.objects.count(),
            'feedbacks_total': Feedback.objects.count(),
            'users_total': User.objects.count(),
        })


# Статистика владельца (GET — только для is_owner)
class OwnerStatsAPIView(generics.GenericAPIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, *args, **kwargs):
        if not request.user.is_owner:
            return Response({'detail': 'Только для владельцев'}, status=status.HTTP_403_FORBIDDEN)

        cars = Car.objects.filter(owner=request.user)
        rentals = Rental.objects.filter(car__owner=request.user)
        completed_rentals = rentals.filter(status='completed')

        total_earnings = completed_rentals.aggregate(Sum('total_price'))['total_price__sum'] or 0
        total_rentals = rentals.count()
        cars_count = cars.count()

        feedbacks = Feedback.objects.filter(rental__car__owner=request.user, feedback_type='car')
        average_rating = feedbacks.aggregate(Avg('rating'))['rating__avg']

        popular_car = cars.annotate(
            rental_count=Count('rentals')
        ).order_by('-rental_count').first()

        today = datetime.today()
        first_day = today.replace(day=1)
        monthly_revenue = completed_rentals.filter(
            created_date__gte=first_day
        ).aggregate(Sum('total_price'))['total_price__sum'] or 0

        return Response({
            'total_earnings': total_earnings,           # Общий доход
            'total_rentals': total_rentals,             # Всего аренд
            'cars_count': cars_count,                   # Количество машин
            'average_rating': round(average_rating, 2) if average_rating else None,  # Средний рейтинг
            'popular_car': {                            # Самая популярная машина
                'id': popular_car.id,
                'brand': popular_car.brand,
                'model_name': popular_car.model_name,
                'rental_count': popular_car.rental_count
            } if popular_car else None,
            'monthly_revenue': monthly_revenue,         # Доход за текущий месяц
        })


# Журнал операций текущего пользователя (GET)
# Собирает в одну timeline все события: аренды, отзывы, жалобы.
# Нужен для «журнала операций» в личном кабинете.
class UserOperationsAPIView(generics.GenericAPIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, *args, **kwargs):
        user = request.user
        operations = []

        # Аренды, где пользователь — арендатор или владелец машины
        for rental in Rental.objects.filter(Q(renter=user) | Q(car__owner=user)):
            operations.append({
                'id': rental.id,
                'type': 'rental',
                'status': rental.status,
                'amount': str(rental.total_price),
                'car': f'{rental.car.brand} {rental.car.model_name}',
                'date': rental.created_date.isoformat(),
            })

        # Отзывы, написанные пользователем
        for feedback in Feedback.objects.filter(author=user):
            operations.append({
                'id': feedback.id,
                'type': 'feedback',
                'status': 'completed',
                'rating': feedback.rating,
                'comment': feedback.comment,
                'date': feedback.created_date.isoformat(),
            })

        # Жалобы, поданные пользователем
        for complaint in Complaint.objects.filter(author=user):
            operations.append({
                'id': complaint.id,
                'type': 'complaint',
                'status': complaint.status,
                'reason': complaint.reason,
                'date': complaint.created_date.isoformat(),
            })

        # Сортируем от новых к старым и ограничиваем (защита от огромного ответа)
        operations.sort(key=lambda x: x['date'], reverse=True)
        return Response(operations[:200])


# Аналитика для личного кабинета пользователя (GET)
# - renters: распределение своих аренд по статусам
# - owners: дополнительно доход по месяцам и машины по брендам
class AnalyticsAPIView(generics.GenericAPIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, *args, **kwargs):
        user = request.user
        rentals = Rental.objects.filter(Q(renter=user) | Q(car__owner=user))

        response_data = {
            # Сколько аренд в каждом статусе (pending/confirmed/active/...)
            'rentals_by_status': list(
                rentals.values('status').annotate(count=Count('id')).order_by('status')
            ),
            'feedbacks_written': Feedback.objects.filter(author=user).count(),
            'rentals_total': rentals.count(),
        }

        # Для владельцев — данные дашборда
        if user.is_owner:
            completed = rentals.filter(status='completed')

            monthly = completed.annotate(
                month=TruncMonth('created_date')
            ).values('month').annotate(
                revenue=Sum('total_price'),
                count=Count('id'),
            ).order_by('month')

            response_data['revenue_by_month'] = [
                {
                    'month': m['month'].strftime('%Y-%m') if m['month'] else None,
                    'revenue': float(m['revenue'] or 0),
                    'count': m['count'],
                } for m in monthly
            ]
            response_data['revenue_total'] = float(
                completed.aggregate(Sum('total_price'))['total_price__sum'] or 0
            )
            response_data['cars_by_brand'] = list(
                user.cars.values('brand').annotate(count=Count('id')).order_by('-count')
            )

            # Сколько дней сдавалась каждая машина (без учёта цены).
            # Считаем аренды ТОЛЬКО машин владельца; отменённые (canceled) не в счёт.
            response_data['cars_rental_days'] = _rental_days_by_car(
                Rental.objects.filter(car__owner=user)
            )

        return Response(response_data)


# Список всех пользователей (GET — только staff, поиск + фильтры)
# Для дашборда админа во фронтенде.
class AdminUserListAPIView(generics.ListAPIView):
    serializer_class = AdminUserSerializer
    permission_classes = [permissions.IsAdminUser]
    filter_backends = [DjangoFilterBackend, SearchFilter]
    filterset_fields = ['is_owner', 'is_renter', 'is_active', 'is_verified', 'is_staff']
    search_fields = ['username', 'email', 'phone_number']

    def get_queryset(self):
        return User.objects.all().order_by('-created_date')


# Детальная страница пользователя (GET/PATCH — только staff)
# Через PATCH админ может: заблокировать (is_active=False), верифицировать
# (is_verified=True), назначить роли (is_owner/is_renter).
class AdminUserDetailAPIView(generics.RetrieveUpdateAPIView):
    serializer_class = AdminUserSerializer
    permission_classes = [permissions.IsAdminUser]

    def get_queryset(self):
        return User.objects.all()

    def perform_update(self, serializer):
        # Защита: суперпользователя может менять только другой суперпользователь
        user = self.get_object()
        if user.is_superuser and not self.request.user.is_superuser:
            raise PermissionDenied('Нельзя изменять суперпользователя')

        # Запоминаем состояние ДО изменения, чтобы понять, что именно поменялось
        old = {
            'is_active': user.is_active,
            'is_verified': user.is_verified,
            'is_owner': user.is_owner,
            'is_renter': user.is_renter,
        }

        serializer.save()
        user.refresh_from_db()

        # Записываем в аудит только реально изменившиеся поля
        if old['is_active'] and not user.is_active:
            log_action(self.request.user, 'user.blocked', obj=user,
                       details={'label': 'Пользователь заблокирован', 'username': user.username})
        elif not old['is_active'] and user.is_active:
            log_action(self.request.user, 'user.unblocked', obj=user,
                       details={'label': 'Пользователь разблокирован', 'username': user.username})

        if not old['is_verified'] and user.is_verified:
            log_action(self.request.user, 'user.verified', obj=user,
                       details={'label': 'Личность подтверждена', 'username': user.username})

        if not old['is_owner'] and user.is_owner:
            log_action(self.request.user, 'user.role_owner', obj=user,
                       details={'label': 'Выдана роль владельца', 'username': user.username})
        elif old['is_owner'] and not user.is_owner:
            log_action(self.request.user, 'user.role_owner_removed', obj=user,
                       details={'label': 'Роль владельца снята', 'username': user.username})

        if not old['is_renter'] and user.is_renter:
            log_action(self.request.user, 'user.role_renter', obj=user,
                       details={'label': 'Выдана роль арендатора', 'username': user.username})
        elif old['is_renter'] and not user.is_renter:
            log_action(self.request.user, 'user.role_renter_removed', obj=user,
                       details={'label': 'Роль арендатора снята', 'username': user.username})


# Журнал аудита действий (GET — только staff)
# Для дашборда админа: кто, что и когда делал (блокировки, роли, жалобы...).
class AdminAuditLogAPIView(generics.ListAPIView):
    serializer_class = AuditLogSerializer
    permission_classes = [permissions.IsAdminUser]
    pagination_class = AuditLogPagination
    filter_backends = [DjangoFilterBackend, SearchFilter]
    filterset_fields = ['action', 'user', 'model_name']
    search_fields = ['action', 'model_name', 'user__username']

    def get_queryset(self):
        return AuditLog.objects.all()


# Аналитика всей платформы (GET — только staff)
# Для дашборда админа: KPI + активность платформы.
# ВАЖНО: НЕ содержит никаких финансовых данных (суммы, доход пользователей) —
# это маркетплейс, доходы каждого владельца анонимны. См. /analytics/ для
# персональной статистики.
class AdminAnalyticsAPIView(generics.GenericAPIView):
    permission_classes = [permissions.IsAdminUser]

    def get(self, request, *args, **kwargs):
        # Активность по месяцам (число аренд, БЕЗ сумм)
        monthly = Rental.objects.annotate(
            month=TruncMonth('created_date')
        ).values('month').annotate(
            count=Count('id'),
        ).order_by('month')

        # Топ машин по числу дней аренды на всей платформе (без учёта цены)
        all_cars_days = _rental_days_by_car(Rental.objects.all())

        return Response({
            # KPI-карточки
            'users_total': User.objects.count(),
            'cars_total': Car.objects.count(),
            'rentals_total': Rental.objects.count(),
            'active_rentals': Rental.objects.filter(status='active').count(),
            'pending_rentals': Rental.objects.filter(status='pending').count(),
            'feedbacks_total': Feedback.objects.count(),
            'pending_complaints': Complaint.objects.filter(status='pending').count(),
            # Графики (только активность, без денег)
            'rentals_by_month': [
                {
                    'month': m['month'].strftime('%Y-%m') if m['month'] else None,
                    'count': m['count'],
                } for m in monthly
            ],
            'cars_by_brand': list(
                Car.objects.values('brand').annotate(count=Count('id')).order_by('-count')
            ),
            'rental_statuses': list(
                Rental.objects.values('status').annotate(count=Count('id')).order_by('status')
            ),
            # Сдаваемость машин (без учёта цены)
            'top_cars_by_days': all_cars_days[:5],
            'rental_days_total': sum(e['rental_days'] for e in all_cars_days),
        })


# Журнал всех операций платформы (GET — только staff)
# В отличие от UserOperationsAPIView включает данные о пользователях.
# ВАЖНО: НЕ содержит сумм (amount) — финансы пользователей анонимны.
class AdminOperationsAPIView(generics.GenericAPIView):
    permission_classes = [permissions.IsAdminUser]

    def get(self, request, *args, **kwargs):
        operations = []

        for rental in Rental.objects.all():
            operations.append({
                'id': rental.id,
                'type': 'rental',
                'status': rental.status,
                'car': f'{rental.car.brand} {rental.car.model_name}',
                'renter': rental.renter.username,
                'owner': rental.car.owner.username,
                'date': rental.created_date.isoformat(),
            })

        for feedback in Feedback.objects.all():
            operations.append({
                'id': feedback.id,
                'type': 'feedback',
                'status': 'completed',
                'rating': feedback.rating,
                'comment': feedback.comment,
                'author': feedback.author.username,
                'date': feedback.created_date.isoformat(),
            })

        for complaint in Complaint.objects.all():
            operations.append({
                'id': complaint.id,
                'type': 'complaint',
                'status': complaint.status,
                'reason': complaint.reason,
                'author': complaint.author.username,
                'target_user': complaint.target_user.username,
                'date': complaint.created_date.isoformat(),
            })

        operations.sort(key=lambda x: x['date'], reverse=True)
        return Response(operations[:200])


# Избранное (GET — список, POST — добавить)
class FavoriteListAPIView(generics.ListCreateAPIView):
    serializer_class = FavoriteSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Favorite.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        car = serializer.validated_data['car']
        if Favorite.objects.filter(user=self.request.user, car=car).exists():
            raise ValidationError({'detail': 'Автомобиль уже в избранном'})
        serializer.save(user=self.request.user)


# Удаление из избранного (DELETE)
class FavoriteDeleteAPIView(generics.DestroyAPIView):
    serializer_class = FavoriteSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        # Только своё избранное
        return Favorite.objects.filter(user=self.request.user)


# Список чатов (GET — только свои чаты)
class ChatListAPIView(generics.ListAPIView):
    serializer_class = ChatSerializer
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = ChatPagination

    def get_queryset(self):
        # Показываем чаты, где пользователь — участник (арендатор или владелец)
        return Chat.objects.filter(
            rental__renter=self.request.user
        ) | Chat.objects.filter(
            rental__car__owner=self.request.user
        )


# Детальная страница чата (GET — с сообщениями)
class ChatDetailAPIView(generics.RetrieveAPIView):
    serializer_class = ChatSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Chat.objects.filter(
            rental__renter=self.request.user
        ) | Chat.objects.filter(
            rental__car__owner=self.request.user
        )


# Отправка сообщения в чат (POST)
class ChatMessageCreateAPIView(generics.CreateAPIView):
    serializer_class = ChatMessageSerializer
    permission_classes = [permissions.IsAuthenticated]

    def perform_create(self, serializer):
        chat_id = self.request.data.get('chat_id')
        try:
            chat = Chat.objects.get(id=chat_id)
            if chat.rental.renter != self.request.user and chat.rental.car.owner != self.request.user:
                raise PermissionDenied('Вы не участник этого чата')
            serializer.save(chat=chat, sender=self.request.user)
        except Chat.DoesNotExist:
            raise ValidationError({'detail': 'Чат не найден'})


# Список жалоб (GET — свои, POST — создать)
class ComplaintListAPIView(generics.ListCreateAPIView):
    serializer_class = ComplaintSerializer
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = ComplaintPagination

    def get_queryset(self):
        # Админ видит все жалобы, пользователь — только свои
        if self.request.user.is_staff:
            return Complaint.objects.all()
        return Complaint.objects.filter(author=self.request.user)

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)


# Детальная страница жалобы (GET/PUT/PATCH)
class ComplaintDetailAPIView(generics.RetrieveUpdateAPIView):
    serializer_class = ComplaintSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_serializer_class(self):
        # Для админа status и admin_response доступны на запись
        # (у обычного пользователя они read_only)
        if self.request.user.is_staff:
            return AdminComplaintSerializer
        return ComplaintSerializer

    def get_queryset(self):
        if self.request.user.is_staff:
            return Complaint.objects.all()
        return Complaint.objects.filter(author=self.request.user)

    def perform_update(self, serializer):
        complaint = self.get_object()
        old_status = complaint.status
        old_response = complaint.admin_response

        serializer.save()
        complaint.refresh_from_db()

        # Записываем в аудит смену статуса жалобы
        if complaint.status != old_status:
            log_action(self.request.user, 'complaint.status_changed', obj=complaint,
                       details={
                           'label': 'Статус жалобы изменён',
                           'from': old_status,
                           'to': complaint.status,
                           'reason': complaint.reason,
                       })

        # Записываем в аудит ответ администратора
        if complaint.admin_response != old_response and complaint.admin_response:
            log_action(self.request.user, 'complaint.response', obj=complaint,
                       details={'label': 'Ответ администратора', 'response': complaint.admin_response})


# Отправка кода верификации на email/телефон (POST)
class SendVerificationCodeAPIView(generics.GenericAPIView):
    serializer_class = VerificationCodeSerializer
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        verification_type = serializer.validated_data['verification_type']

        code = str(random.randint(100000, 999999))
        expires_at = timezone.now() + timedelta(minutes=10)

        VerificationCode.objects.create(
            user=request.user,
            code=code,
            verification_type=verification_type,
            expires_at=expires_at
        )

        if verification_type == 'email':
            send_email(
                subject='Код подтверждения',
                message=f'Ваш код подтверждения: {code}',
                recipient_list=[request.user.email],
            )
        else:
            send_sms(request.user.phone_number, f'Ваш код подтверждения: {code}')

        return Response({
            'message': f'Код верификации отправлен на {verification_type}'
        }, status=status.HTTP_200_OK)


# Подтверждение кода верификации (POST)
class ConfirmVerificationCodeAPIView(generics.GenericAPIView):
    serializer_class = VerificationConfirmSerializer
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        verification_type = serializer.validated_data['verification_type']
        code = serializer.validated_data['code']

        try:
            verification = VerificationCode.objects.get(
                user=request.user,
                code=code,
                verification_type=verification_type,
                is_used=False,
                expires_at__gte=timezone.now()
            )

            verification.is_used = True
            verification.save()

            if verification_type == 'email':
                request.user.email_verified = True
            else:
                request.user.phone_verified = True

            request.user.save()

            return Response({
                'message': f'{verification_type} успешно верифицирован'
            }, status=status.HTTP_200_OK)

        except VerificationCode.DoesNotExist:
            return Response({
                'detail': 'Неверный или истекший код'
            }, status=status.HTTP_400_BAD_REQUEST)


# Запрос сброса пароля (POST — отправляет код на email)
class PasswordResetRequestAPIView(generics.GenericAPIView):
    serializer_class = PasswordResetRequestSerializer
    permission_classes = [permissions.AllowAny]

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        email = serializer.validated_data['email']
        user = User.objects.get(email=email)

        code = str(random.randint(100000, 999999))
        expires_at = timezone.now() + timedelta(minutes=10)

        VerificationCode.objects.create(
            user=user,
            code=code,
            verification_type='password_reset',
            expires_at=expires_at
        )

        send_email(
            subject='Сброс пароля',
            message=f'Ваш код для сброса пароля: {code}',
            recipient_list=[email],
        )
        send_sms(user.phone_number, f'Код сброса пароля: {code}')

        return Response({
            'message': 'Код сброса отправлен на вашу почту'
        }, status=status.HTTP_200_OK)


# Подтверждение сброса пароля (POST — код + новый пароль)
class PasswordResetConfirmAPIView(generics.GenericAPIView):
    serializer_class = PasswordResetConfirmSerializer
    permission_classes = [permissions.AllowAny]

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        email = serializer.validated_data['email']
        code = serializer.validated_data['code']
        new_password = serializer.validated_data['new_password']

        try:
            user = User.objects.get(email=email)

            verification = VerificationCode.objects.get(
                user=user,
                code=code,
                verification_type='password_reset',
                is_used=False,
                expires_at__gte=timezone.now()
            )

            verification.is_used = True
            verification.save()

            user.set_password(new_password)
            user.save()

            return Response({
                'message': 'Пароль успешно изменён'
            }, status=status.HTTP_200_OK)

        except (User.DoesNotExist, VerificationCode.DoesNotExist):
            return Response({
                'detail': 'Неверный или истекший код'
            }, status=status.HTTP_400_BAD_REQUEST)


# Календарь доступности автомобиля (GET — по году и месяцу)
# Возвращает статус каждого дня: free, booked, blocked, past
class CarCalendarAPIView(generics.GenericAPIView):
    permission_classes = [permissions.AllowAny]

    def get(self, request, pk):
        try:
            car = Car.objects.get(pk=pk)
        except Car.DoesNotExist:
            return Response({'detail': 'Автомобиль не найден'}, status=status.HTTP_404_NOT_FOUND)

        year = request.query_params.get('year')
        month = request.query_params.get('month')

        try:
            year = int(year) if year else timezone.now().year
            month = int(month) if month else timezone.now().month
        except ValueError:
            return Response({'detail': 'Неверный формат года или месяца'}, status=status.HTTP_400_BAD_REQUEST)

        # Генерируем все дни месяца
        _, days_in_month = monthrange(year, month)
        month_dates = [datetime(year, month, day).date() for day in range(1, days_in_month + 1)]

        # Собираем даты, занятые другими арендами
        booked_rentals = Rental.objects.filter(
            car=car,
            status__in=['pending', 'confirmed', 'active']
        ).exclude(end_date__lt=month_dates[0]).exclude(start_date__gt=month_dates[-1])

        booked_dates = set()
        for rental in booked_rentals:
            current = max(rental.start_date, month_dates[0])
            end = min(rental.end_date, month_dates[-1])
            while current <= end:
                booked_dates.add(current)
                current += timedelta(days=1)

        # Собираем даты, заблокированные владельцем
        blocked = CarUnavailableDate.objects.filter(car=car).exclude(
            end_date__lt=month_dates[0]
        ).exclude(start_date__gt=month_dates[-1])

        blocked_dates = set()
        for item in blocked:
            current = max(item.start_date, month_dates[0])
            end = min(item.end_date, month_dates[-1])
            while current <= end:
                blocked_dates.add(current)
                current += timedelta(days=1)

        # Формируем ответ для каждого дня месяца
        calendar_data = []
        for date in month_dates:
            status_str = 'free'
            if date in booked_dates:
                status_str = 'booked'
            elif date in blocked_dates:
                status_str = 'blocked'
            elif date < timezone.now().date():
                status_str = 'past'

            calendar_data.append({
                'date': date.isoformat(),
                'status': status_str,
            })

        return Response({
            'car_id': car.id,
            'year': year,
            'month': month,
            'days': calendar_data,
        })
