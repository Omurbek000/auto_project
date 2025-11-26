from django.db import models
from django.contrib.auth.models import AbstractUser
from phonenumber_field.formfields import PhoneNumberField
from django.core.validators import MinValueValidator, MaxValueValidator

class User(AbstractUser):
    ROLE_CHOICES = (
        ('Admin','Admin'),
        ('Seller','Seller'),
        ('buyer','buyer'),
    )
    role = models.CharField(max_length=32, choices=ROLE_CHOICES, default='buyer')
    phone_number = PhoneNumberField(region='KG' unique=True, blank=True, null=True)
    
class Car(models.Model):
    FUEL_CHOICES = (
        ('petrol','petrol'),
        ('diesel','diesel'),
        ('elektrik','elektrik')
        ('gibrid','gibrid')
    )
    TRANS_CHOICES = (
        ('manual','manual')
        ('auto','auto')
    )
    CONDIRIONS_CHOICES = (
        ('new','new'),
        ('used','used')
        ('damaged','damaged')
    )
    brand = models.CharField(max_length=100)
    model = models.CharField(max_length=100)
    year = models.IntegerField()
    fuel_type = models.CharField(max_length=100, choices=FUEL_CHOICES)
    transmission = models.CharField(max_length=100, choices=TRANS_CHOICES)
    milage = models.IntegerField()
    price = models.DecimalField()
    condition = models.CharField(max_length=100, choices=CONDIRIONS_CHOICES)
    description = models.TextField()
    image = models.ImageField(upload_to='car_images/')
    seller = models.ForeignKey(User, on_delete=models.CASCADE)


class Auction(models.Model):
    STATUS_CHOICSE =(
        ('active','active'),
        ('finished','finished')
        ('canceled','canceled')
    )
    car = models.OneToOneField(Car, on_delete=models.CASCADE)
    start_price = models.DecimalField()
    min_price = models.DecimalField()
    start_time = models.DateTimeField(auto_now_add=True)
    end_time = models.DateTimeField()
    status = models.CharField(max_length=15, choices=STATUS_CHOICSE, default='active')    


class Bid(models.Model):
    auction = models.ForeignKey(Auction, on_delete=models.CASCADE)
    buyer = models.ForeignKey(User, on_delete=models.CASCADE)
    amount = models.DecimalField()
    creted_at = models.DateTimeField(auto_now_add=True) 

class Feedback(models.Model):
    seller = models.ForeignKey(User, on_delete=models.CASCADE)
    buyer = models.ForeignKey(User, on_delete=models.CASCADE)       
    rating = models.IntegerField(validators=[MinValueValidator(1), MaxValueValidator(5)])
    comment = models.TextField()