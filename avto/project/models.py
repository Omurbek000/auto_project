from django.db import models
from django.contrib.auth.models import AbstractUser
from phonenumber_field.modelfields import PhoneNumberField
from django.core.validators import MinValueValidator, MaxValueValidator


ROLE_CHOICES = (
    ('admin', 'admin'),
    ('seller', 'seller'),
    ('buyer', 'buyer'),
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

CONDITION_CHOICES = (
    ('new', 'new'),
    ('used', 'used'),
    ('damaged', 'damaged'),
)

STATUS_CHOICES = (
    ('active', 'active'),
    ('finished', 'finished'),
    ('canceled', 'canceled'),
)


class User(AbstractUser):
    role = models.CharField(max_length=32, choices=ROLE_CHOICES, default='buyer')
    phone_number = PhoneNumberField(unique=True, blank=True, null=True)

    def __str__(self):
        return self.username


class Car(models.Model):
    brand = models.CharField(max_length=100)
    model_name = models.CharField(max_length=100)
    year = models.PositiveIntegerField()
    fuel_type = models.CharField(max_length=20, choices=FUEL_CHOICES)
    transmission = models.CharField(max_length=20, choices=TRANS_CHOICES)
    mileage = models.PositiveIntegerField()
    price = models.DecimalField(max_digits=10, decimal_places=2)
    condition = models.CharField(max_length=20, choices=CONDITION_CHOICES)
    description = models.TextField()
    image = models.ImageField(upload_to='car_images/')
    seller = models.ForeignKey(User, on_delete=models.CASCADE, related_name='cars')
    is_available = models.BooleanField(default=True)
    created_date = models.DateField(auto_now_add=True)

    def __str__(self):
        return f"{self.brand} {self.model_name} ({self.year})"

    class Meta:
        ordering = ['-created_date']


class Auction(models.Model):
    car = models.OneToOneField(Car, on_delete=models.CASCADE, related_name='auction')
    start_price = models.DecimalField(max_digits=10, decimal_places=2)
    min_price = models.DecimalField(max_digits=10, decimal_places=2)
    start_time = models.DateTimeField(auto_now_add=True)
    end_time = models.DateTimeField()
    status = models.CharField(max_length=15, choices=STATUS_CHOICES, default='active')

    def __str__(self):
        return f"Auction: {self.car} ({self.status})"

    class Meta:
        ordering = ['-start_time']


class Bid(models.Model):
    auction = models.ForeignKey(Auction, on_delete=models.CASCADE, related_name='bids')
    buyer = models.ForeignKey(User, on_delete=models.CASCADE, related_name='bids')
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.buyer} - {self.amount}"

    class Meta:
        ordering = ['-created_at']


class Feedback(models.Model):
    seller = models.ForeignKey(User, on_delete=models.CASCADE, related_name='seller_feedbacks')
    buyer = models.ForeignKey(User, on_delete=models.CASCADE, related_name='buyer_feedbacks')
    rating = models.PositiveSmallIntegerField(validators=[MinValueValidator(1), MaxValueValidator(5)])
    comment = models.TextField()
    created_date = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.buyer} → {self.seller}: {self.rating}"

    class Meta:
        ordering = ['-created_date']
