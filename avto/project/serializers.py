# Сериализаторы — преобразуют данные между Python/БД и JSON (API)
# Валидируют входящие данные, определяют какие поля отдавать клиенту

from rest_framework import serializers
from rest_framework_simplejwt.tokens import RefreshToken
from datetime import date

from .models import User, Car, CarImage, CarUnavailableDate, Rental, Feedback, Favorite, Chat, ChatMessage, Complaint, VerificationCode, AuditLog


# Сериализатор регистрации нового пользователя
# Принимает: username, email, password, phone_number, is_owner
# Создаёт пользователя в БД с захэшированным паролем
class RegisterSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('username', 'email', 'password', 'phone_number', 'is_owner')
        extra_kwargs = {'password': {'write_only': True}}  # Пароль только на вход, никогда не возвращается

    def validate_email(self, value):
        # Проверка: email не должен быть занят
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError('Пользователь с таким email уже существует')
        return value

    def create(self, validated_data):
        # Создание пользователя с правильным хэшированием пароля
        password = validated_data.pop('password')
        user = User(**validated_data)
        user.set_password(password)  # Хэширует пароль (не хранит в открытом виде)
        user.save()
        return user


# Сериализатор логина. Проверяет логин/пароль, возвращает JWT-токены
class CustomLoginSerializer(serializers.Serializer):
    username = serializers.CharField()
    password = serializers.CharField(write_only=True)

    def validate(self, data):
        # Поиск пользователя и проверка пароля
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
        # Формирование ответа с JWT-токенами
        user = self.context['user']
        refresh = RefreshToken.for_user(user)

        return {
            'user': {
                'id': user.id,
                'username': user.username,
                'email': user.email,
                'is_owner': user.is_owner,
                'is_renter': user.is_renter,
                'is_staff': user.is_staff,  # Только для чтения: фронту нужен редирект админа на дашборд
            },
            'access': str(refresh.access_token),   # Токен доступа (короткоживущий)
            'refresh': str(refresh),               # Токен обновления (долгоживущий)
        }


# Сериализатор логаута. Принимает refresh-токен и проверяет его валидность
class LogoutSerializer(serializers.Serializer):
    refresh = serializers.CharField()

    def validate(self, attrs):
        token = attrs.get('refresh')
        try:
            RefreshToken(token)  # Просто проверяем что токен валидный
        except Exception:
            raise serializers.ValidationError({'refresh': 'Невалидный токен'})
        return attrs


# Сериализатор профиля пользователя (детальная информация)
# Показывает рейтинги, возраст, стаж — вычисляемые поля
class UserSerializer(serializers.ModelSerializer):
    # ReadOnlyField — поле только для чтения, клиент не может его изменить
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
            'is_owner', 'is_renter', 'avatar', 'bio', 'date_of_birth', 'age',
            'driving_license_number', 'driving_license_date', 'driving_experience',
            'languages', 'email_verified', 'phone_verified', 'is_verified',
            'renter_rating', 'renter_rating_count', 'owner_rating', 'owner_rating_count',
            'created_date'
        ]


# Сериализатор для массовой загрузки фото
class CarImageBulkUploadSerializer(serializers.Serializer):
    car_id = serializers.IntegerField()

    def validate_car_id(self, value):
        request = self.context.get('request')
        if not Car.objects.filter(id=value, owner=request.user).exists():
            raise serializers.ValidationError('Автомобиль не найден или вы не владелец')
        return value

    def create(self, validated_data):
        car = Car.objects.get(id=validated_data['car_id'])
        files = self.context['request'].FILES.getlist('images')
        if not files:
            raise serializers.ValidationError({'images': 'Не загружено ни одного файла'})
        images = []
        for f in files:
            images.append(CarImage.objects.create(car=car, image=f))
        return images


# Сериализатор изображений автомобиля
class CarImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = CarImage
        fields = ['id', 'image', 'created_date']


# Сериализатор заблокированных дат (владелец вручную блокирует дни)
class CarUnavailableDateSerializer(serializers.ModelSerializer):
    class Meta:
        model = CarUnavailableDate
        fields = ['id', 'start_date', 'end_date', 'reason', 'created_date']


# Сериализатор для списка автомобилей (краткая информация)
class CarListSerializer(serializers.ModelSerializer):
    owner = UserSerializer(read_only=True)                                               # Информация о владельце (только чтение)
    owner_id = serializers.PrimaryKeyRelatedField(                                      # ID владельца (только запись)
        queryset=User.objects.all(),
        write_only=True,
        required=False,
        source='owner',
    )
    average_rating = serializers.ReadOnlyField()                                        # Средний рейтинг
    feedbacks_count = serializers.ReadOnlyField()                                       # Количество отзывов
    images = CarImageSerializer(many=True, read_only=True)                              # Доп. фото

    class Meta:
        model = Car
        fields = [
            'id', 'brand', 'model_name', 'year', 'fuel_type', 'transmission',
            'mileage', 'price_per_day', 'location', 'image', 'images',
            'owner', 'owner_id', 'is_available', 'average_rating', 'feedbacks_count',
            'min_age', 'min_driving_experience', 'deposit', 'created_date',
        ]
        read_only_fields = ['owner']  # Владелец автоматически проставляется из запроса


# Сериализатор для детальной страницы автомобиля
class CarDetailSerializer(serializers.ModelSerializer):
    owner = UserSerializer(read_only=True)
    average_rating = serializers.ReadOnlyField()
    feedbacks_count = serializers.ReadOnlyField()
    images = CarImageSerializer(many=True, read_only=True)
    unavailable_dates = CarUnavailableDateSerializer(many=True, read_only=True)  # Заблокированные даты

    class Meta:
        model = Car
        fields = [
            'id', 'brand', 'model_name', 'year', 'fuel_type', 'transmission',
            'mileage', 'price_per_day', 'description', 'location', 'image',
            'images', 'unavailable_dates', 'owner', 'is_available',
            'average_rating', 'feedbacks_count', 'min_age', 'min_driving_experience',
            'deposit', 'cancellation_policy', 'created_date',
        ]


# Общая проверка дат аренды. Используется и при создании (RentalListSerializer),
# и при изменении дат существующей аренды (RentalDetailSerializer), чтобы
# продление не «перекрыло» уже занятые другим человеком даты.
# data — словарь валидированных полей (start_date/end_date/car), instance —
# текущая аренда при обновлении (её даты не считаем пересечением).
def validate_rental_dates(data, instance=None):
    # При PATCH (частичное обновление) в data приходят только изменённые поля,
    # поэтому недостающие даты подставляем из текущей записи
    start = data.get('start_date') or (instance.start_date if instance else None)
    end = data.get('end_date') or (instance.end_date if instance else None)

    if not (start and end):
        return data

    # Дата начала не может быть в прошлом
    if start < date.today():
        raise serializers.ValidationError(
            {'start_date': 'Дата начала не может быть в прошлом'}
        )
    # Дата окончания должна быть позже даты начала
    if end <= start:
        raise serializers.ValidationError(
            {'end_date': 'Дата окончания должна быть после даты начала'}
        )

    # Машина: при создании она приходит в data, при обновлении берём из instance
    car = data.get('car') or (instance.car if instance else None)

    if car:
        # Блокируем строку машины на время транзакции (ATOMIC_REQUESTS): если два
        # запроса одновременно бронируют одну машину, второй подождёт, пока первый
        # закоммитится, и уже увидит его бронь в проверке ниже. Иначе оба могли бы
        # пройти проверку «не пересекается» и создать двойное бронирование.
        # select_for_update работает на PostgreSQL/MySQL; на SQLite это no-op
        # (дев-режим, там нет блокировок строк).
        car = Car.objects.select_for_update().get(pk=car.pk)

        # Проверка пересечения с другими арендами
        overlapping_rentals = Rental.objects.filter(
            car=car,
            status__in=['pending', 'confirmed', 'active']
        ).exclude(end_date__lt=start).exclude(start_date__gt=end)

        if instance:
            overlapping_rentals = overlapping_rentals.exclude(id=instance.id)

        if overlapping_rentals.exists():
            raise serializers.ValidationError(
                {'car': 'Автомобиль уже забронирован на выбранные даты'}
            )

        # Проверка пересечения с заблокированными владельцем датами
        unavailable_dates = CarUnavailableDate.objects.filter(car=car
        ).exclude(end_date__lt=start).exclude(start_date__gt=end)

        if unavailable_dates.exists():
            raise serializers.ValidationError(
                {'car': 'Владелец заблокировал эти даты'}
            )

    return data


# Сериализатор аренды (создание и список)
class RentalListSerializer(serializers.ModelSerializer):
    car = CarListSerializer(read_only=True)                                      # Данные о машине
    renter = UserSerializer(read_only=True)                                      # Данные об арендаторе
    car_id = serializers.PrimaryKeyRelatedField(                                 # ID машины (только запись)
        queryset=Car.objects.all(),                                              # Проверка пересечений дат — в validate()
        write_only=True,
        source='car',
    )

    class Meta:
        model = Rental
        fields = [
            'id', 'car', 'car_id', 'renter',
            'start_date', 'end_date', 'total_price', 'status', 'created_date',
        ]
        read_only_fields = ['renter', 'total_price', 'status']  # Проставляются автоматически

    def get_fields(self):
        fields = super().get_fields()
        request = self.context.get('request')
        # Скрываем цену аренды от админа: это маркетплейс, доходы пользователей
        # анонимны. Владелец и арендатор свою цену видят, админ — нет.
        if request and getattr(request.user, 'is_staff', False):
            fields.pop('total_price', None)
        return fields

    def validate(self, data):
        # Проверка дат и доступности автомобиля (общая логика — в validate_rental_dates)
        return validate_rental_dates(data, self.instance)

    def create(self, validated_data):
        # Автоматический расчёт итоговой цены: цена_за_день * количество_дней
        car = validated_data['car']
        start = validated_data['start_date']
        end = validated_data['end_date']
        days = (end - start).days + 1
        validated_data['total_price'] = car.price_per_day * days
        return super().create(validated_data)


# Сериализатор для детальной страницы аренды
class RentalDetailSerializer(serializers.ModelSerializer):
    car = CarDetailSerializer(read_only=True)
    renter = UserSerializer(read_only=True)

    class Meta:
        model = Rental
        fields = [
            'id', 'car', 'renter',
            'start_date', 'end_date', 'total_price', 'status', 'created_date',
        ]
        # status/total_price/renter менять через PATCH нельзя:
        # статусы меняются только через /confirm/, /reject/, /start/, /complete/,
        # цена всегда пересчитывается автоматически из дат (см. update ниже)
        read_only_fields = ['renter', 'total_price', 'status']

    def get_fields(self):
        fields = super().get_fields()
        request = self.context.get('request')
        # Скрываем цену аренды от админа (см. RentalListSerializer)
        if request and getattr(request.user, 'is_staff', False):
            fields.pop('total_price', None)
        return fields

    def validate(self, data):
        # Проверка пересечений дат при продлении/изменении аренды
        return validate_rental_dates(data, self.instance)

    def update(self, instance, validated_data):
        # При изменении дат пересчитываем цену (цена_за_день × дни)
        start = validated_data.get('start_date', instance.start_date)
        end = validated_data.get('end_date', instance.end_date)
        days = (end - start).days + 1
        validated_data['total_price'] = instance.car.price_per_day * days
        return super().update(instance, validated_data)


# Сериализатор отзыва
class FeedbackSerializer(serializers.ModelSerializer):
    rental = RentalListSerializer(read_only=True)
    author = UserSerializer(read_only=True)
    rental_id = serializers.PrimaryKeyRelatedField(  # ID аренды (только запись)
        queryset=Rental.objects.all(),
        write_only=True,
        source='rental',
    )

    class Meta:
        model = Feedback
        fields = [
            'id', 'rental', 'rental_id', 'feedback_type',
            'author', 'rating', 'comment', 'created_date',
        ]
        read_only_fields = ['author']

    def validate(self, data):
        # Проверка: отзыв только для завершённой аренды, и только участник может писать
        request = self.context.get('request')
        rental = data.get('rental')
        feedback_type = data.get('feedback_type')

        # Эти проверки актуальны только при создании отзыва (или когда rental/тип
        # явно переданы). При частичном обновлении (PATCH) rental может быть None —
        # тогда за права отвечает views.perform_update (только автор или админ)
        if rental and feedback_type:
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

            # Проверка на повторный отзыв
            if Feedback.objects.filter(rental=rental, feedback_type=feedback_type, author=request.user).exists():
                raise serializers.ValidationError('Вы уже оставили отзыв')

        return data

    def create(self, validated_data):
        validated_data['author'] = self.context['request'].user
        return super().create(validated_data)


# Сериализатор избранного
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


# Сериализатор сообщения в чате
class ChatMessageSerializer(serializers.ModelSerializer):
    sender = UserSerializer(read_only=True)

    class Meta:
        model = ChatMessage
        fields = ['id', 'sender', 'message', 'is_read', 'created_date']


# Сериализатор чата (с вложенными сообщениями)
class ChatSerializer(serializers.ModelSerializer):
    rental = RentalListSerializer(read_only=True)
    messages = ChatMessageSerializer(many=True, read_only=True)

    class Meta:
        model = Chat
        fields = ['id', 'rental', 'messages', 'created_date']


# Сериализатор жалобы
class ComplaintSerializer(serializers.ModelSerializer):
    author = UserSerializer(read_only=True)
    target_user = UserSerializer(read_only=True)
    target_user_id = serializers.PrimaryKeyRelatedField(  # ID пользователя на кого жалуются
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


# Сериализатор админа для управления пользователями.
# В отличие от UserSerializer, позволяет менять блокировку (is_active),
# верификацию (is_verified) и роли (is_owner/is_renter).
# is_staff — read_only: выдавать права админа может только суперпользователь
# через Django-админку (защита от эскалации прав через API).
class AdminUserSerializer(serializers.ModelSerializer):
    age = serializers.ReadOnlyField()
    driving_experience = serializers.ReadOnlyField()

    class Meta:
        model = User
        fields = [
            'id', 'username', 'first_name', 'last_name', 'email', 'phone_number',
            'is_active', 'is_owner', 'is_renter', 'is_staff',
            'is_verified', 'email_verified', 'phone_verified',
            'age', 'driving_experience', 'created_date',
        ]
        extra_kwargs = {'is_staff': {'read_only': True}}


# Сериализатор админа для жалоб.
# У обычного пользователя status и admin_response — read_only,
# админ же может менять статус жалобы и писать ответ.
class AdminComplaintSerializer(serializers.ModelSerializer):
    author = UserSerializer(read_only=True)
    target_user = UserSerializer(read_only=True)

    class Meta:
        model = Complaint
        fields = [
            'id', 'author', 'target_user', 'rental',
            'reason', 'description', 'status', 'admin_response',
            'created_date', 'updated_date'
        ]
        read_only_fields = ['author', 'target_user', 'rental']


# Сериализатор записи журнала аудита (только чтение — записи создаются системой)
class AuditLogSerializer(serializers.ModelSerializer):
    username = serializers.CharField(source='user.username', read_only=True, default=None)

    class Meta:
        model = AuditLog
        fields = ['id', 'user', 'username', 'action', 'model_name', 'object_id', 'details', 'created_date']


# Сериализатор запроса кода верификации
class VerificationCodeSerializer(serializers.Serializer):
    verification_type = serializers.ChoiceField(choices=['email', 'phone'])


# Сериализатор подтверждения кода верификации
class VerificationConfirmSerializer(serializers.Serializer):
    verification_type = serializers.ChoiceField(choices=['email', 'phone'])
    code = serializers.CharField(max_length=6)


# Сериализатор запроса сброса пароля (принимает email)
class PasswordResetRequestSerializer(serializers.Serializer):
    email = serializers.EmailField()

    def validate_email(self, value):
        # Проверка: пользователь с таким email должен существовать
        if not User.objects.filter(email=value).exists():
            raise serializers.ValidationError('Пользователь с таким email не найден')
        return value


# Сериализатор подтверждения сброса пароля (код + новый пароль)
class PasswordResetConfirmSerializer(serializers.Serializer):
    email = serializers.EmailField()
    code = serializers.CharField(max_length=6)
    new_password = serializers.CharField(write_only=True, min_length=8)

    def validate_email(self, value):
        if not User.objects.filter(email=value).exists():
            raise serializers.ValidationError('Пользователь с таким email не найден')
        return value


# Сериализатор смены пароля авторизованного пользователя (старый + новый пароль)
class PasswordChangeSerializer(serializers.Serializer):
    old_password = serializers.CharField(write_only=True)
    new_password = serializers.CharField(write_only=True, min_length=8)

    def validate_old_password(self, value):
        request = self.context.get('request')
        if not request.user.check_password(value):
            raise serializers.ValidationError('Старый пароль неверный')
        return value
