from django_filters import FilterSet
from .models import Car, Auction, Bid


class CarFilter(FilterSet):
    class Meta:
        model = Car
        fields = {
            'brand': ['exact', 'icontains'],
            'model_name': ['exact', 'icontains'],
            'year': ['exact', 'gt', 'lt'],
            'fuel_type': ['exact'],
            'transmission': ['exact'],
            'condition': ['exact'],
            'mileage': ['exact', 'lte', 'gte'],
            'price': ['exact', 'gte', 'lte'],
            'is_available': ['exact'],
            'seller': ['exact'],
        }


class AuctionFilter(FilterSet):
    class Meta:
        model = Auction
        fields = {
            'status': ['exact'],
            'car__brand': ['exact', 'icontains'],
            'car__model_name': ['exact', 'icontains'],
            'start_price': ['gte', 'lte'],
            'end_time': ['gte', 'lte'],
        }


class BidFilter(FilterSet):
    class Meta:
        model = Bid
        fields = {
            'auction': ['exact'],
            'buyer': ['exact'],
            'amount': ['gte', 'lte'],
        }
