from django_filters import FilterSet
from .models import Car, Rental


class CarFilter(FilterSet):
    class Meta:
        model = Car
        fields = {
            'brand': ['exact', 'icontains'],
            'model_name': ['exact', 'icontains'],
            'year': ['exact', 'gt', 'lt'],
            'fuel_type': ['exact'],
            'transmission': ['exact'],
            'mileage': ['exact', 'lte', 'gte'],
            'price_per_day': ['exact', 'gte', 'lte'],
            'is_available': ['exact'],
            'owner': ['exact'],
            'location': ['exact', 'icontains'],
        }


class RentalFilter(FilterSet):
    class Meta:
        model = Rental
        fields = {
            'status': ['exact'],
            'car': ['exact'],
            'renter': ['exact'],
            'start_date': ['exact', 'gte', 'lte'],
            'end_date': ['exact', 'gte', 'lte'],
        }
