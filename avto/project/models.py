from django.db import models
from django.contrib.auth.models import AbstractUser
from phonenumber_field.modelfields import PhoneNumberField
from django.core.validators import MinValueValidator, MaxValueValidator


ROLE_CHOICES = (
    ('admin', 'admin'),
    ('owner', 'owner'),
    ('renter', 'renter'),
)

FUEL_CHOICES = (
    ('petrol', 'petrol'),
    ('diesel', 'diesel'),
    ('electric', 'electric'),
    ('hybrid', 'hybrid'),
)

TRANS_CHOICES = (
    ('manual', 'manual'),
    ('auto', 'auto'),
)

RENTAL_STATUS_CHOICES = (
    ('pending', 'pending'),
    ('confirmed', 'confirmed'),
    ('active', 'active'),
    ('completed', 'completed'),
    ('canceled', 'canceled'),
)


class User(AbstractUser):
    role = models.CharField(max_length=32, choices=ROLE_CHOICES, default='renter')
    phone_number = PhoneNumberField(unique=True, blank=True, null=True)
    avatar = models.ImageField(upload_to='avatars/', blank=True, null=True)
    bio = models.TextField(blank=True, null=True)
    date_of_birth = models.DateField(blank=True, null=True)
    driving_license_number = models.CharField(max_length=50, blank=True, null=True)
    driving_license_date = models.DateField(blank=True, null=True)
    languages = models.CharField(max_length=255, blank=True, null=True)
    email_verified = models.BooleanField(default=False)
    phone_verified = models.BooleanField(default=False)
    is_verified = models.BooleanField(default=False)
    created_date = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.username

    @property
    def age(self):
        if self.date_of_birth:
            from datetime import date
            today = date.today()
            return today.year - self.date_of_birth.year - ((today.month, today.day) < (self.date_of_birth.month, self.date_of_birth.day))
        return None

    @property
    def driving_experience(self):
        if self.driving_license_date:
            from datetime import date
            today = date.today()
            years = today.year - self.driving_license_date.year
            return years if years >= 0 else 0
        return None

    @property
    def renter_rating(self):
        from django.db.models import Avg
        feedbacks = Feedback.objects.filter(rental__renter=self, feedback_type='renter')
        avg = feedbacks.aggregate(Avg('rating'))['rating__avg']
        return round(avg, 2) if avg else None

    @property
    def renter_rating_count(self):
        return Feedback.objects.filter(rental__renter=self, feedback_type='renter').count()

    @property
    def owner_rating(self):
        from django.db.models import Avg
        feedbacks = Feedback.objects.filter(rental__car__owner=self, feedback_type='car')
        avg = feedbacks.aggregate(Avg('rating'))['rating__avg']
        return round(avg, 2) if avg else None

    @property
    def owner_rating_count(self):
        return Feedback.objects.filter(rental__car__owner=self, feedback_type='car').count()


class Car(models.Model):
    brand = models.CharField(max_length=100)
    model_name = models.CharField(max_length=100)
    year = models.PositiveIntegerField()
    fuel_type = models.CharField(max_length=20, choices=FUEL_CHOICES)
    transmission = models.CharField(max_length=20, choices=TRANS_CHOICES)
    mileage = models.PositiveIntegerField()
    price_per_day = models.DecimalField(max_digits=10, decimal_places=2)
    description = models.TextField()
    location = models.CharField(max_length=255)
    image = models.ImageField(upload_to='car_images/')
    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name='cars', limit_choices_to={'role': 'owner'})
    is_available = models.BooleanField(default=True)
    min_age = models.PositiveIntegerField(default=21)
    min_driving_experience = models.PositiveIntegerField(default=2)
    deposit = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    cancellation_policy = models.TextField(blank=True, null=True)
    created_date = models.DateField(auto_now_add=True)

    def __str__(self):
        return f"{self.brand} {self.model_name} ({self.year})"

    @property
    def average_rating(self):
        from django.db.models import Avg
        avg = self.rentals.filter(feedback__isnull=False).aggregate(Avg('feedback__rating'))['feedback__rating__avg']
        return round(avg, 2) if avg else None

    @property
    def feedbacks_count(self):
        return self.rentals.filter(feedback__isnull=False).count()

    class Meta:
        ordering = ['-created_date']


class CarImage(models.Model):
    car = models.ForeignKey(Car, on_delete=models.CASCADE, related_name='images')
    image = models.ImageField(upload_to='car_images/')
    created_date = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.car.brand} {self.car.model_name} - Image"

    class Meta:
        ordering = ['created_date']


class CarUnavailableDate(models.Model):
    car = models.ForeignKey(Car, on_delete=models.CASCADE, related_name='unavailable_dates')
    start_date = models.DateField()
    end_date = models.DateField()
    reason = models.CharField(max_length=255, blank=True, null=True)
    created_date = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.car} - {self.start_date} to {self.end_date}"

    class Meta:
        ordering = ['start_date']


class Rental(models.Model):
    car = models.ForeignKey(Car, on_delete=models.CASCADE, related_name='rentals')
    renter = models.ForeignKey(User, on_delete=models.CASCADE, related_name='rentals', limit_choices_to={'role': 'renter'})
    start_date = models.DateField()
    end_date = models.DateField()
    total_price = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(max_length=15, choices=RENTAL_STATUS_CHOICES, default='pending')
    created_date = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.renter} → {self.car} ({self.status})"

    class Meta:
        ordering = ['-created_date']


FEEDBACK_TYPE_CHOICES = (
    ('car', 'car'),
    ('renter', 'renter'),
)


class Feedback(models.Model):
    rental = models.ForeignKey(Rental, on_delete=models.CASCADE, related_name='feedbacks')
    feedback_type = models.CharField(max_length=10, choices=FEEDBACK_TYPE_CHOICES)
    author = models.ForeignKey(User, on_delete=models.CASCADE, related_name='given_feedbacks')
    rating = models.PositiveSmallIntegerField(validators=[MinValueValidator(1), MaxValueValidator(5)])
    comment = models.TextField()
    created_date = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.author.username} → {self.feedback_type}: {self.rating}"

    class Meta:
        ordering = ['-created_date']
        unique_together = ['rental', 'feedback_type', 'author']


class Favorite(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='favorites')
    car = models.ForeignKey(Car, on_delete=models.CASCADE, related_name='favorited_by')
    created_date = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} → {self.car}"

    class Meta:
        ordering = ['-created_date']
        unique_together = ['user', 'car']


class Chat(models.Model):
    rental = models.OneToOneField(Rental, on_delete=models.CASCADE, related_name='chat')
    created_date = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Chat: {self.rental}"

    class Meta:
        ordering = ['-created_date']


class ChatMessage(models.Model):
    chat = models.ForeignKey(Chat, on_delete=models.CASCADE, related_name='messages')
    sender = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sent_messages')
    message = models.TextField()
    is_read = models.BooleanField(default=False)
    created_date = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.sender.username}: {self.message[:50]}"

    class Meta:
        ordering = ['created_date']


COMPLAINT_STATUS_CHOICES = (
    ('pending', 'pending'),
    ('reviewing', 'reviewing'),
    ('resolved', 'resolved'),
    ('rejected', 'rejected'),
)


class Complaint(models.Model):
    author = models.ForeignKey(User, on_delete=models.CASCADE, related_name='complaints_made')
    target_user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='complaints_received')
    rental = models.ForeignKey(Rental, on_delete=models.CASCADE, related_name='complaints', blank=True, null=True)
    reason = models.CharField(max_length=255)
    description = models.TextField()
    status = models.CharField(max_length=20, choices=COMPLAINT_STATUS_CHOICES, default='pending')
    admin_response = models.TextField(blank=True, null=True)
    created_date = models.DateTimeField(auto_now_add=True)
    updated_date = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.author.username} → {self.target_user.username}: {self.reason}"

    class Meta:
        ordering = ['-created_date']


class VerificationCode(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='verification_codes')
    code = models.CharField(max_length=6)
    verification_type = models.CharField(max_length=10, choices=(('email', 'email'), ('phone', 'phone')))
    is_used = models.BooleanField(default=False)
    expires_at = models.DateTimeField()
    created_date = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} - {self.verification_type}: {self.code}"

    class Meta:
        ordering = ['-created_date']
