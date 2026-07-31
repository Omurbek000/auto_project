# Модели данных (таблицы в базе данных)
# Каждый класс = одна таблица, каждое поле = колонка в таблице

from django.db import models
from django.contrib.auth.models import AbstractUser
from django.db.models import Avg
from datetime import date
from phonenumber_field.modelfields import PhoneNumberField
from django.core.validators import MinValueValidator, MaxValueValidator


# Константы-списки для полей с выбором одного варианта (choices)
# Хранятся отдельно, чтобы не загромождать классы моделей

FUEL_CHOICES = (
    ('petrol', 'petrol'),      # Бензин
    ('diesel', 'diesel'),       # Дизель
    ('electric', 'electric'),   # Электро
    ('hybrid', 'hybrid'),       # Гибрид
)

TRANS_CHOICES = (
    ('manual', 'manual'),       # Механика
    ('auto', 'auto'),           # Автомат
)

RENTAL_STATUS_CHOICES = (
    ('pending', 'pending'),     # Ожидает подтверждения владельцем
    ('confirmed', 'confirmed'), # Подтверждена владельцем
    ('active', 'active'),       # Активна (арендатор забрал машину)
    ('completed', 'completed'), # Завершена (арендатор вернул машину)
    ('canceled', 'canceled'),   # Отменена (владельцем или автоматически)
)


# Пользователь. Расширяет стандартную модель User из Django (AbstractUser)
# AbstractUser уже содержит: username, password, email, first_name, last_name, is_staff, is_active и тд
class User(AbstractUser):
    # Свои (дополнительные) поля
    is_owner = models.BooleanField(default=False, verbose_name='Владелец авто')  # Может сдавать машины
    is_renter = models.BooleanField(default=True, verbose_name='Арендатор')      # Может брать в аренду
    phone_number = PhoneNumberField(unique=True, blank=True, null=True)          # Номер телефона (уникальный)
    avatar = models.ImageField(upload_to='avatars/', blank=True, null=True)      # Аватарка
    bio = models.TextField(blank=True, null=True)                                # О себе
    date_of_birth = models.DateField(blank=True, null=True)                      # Дата рождения
    driving_license_number = models.CharField(max_length=50, blank=True, null=True)  # Номер прав
    driving_license_date = models.DateField(blank=True, null=True)               # Дата получения прав
    languages = models.CharField(max_length=255, blank=True, null=True)          # Языки
    email_verified = models.BooleanField(default=False)                          # Email подтверждён?
    phone_verified = models.BooleanField(default=False)                          # Телефон подтверждён?
    is_verified = models.BooleanField(default=False)                             # Личность подтверждена?
    created_date = models.DateTimeField(auto_now_add=True)                       # Дата регистрации

    def __str__(self):
        # Что показывать в админке и при выводе объекта
        return self.username

    # Вычисляемые поля (@property). Не хранятся в БД, считаются на лету

    @property
    def age(self):
        if self.date_of_birth:
            today = date.today()
            return today.year - self.date_of_birth.year - ((today.month, today.day) < (self.date_of_birth.month, self.date_of_birth.day))
        return None

    @property
    def driving_experience(self):
        if self.driving_license_date:
            today = date.today()
            years = today.year - self.driving_license_date.year
            return years if years >= 0 else 0
        return None

    @property
    def renter_rating(self):
        feedbacks = Feedback.objects.filter(rental__renter=self, feedback_type='renter')
        avg = feedbacks.aggregate(Avg('rating'))['rating__avg']
        return round(avg, 2) if avg else None

    @property
    def renter_rating_count(self):
        return Feedback.objects.filter(rental__renter=self, feedback_type='renter').count()

    @property
    def owner_rating(self):
        feedbacks = Feedback.objects.filter(rental__car__owner=self, feedback_type='car')
        avg = feedbacks.aggregate(Avg('rating'))['rating__avg']
        return round(avg, 2) if avg else None

    @property
    def owner_rating_count(self):
        return Feedback.objects.filter(rental__car__owner=self, feedback_type='car').count()


# Автомобиль
class Car(models.Model):
    brand = models.CharField(max_length=100)                              # Марка (Toyota, BMW и тд)
    model_name = models.CharField(max_length=100)                         # Модель (Camry, X5)
    year = models.PositiveIntegerField()                                  # Год выпуска
    fuel_type = models.CharField(max_length=20, choices=FUEL_CHOICES)    # Тип топлива
    transmission = models.CharField(max_length=20, choices=TRANS_CHOICES) # Коробка передач
    mileage = models.PositiveIntegerField()                               # Пробег (км)
    price_per_day = models.DecimalField(max_digits=10, decimal_places=2)  # Цена за сутки
    description = models.TextField()                                      # Описание
    location = models.CharField(max_length=255)                           # Локация (город/адрес)
    image = models.ImageField(upload_to='car_images/', blank=True, null=True)  # Главное фото
    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name='cars')  # Владелец (кто сдаёт)
    is_available = models.BooleanField(default=True)                      # Доступна ли сейчас
    min_age = models.PositiveIntegerField(default=21)                     # Минимальный возраст арендатора
    min_driving_experience = models.PositiveIntegerField(default=2)       # Минимальный стаж (лет)
    deposit = models.DecimalField(max_digits=10, decimal_places=2, default=0)  # Залог
    cancellation_policy = models.TextField(blank=True, null=True)         # Условия отмены
    created_date = models.DateField(auto_now_add=True)                    # Дата добавления

    def __str__(self):
        return f"{self.brand} {self.model_name} ({self.year})"

    @property
    def average_rating(self):
        avg = self.rentals.filter(feedbacks__isnull=False).aggregate(Avg('feedbacks__rating'))['feedbacks__rating__avg']
        return round(avg, 2) if avg else None

    @property
    def feedbacks_count(self):
        return self.rentals.filter(feedbacks__isnull=False).count()

    class Meta:
        ordering = ['-created_date']  # Сортировка: новые сверху


# Дополнительные фотографии автомобиля
class CarImage(models.Model):
    car = models.ForeignKey(Car, on_delete=models.CASCADE, related_name='images')
    image = models.ImageField(upload_to='car_images/')
    created_date = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.car.brand} {self.car.model_name} - Image"

    class Meta:
        ordering = ['created_date']


# Даты, когда автомобиль недоступен (владелец вручную заблокировал)
class CarUnavailableDate(models.Model):
    car = models.ForeignKey(Car, on_delete=models.CASCADE, related_name='unavailable_dates')
    start_date = models.DateField()                                    # С какой даты
    end_date = models.DateField()                                      # По какую дату
    reason = models.CharField(max_length=255, blank=True, null=True)    # Причина
    created_date = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.car} - {self.start_date} to {self.end_date}"

    class Meta:
        ordering = ['start_date']


# Аренда. Главный бизнес-объект — связывает машину, арендатора и даты
class Rental(models.Model):
    car = models.ForeignKey(Car, on_delete=models.CASCADE, related_name='rentals')
    renter = models.ForeignKey(User, on_delete=models.CASCADE, related_name='rentals')
    start_date = models.DateField()                                     # Дата начала аренды
    end_date = models.DateField()                                       # Дата окончания
    total_price = models.DecimalField(max_digits=10, decimal_places=2)  # Итоговая цена
    status = models.CharField(max_length=15, choices=RENTAL_STATUS_CHOICES, default='pending')
    created_date = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.renter} → {self.car} ({self.status})"

    class Meta:
        ordering = ['-created_date']


FEEDBACK_TYPE_CHOICES = (
    ('car', 'car'),         # Отзыв на автомобиль
    ('renter', 'renter'),   # Отзыв на арендатора
)


# Отзыв. Можно оставить на машину (от арендатора) или на арендатора (от владельца)
class Feedback(models.Model):
    rental = models.ForeignKey(Rental, on_delete=models.CASCADE, related_name='feedbacks')
    feedback_type = models.CharField(max_length=10, choices=FEEDBACK_TYPE_CHOICES)  # Тип отзыва
    author = models.ForeignKey(User, on_delete=models.CASCADE, related_name='given_feedbacks')
    rating = models.PositiveSmallIntegerField(validators=[MinValueValidator(1), MaxValueValidator(5)])  # Оценка 1-5
    comment = models.TextField()                   # Текст отзыва
    created_date = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.author.username} → {self.feedback_type}: {self.rating}"

    class Meta:
        ordering = ['-created_date']
        unique_together = ['rental', 'feedback_type', 'author']  # Нельзя два отзыва одного типа на одну аренду


# Избранное. Пользователь может добавить машину в избранное
class Favorite(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='favorites')
    car = models.ForeignKey(Car, on_delete=models.CASCADE, related_name='favorited_by')
    created_date = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} → {self.car}"

    class Meta:
        ordering = ['-created_date']
        unique_together = ['user', 'car']  # Нельзя добавить одну машину дважды


# Чат. Создаётся автоматически при бронировании для общения владельца и арендатора
class Chat(models.Model):
    rental = models.OneToOneField(Rental, on_delete=models.CASCADE, related_name='chat')
    created_date = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Chat: {self.rental}"

    class Meta:
        ordering = ['-created_date']


# Сообщение в чате
class ChatMessage(models.Model):
    chat = models.ForeignKey(Chat, on_delete=models.CASCADE, related_name='messages')
    sender = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sent_messages')
    message = models.TextField()
    is_read = models.BooleanField(default=False)     # Прочитано ли получателем
    created_date = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.sender.username}: {self.message[:50]}"

    class Meta:
        ordering = ['created_date']


COMPLAINT_STATUS_CHOICES = (
    ('pending', 'pending'),     # Ожидает рассмотрения
    ('reviewing', 'reviewing'), # Рассматривается
    ('resolved', 'resolved'),   # Решена
    ('rejected', 'rejected'),   # Отклонена
)


# Жалоба. Один пользователь жалуется на другого
class Complaint(models.Model):
    author = models.ForeignKey(User, on_delete=models.CASCADE, related_name='complaints_made')
    target_user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='complaints_received')
    rental = models.ForeignKey(Rental, on_delete=models.CASCADE, related_name='complaints', blank=True, null=True)
    reason = models.CharField(max_length=255)             # Причина (коротко)
    description = models.TextField()                      # Описание (подробно)
    status = models.CharField(max_length=20, choices=COMPLAINT_STATUS_CHOICES, default='pending')
    admin_response = models.TextField(blank=True, null=True)  # Ответ администратора
    created_date = models.DateTimeField(auto_now_add=True)
    updated_date = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.author.username} → {self.target_user.username}: {self.reason}"

    class Meta:
        ordering = ['-created_date']


VERIFICATION_TYPE_CHOICES = (
    ('email', 'email'),               # Верификация email
    ('phone', 'phone'),               # Верификация телефона
    ('password_reset', 'password_reset'),  # Сброс пароля
)


# Код подтверждения. Используется для email/phone верификации и сброса пароля
class VerificationCode(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='verification_codes')
    code = models.CharField(max_length=6)                                    # 6-значный код
    verification_type = models.CharField(max_length=20, choices=VERIFICATION_TYPE_CHOICES)
    is_used = models.BooleanField(default=False)                             # Использован?
    expires_at = models.DateTimeField()                                      # До какого времени действителен
    created_date = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} - {self.verification_type}: {self.code}"

    class Meta:
        ordering = ['-created_date']
