# auction/filters.py
from django_filters import FilterSet
from .models import Car, Auction

class CarFilter(FilterSet):
    class Meta:
        model = Car
        fields = {
            'brand': ['exact', 'icontains'],
            'model': ['exact', 'icontains'],
            'year': ['exact', 'gt', 'lt'],
            'fuel_type': ['exact'],
            'transmission': ['exact'],
            'condition': ['exact'],
            'mileage': ['exact', 'lte', 'gte'],
            'price': ['exact', 'gte', 'lte'],
        }

class AuctionFilter(FilterSet):
    class Meta:
        model = Auction
        fields = {
            'status': ['exact'],
            'car__brand': ['exact', 'icontains'],
            'car__model': ['exact', 'icontains'],
            'current_price': ['gte', 'lte'],
            'end_time': ['gte', 'lte'],
        }