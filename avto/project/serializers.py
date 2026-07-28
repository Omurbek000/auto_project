from rest_framework import serializers
from .models import *
from rest_framework_simplejwt.tokens import RefreshToken
from datetime import date


class RegisterSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('username', 'email', 'password', 'phone_number', 'role')
        extra_kwargs = {'password': {'write_only': True}}

    def validate_email(self, value):
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError('Пользователь с таким email уже существует')
        return value

    def create(self, validated_data):
        password = validated_data.pop('password')
        user = User(**validated_data)
        user.set_password(password)
        user.save()
        return user


class CustomLoginSerializer(serializers.Serializer):
    username = serializers.CharField()
    password = serializers.CharField(write_only=True)

    def validate(self, data):
        username = data.get('username')
        password = data.get('password')

        try:
            user = User.objects.get(username=username)
        except User.DoesNotExist:
            raise serializers.ValidationError({'username': 'Пользователь с таким именем не найден'})

        if not user.check_password(password):
            raise serializers.ValidationError({'password': 'Неверный пароль'})

        self.context['user'] = user
        return data

    def to_representation(self, instance):
        user = self.context['user']
        refresh = RefreshToken.for_user(user)

        return {
            'user': {
                'id': user.id,
                'username': user.username,
                'email': user.email,
                'role': user.role,
            },
            'access': str(refresh.access_token),
            'refresh': str(refresh),
        }


class LogoutSerializer(serializers.Serializer):
    refresh = serializers.CharField()

    def validate(self, attrs):
        token = attrs.get('refresh')
        try:
            RefreshToken(token)
        except Exception:
            raise serializers.ValidationError({'refresh': 'Невалидный токен'})
        return attrs


class UserSerializer(serializers.ModelSerializer):
    renter_rating = serializers.ReadOnlyField()
    renter_rating_count = serializers.ReadOnlyField()
    owner_rating = serializers.ReadOnlyField()
    owner_rating_count = serializers.ReadOnlyField()
    age = serializers.ReadOnlyField()
    driving_experience = serializers.ReadOnlyField()

    class Meta:
        model = User
        fields = [
            'id', 'username', 'first_name', 'last_name', 'email', 'phone_number',
            'role', 'avatar', 'bio', 'date_of_birth', 'age', 'driving_license_number',
            'driving_license_date', 'driving_experience', 'languages', 'email_verified',
            'phone_verified', 'is_verified', 'renter_rating', 'renter_rating_count',
            'owner_rating', 'owner_rating_count', 'created_date'
        ]


class CarImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = CarImage
        fields = ['id', 'image', 'created_date']


class CarUnavailableDateSerializer(serializers.ModelSerializer):
    class Meta:
        model = CarUnavailableDate
        fields = ['id', 'start_date', 'end_date', 'reason', 'created_date']


class CarListSerializer(serializers.ModelSerializer):
    owner = UserSerializer(read_only=True)
    owner_id = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.filter(role='owner'),
        write_only=True,
        source='owner',
    )
    average_rating = serializers.ReadOnlyField()
    feedbacks_count = serializers.ReadOnlyField()
    images = CarImageSerializer(many=True, read_only=True)

    class Meta:
        model = Car
        fields = [
            'id',
            'brand',
            'model_name',
            'year',
            'fuel_type',
            'transmission',
            'mileage',
            'price_per_day',
            'location',
            'image',
            'images',
            'owner',
            'owner_id',
            'is_available',
            'average_rating',
            'feedbacks_count',
            'min_age',
            'min_driving_experience',
            'deposit',
            'created_date',
        ]
        read_only_fields = ['owner']


class CarDetailSerializer(serializers.ModelSerializer):
    owner = UserSerializer(read_only=True)
    average_rating = serializers.ReadOnlyField()
    feedbacks_count = serializers.ReadOnlyField()
    images = CarImageSerializer(many=True, read_only=True)
    unavailable_dates = CarUnavailableDateSerializer(many=True, read_only=True)

    class Meta:
        model = Car
        fields = [
            'id',
            'brand',
            'model_name',
            'year',
            'fuel_type',
            'transmission',
            'mileage',
            'price_per_day',
            'description',
            'location',
            'image',
            'images',
            'unavailable_dates',
            'owner',
            'is_available',
            'average_rating',
            'feedbacks_count',
            'min_age',
            'min_driving_experience',
            'deposit',
            'cancellation_policy',
            'created_date',
        ]


class RentalListSerializer(serializers.ModelSerializer):
    car = CarListSerializer(read_only=True)
    renter = UserSerializer(read_only=True)
    car_id = serializers.PrimaryKeyRelatedField(
        queryset=Car.objects.filter(is_available=True),
        write_only=True,
        source='car',
    )

    class Meta:
        model = Rental
        fields = [
            'id',
            'car',
            'car_id',
            'renter',
            'start_date',
            'end_date',
            'total_price',
            'status',
            'created_date',
        ]
        read_only_fields = ['renter', 'total_price', 'status']

    def validate(self, data):
        start = data.get('start_date')
        end = data.get('end_date')
        car = data.get('car')

        if start and end:
            if start < date.today():
                raise serializers.ValidationError(
                    {'start_date': 'Дата начала не может быть в прошлом'}
                )
            if end <= start:
                raise serializers.ValidationError(
                    {'end_date': 'Дата окончания должна быть после даты начала'}
                )

            if car:
                overlapping_rentals = Rental.objects.filter(
                    car=car,
                    status__in=['pending', 'confirmed', 'active']
                ).exclude(
                    end_date__lt=start
                ).exclude(
                    start_date__gt=end
                )

                if self.instance:
                    overlapping_rentals = overlapping_rentals.exclude(id=self.instance.id)

                if overlapping_rentals.exists():
                    raise serializers.ValidationError(
                        {'car': 'Автомобиль уже забронирован на выбранные даты'}
                    )

                unavailable_dates = CarUnavailableDate.objects.filter(
                    car=car
                ).exclude(
                    end_date__lt=start
                ).exclude(
                    start_date__gt=end
                )

                if unavailable_dates.exists():
                    raise serializers.ValidationError(
                        {'car': 'Владелец заблокировал эти даты'}
                    )

        return data

    def create(self, validated_data):
        car = validated_data['car']
        start = validated_data['start_date']
        end = validated_data['end_date']
        days = (end - start).days + 1
        validated_data['total_price'] = car.price_per_day * days
        return super().create(validated_data)


class RentalDetailSerializer(serializers.ModelSerializer):
    car = CarDetailSerializer(read_only=True)
    renter = UserSerializer(read_only=True)

    class Meta:
        model = Rental
        fields = [
            'id',
            'car',
            'renter',
            'start_date',
            'end_date',
            'total_price',
            'status',
            'created_date',
        ]


class FeedbackSerializer(serializers.ModelSerializer):
    rental = RentalListSerializer(read_only=True)
    author = UserSerializer(read_only=True)
    rental_id = serializers.PrimaryKeyRelatedField(
        queryset=Rental.objects.all(),
        write_only=True,
        source='rental',
    )

    class Meta:
        model = Feedback
        fields = [
            'id',
            'rental',
            'rental_id',
            'feedback_type',
            'author',
            'rating',
            'comment',
            'created_date',
        ]
        read_only_fields = ['author']

    def validate(self, data):
        request = self.context.get('request')
        rental = data.get('rental')
        feedback_type = data.get('feedback_type')

        if rental.status != 'completed':
            raise serializers.ValidationError('Вы можете оставлять отзывы только для завершенных аренд')

        if feedback_type == 'car':
            if rental.renter != request.user:
                raise serializers.ValidationError('Только арендатор может оставить отзыв на автомобиль')
        elif feedback_type == 'renter':
            if rental.car.owner != request.user:
                raise serializers.ValidationError('Только владелец может оставить отзыв на арендатора')
        else:
            raise serializers.ValidationError('Неверный тип отзыва')

        if Feedback.objects.filter(rental=rental, feedback_type=feedback_type, author=request.user).exists():
            raise serializers.ValidationError('Вы уже оставили отзыв')

        return data

    def create(self, validated_data):
        validated_data['author'] = self.context['request'].user
        return super().create(validated_data)


class FavoriteSerializer(serializers.ModelSerializer):
    car = CarListSerializer(read_only=True)
    car_id = serializers.PrimaryKeyRelatedField(
        queryset=Car.objects.all(),
        write_only=True,
        source='car',
    )

    class Meta:
        model = Favorite
        fields = ['id', 'car', 'car_id', 'created_date']


class ChatMessageSerializer(serializers.ModelSerializer):
    sender = UserSerializer(read_only=True)

    class Meta:
        model = ChatMessage
        fields = ['id', 'sender', 'message', 'is_read', 'created_date']


class ChatSerializer(serializers.ModelSerializer):
    rental = RentalListSerializer(read_only=True)
    messages = ChatMessageSerializer(many=True, read_only=True)

    class Meta:
        model = Chat
        fields = ['id', 'rental', 'messages', 'created_date']


class ComplaintSerializer(serializers.ModelSerializer):
    author = UserSerializer(read_only=True)
    target_user = UserSerializer(read_only=True)
    target_user_id = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.all(),
        write_only=True,
        source='target_user',
    )

    class Meta:
        model = Complaint
        fields = [
            'id', 'author', 'target_user', 'target_user_id', 'rental',
            'reason', 'description', 'status', 'admin_response',
            'created_date', 'updated_date'
        ]
        read_only_fields = ['author', 'status', 'admin_response']


class VerificationCodeSerializer(serializers.Serializer):
    verification_type = serializers.ChoiceField(choices=['email', 'phone'])


class VerificationConfirmSerializer(serializers.Serializer):
    verification_type = serializers.ChoiceField(choices=['email', 'phone'])
    code = serializers.CharField(max_length=6)
