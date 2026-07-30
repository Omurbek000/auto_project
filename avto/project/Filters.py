# Фильтры для API. Позволяют клиенту сортировать и отбирать данные
# Например: /car/?price_per_day__lte=5000&fuel_type=petrol

from django_filters import FilterSet
from .models import Car, Rental, Feedback


# Фильтр для автомобилей
# Клиент может фильтровать по любому из этих полей
class CarFilter(FilterSet):
    class Meta:
        model = Car
        fields = {
            'brand': ['exact', 'icontains'],             # Точное совпадение или содержит
            'model_name': ['exact', 'icontains'],
            'year': ['exact', 'gt', 'lt'],               # Год: больше (gt) или меньше (lt)
            'fuel_type': ['exact'],
            'transmission': ['exact'],
            'mileage': ['exact', 'lte', 'gte'],          # Пробег: меньше/равно или больше/равно
            'price_per_day': ['exact', 'gte', 'lte'],    # Цена за сутки
            'is_available': ['exact'],
            'owner': ['exact'],
            'location': ['exact', 'icontains'],
        }


# Фильтр для аренды
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


# Фильтр для отзывов
class FeedbackFilter(FilterSet):
    class Meta:
        model = Feedback
        fields = {
            'feedback_type': ['exact'],    # car или renter
            'rating': ['exact', 'gte', 'lte'],  # Оценка 1-5
            'created_date': ['exact', 'gte', 'lte'],
        }
