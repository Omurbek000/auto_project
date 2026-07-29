from rest_framework import viewsets, generics, permissions, status
from .serializers import *
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter
from .filters import CarFilter, RentalFilter
from .pagination import CarPagination, RentalPagination, FeedbackPagination
from .permissions import IsOwnerOrAdmin, IsRenterOrAdmin, IsOwnerOrReadOnly, IsRentalParticipant
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth.models import AnonymousUser



class RegisterView(generics.CreateAPIView):
    serializer_class = RegisterSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class CustomLoginView(generics.GenericAPIView):
    serializer_class = CustomLoginSerializer

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


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


class UserProfileListAPIView(generics.ListAPIView):
    queryset = User.objects.all()
    serializer_class = UserSerializer

    def get_queryset(self):
        return User.objects.filter(id=self.request.user.id)


class UserProfileDetailAPIView(generics.RetrieveUpdateDestroyAPIView):
    queryset = User.objects.all()
    serializer_class = UserSerializer

    def get_queryset(self):
        return User.objects.filter(id=self.request.user.id)


class CarListAPIView(generics.ListCreateAPIView):
    queryset = Car.objects.all()
    serializer_class = CarListSerializer
    filter_backends = [DjangoFilterBackend, SearchFilter]
    filterset_class = CarFilter
    search_fields = ["brand", "model_name", "description", "location"]
    pagination_class = CarPagination
    permission_classes = [permissions.IsAuthenticatedOrReadOnly, IsOwnerOrAdmin]

    def perform_create(self, serializer):
        if self.request.user.role != 'owner':
            raise permissions.PermissionDenied('Только владельцы могут создавать автомобили')
        serializer.save(owner=self.request.user)


class CarDetailAPIView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Car.objects.all()
    serializer_class = CarDetailSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly, IsOwnerOrReadOnly]


class CarOwnerListAPIView(generics.ListAPIView):
    serializer_class = CarListSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Car.objects.filter(owner=self.request.user)


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
            from rest_framework.exceptions import ValidationError
            raise ValidationError({'detail': 'Автомобиль не найден или вы не владелец'})


class CarUnavailableDateAPIView(generics.ListCreateAPIView):
    serializer_class = CarUnavailableDateSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        car_id = self.kwargs.get('car_id')
        return CarUnavailableDate.objects.filter(car_id=car_id, car__owner=self.request.user)

    def perform_create(self, serializer):
        car_id = self.kwargs.get('car_id')
        try:
            car = Car.objects.get(id=car_id, owner=self.request.user)
            serializer.save(car=car)
        except Car.DoesNotExist:
            from rest_framework.exceptions import ValidationError
            raise ValidationError({'detail': 'Автомобиль не найден или вы не владелец'})


class RentalListAPIView(generics.ListCreateAPIView):
    queryset = Rental.objects.all()
    serializer_class = RentalListSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_class = RentalFilter
    pagination_class = RentalPagination
    permission_classes = [permissions.IsAuthenticated, IsRentalParticipant]

    def get_queryset(self):
        if isinstance(self.request.user, AnonymousUser):
            return Rental.objects.none()

        if self.request.user.role == "admin":
            return Rental.objects.all()

        if self.request.user.role == "owner":
            return Rental.objects.filter(car__owner=self.request.user)

        return Rental.objects.filter(renter=self.request.user)


class RentalDetailAPIView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Rental.objects.all()
    serializer_class = RentalDetailSerializer
    permission_classes = [permissions.IsAuthenticated, IsRentalParticipant]


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


class FeedbackViewSet(viewsets.ModelViewSet):
    queryset = Feedback.objects.all()
    serializer_class = FeedbackSerializer
    pagination_class = FeedbackPagination
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        if isinstance(self.request.user, AnonymousUser):
            return Feedback.objects.none()

        if self.request.user.role == 'admin':
            return Feedback.objects.all()

        return Feedback.objects.filter(rental__car__owner=self.request.user) | Feedback.objects.filter(rental__renter=self.request.user)

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)


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
            from datetime import datetime
            try:
                start = datetime.strptime(start_date, '%Y-%m-%d').date()
                end = datetime.strptime(end_date, '%Y-%m-%d').date()

                unavailable_car_ids = Rental.objects.filter(
                    status__in=['pending', 'confirmed', 'active']
                ).exclude(
                    end_date__lt=start
                ).exclude(
                    start_date__gt=end
                ).values_list('car_id', flat=True)

                queryset = queryset.exclude(id__in=unavailable_car_ids)
            except ValueError:
                pass

        return queryset


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


class OwnerStatsAPIView(generics.GenericAPIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, *args, **kwargs):
        if request.user.role != 'owner':
            return Response({'detail': 'Только для владельцев'}, status=status.HTTP_403_FORBIDDEN)

        from django.db.models import Sum, Count, Avg

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

        from datetime import datetime, timedelta
        today = datetime.today()
        first_day = today.replace(day=1)
        monthly_revenue = completed_rentals.filter(
            created_date__gte=first_day
        ).aggregate(Sum('total_price'))['total_price__sum'] or 0

        return Response({
            'total_earnings': total_earnings,
            'total_rentals': total_rentals,
            'cars_count': cars_count,
            'average_rating': round(average_rating, 2) if average_rating else None,
            'popular_car': {
                'id': popular_car.id,
                'brand': popular_car.brand,
                'model_name': popular_car.model_name,
                'rental_count': popular_car.rental_count
            } if popular_car else None,
            'monthly_revenue': monthly_revenue,
        })


class FavoriteListAPIView(generics.ListCreateAPIView):
    serializer_class = FavoriteSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Favorite.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        car = serializer.validated_data['car']
        if Favorite.objects.filter(user=self.request.user, car=car).exists():
            from rest_framework.exceptions import ValidationError
            raise ValidationError({'detail': 'Автомобиль уже в избранном'})
        serializer.save(user=self.request.user)


class FavoriteDeleteAPIView(generics.DestroyAPIView):
    serializer_class = FavoriteSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Favorite.objects.filter(user=self.request.user)


class ChatListAPIView(generics.ListAPIView):
    serializer_class = ChatSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Chat.objects.filter(
            rental__renter=self.request.user
        ) | Chat.objects.filter(
            rental__car__owner=self.request.user
        )


class ChatDetailAPIView(generics.RetrieveAPIView):
    serializer_class = ChatSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Chat.objects.filter(
            rental__renter=self.request.user
        ) | Chat.objects.filter(
            rental__car__owner=self.request.user
        )


class ChatMessageCreateAPIView(generics.CreateAPIView):
    serializer_class = ChatMessageSerializer
    permission_classes = [permissions.IsAuthenticated]

    def perform_create(self, serializer):
        chat_id = self.request.data.get('chat_id')
        try:
            chat = Chat.objects.get(id=chat_id)
            if chat.rental.renter != self.request.user and chat.rental.car.owner != self.request.user:
                from rest_framework.exceptions import PermissionDenied
                raise PermissionDenied('Вы не участник этого чата')
            serializer.save(chat=chat, sender=self.request.user)
        except Chat.DoesNotExist:
            from rest_framework.exceptions import ValidationError
            raise ValidationError({'detail': 'Чат не найден'})


class ComplaintListAPIView(generics.ListCreateAPIView):
    serializer_class = ComplaintSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        if self.request.user.role == 'admin':
            return Complaint.objects.all()
        return Complaint.objects.filter(author=self.request.user)

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)


class ComplaintDetailAPIView(generics.RetrieveUpdateAPIView):
    serializer_class = ComplaintSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        if self.request.user.role == 'admin':
            return Complaint.objects.all()
        return Complaint.objects.filter(author=self.request.user)


class SendVerificationCodeAPIView(generics.GenericAPIView):
    serializer_class = VerificationCodeSerializer
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        verification_type = serializer.validated_data['verification_type']

        import random
        from datetime import datetime, timedelta

        code = str(random.randint(100000, 999999))
        expires_at = datetime.now() + timedelta(minutes=10)

        VerificationCode.objects.create(
            user=request.user,
            code=code,
            verification_type=verification_type,
            expires_at=expires_at
        )

        # TODO: Отправить код на email или телефон (пока не реализовано)

        return Response({
            'message': f'Код верификации отправлен на {verification_type}'
        }, status=status.HTTP_200_OK)


class ConfirmVerificationCodeAPIView(generics.GenericAPIView):
    serializer_class = VerificationConfirmSerializer
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        verification_type = serializer.validated_data['verification_type']
        code = serializer.validated_data['code']

        from datetime import datetime

        try:
            verification = VerificationCode.objects.get(
                user=request.user,
                code=code,
                verification_type=verification_type,
                is_used=False,
                expires_at__gte=datetime.now()
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
