# Тесты проекта (Avto - Car Rental API)
#
# Два типа тестов:
#   TestCase   — тесты моделей (проверка логики прямо на уровне Django-моделей)
#   APITestCase — тесты API-эндпоинтов (отправляют реальные HTTP-запросы)
#
# APITestCase использует JWT-токены: для авторизации в тесте нужно получить
# токены через get_tokens(user) и передать их в заголовке HTTP_AUTHORIZATION.
#
# Запуск:  python manage.py test

import io
from datetime import date, timedelta

from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone
from PIL import Image
from rest_framework import status
from rest_framework.test import APITestCase
from rest_framework_simplejwt.tokens import RefreshToken

from .models import User, Car, CarImage, CarUnavailableDate, Rental, Feedback, Favorite, Chat, ChatMessage, Complaint, VerificationCode, AuditLog


def get_tokens(user):
    # Генерирует пару JWT-токенов (access + refresh) для авторизации в тестах.
    # Возвращает словарь, который можно передать в заголовок HTTP_AUTHORIZATION.
    refresh = RefreshToken.for_user(user)
    return {
        'access': str(refresh.access_token),
        'refresh': str(refresh),
    }


def create_test_image():
    # Создаёт валидную картинку в памяти (без файла на диске)
    # для тестов загрузки фотографий (multipart-запросы).
    file = io.BytesIO()
    Image.new('RGB', (100, 100), color='red').save(file, 'jpeg')
    file.seek(0)
    return SimpleUploadedFile('test.jpg', file.read(), content_type='image/jpeg')


class UserModelTests(TestCase):
    # Тесты модели User: роли (renter/owner), вычисляемые поля (возраст, стаж)
    def test_create_renter(self):
        user = User.objects.create_user(username='renter1', password='pass123', email='r@t.com')
        self.assertTrue(user.is_renter)
        self.assertFalse(user.is_owner)
        self.assertFalse(user.is_staff)

    def test_create_owner(self):
        user = User.objects.create_user(username='owner1', password='pass123', is_owner=True)
        self.assertTrue(user.is_renter)
        self.assertTrue(user.is_owner)

    def test_age_property(self):
        user = User.objects.create_user(username='u1', password='pass123', date_of_birth=date(2000, 6, 15))
        expected = date.today().year - 2000 - ((date.today().month, date.today().day) < (6, 15))
        self.assertEqual(user.age, expected)

    def test_age_none(self):
        user = User.objects.create_user(username='u2', password='pass123')
        self.assertIsNone(user.age)

    def test_driving_experience(self):
        user = User.objects.create_user(username='u3', password='pass123', driving_license_date=date(2020, 1, 1))
        expected = max(0, date.today().year - 2020)
        self.assertEqual(user.driving_experience, expected)

    def test_str(self):
        user = User.objects.create_user(username='testuser', password='pass123')
        self.assertEqual(str(user), 'testuser')


class CarModelTests(TestCase):
    # Тесты модели Car: создание, средний рейтинг из отзывов, __str__

    def setUp(self):
        # Общий владелец для всех тестов класса
        self.owner = User.objects.create_user(username='owner', password='pass123', is_owner=True)

    def test_create_car(self):
        car = Car.objects.create(
            owner=self.owner, brand='Toyota', model_name='Camry', year=2020,
            fuel_type='petrol', transmission='auto', mileage=50000,
            price_per_day=50, description='Nice car', location='Moscow'
        )
        self.assertEqual(str(car), 'Toyota Camry (2020)')
        self.assertTrue(car.is_available)

    def test_average_rating_no_feedback(self):
        car = Car.objects.create(
            owner=self.owner, brand='Toyota', model_name='Camry', year=2020,
            fuel_type='petrol', transmission='auto', mileage=50000,
            price_per_day=50, description='Nice car', location='Moscow'
        )
        self.assertIsNone(car.average_rating)

    def test_average_rating_with_feedback(self):
        car = Car.objects.create(
            owner=self.owner, brand='Toyota', model_name='Camry', year=2020,
            fuel_type='petrol', transmission='auto', mileage=50000,
            price_per_day=50, description='Nice car', location='Moscow'
        )
        renter1 = User.objects.create_user(username='renter1', password='pass123')
        renter2 = User.objects.create_user(username='renter2', password='pass123')
        rental1 = Rental.objects.create(
            car=car, renter=renter1, start_date=date(2024, 1, 1),
            end_date=date(2024, 1, 5), total_price=250, status='completed'
        )
        rental2 = Rental.objects.create(
            car=car, renter=renter2, start_date=date(2024, 2, 1),
            end_date=date(2024, 2, 5), total_price=250, status='completed'
        )
        Feedback.objects.create(rental=rental1, feedback_type='car', author=renter1, rating=4, comment='Good')
        Feedback.objects.create(rental=rental2, feedback_type='car', author=renter2, rating=5, comment='Great')
        self.assertEqual(car.average_rating, 4.5)

    def test_car_ordering(self):
        Car.objects.create(
            owner=self.owner, brand='A', model_name='A', year=2020,
            fuel_type='petrol', transmission='auto', mileage=0,
            price_per_day=10, description='', location='Moscow'
        )
        Car.objects.create(
            owner=self.owner, brand='B', model_name='B', year=2020,
            fuel_type='petrol', transmission='auto', mileage=0,
            price_per_day=10, description='', location='Moscow'
        )
        self.assertEqual(Car.objects.count(), 2)


class RentalModelTests(TestCase):
    # Тесты модели Rental: создание аренды и статус по умолчанию (pending)

    def setUp(self):
        self.owner = User.objects.create_user(username='owner', password='pass123', is_owner=True)
        self.renter = User.objects.create_user(username='renter', password='pass123')
        self.car = Car.objects.create(
            owner=self.owner, brand='Toyota', model_name='Camry', year=2020,
            fuel_type='petrol', transmission='auto', mileage=50000,
            price_per_day=50, description='', location='Moscow'
        )

    def test_create_rental(self):
        rental = Rental.objects.create(
            car=self.car, renter=self.renter,
            start_date=date(2025, 1, 1), end_date=date(2025, 1, 5),
            total_price=250, status='pending'
        )
        self.assertEqual(str(rental), 'renter → Toyota Camry (2020) (pending)')

    def test_rental_default_status(self):
        rental = Rental.objects.create(
            car=self.car, renter=self.renter,
            start_date=date(2025, 1, 1), end_date=date(2025, 1, 5),
            total_price=250
        )
        self.assertEqual(rental.status, 'pending')


class AuthAPITests(APITestCase):
    # Тесты авторизации: регистрация, логин, логаут, обновление JWT-токена
    def test_register(self):
        data = {'username': 'newuser', 'email': 'new@t.com', 'password': 'testpass123', 'is_owner': True}
        response = self.client.post(reverse('register'), data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn('username', response.data)
        self.assertTrue(User.objects.filter(username='newuser').exists())

    def test_register_duplicate_email(self):
        User.objects.create_user(username='existing', email='dup@t.com', password='pass123')
        data = {'username': 'newuser', 'email': 'dup@t.com', 'password': 'testpass123'}
        response = self.client.post(reverse('register'), data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_login_success(self):
        User.objects.create_user(username='testuser', password='testpass123', email='t@t.com')
        response = self.client.post(reverse('login'), {'username': 'testuser', 'password': 'testpass123'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('access', response.data)
        self.assertIn('refresh', response.data)

    def test_login_wrong_password(self):
        User.objects.create_user(username='testuser', password='testpass123', email='t@t.com')
        response = self.client.post(reverse('login'), {'username': 'testuser', 'password': 'wrong'})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_login_wrong_username(self):
        response = self.client.post(reverse('login'), {'username': 'nouser', 'password': 'testpass123'})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_logout(self):
        user = User.objects.create_user(username='testuser', password='testpass123', email='t@t.com')
        tokens = get_tokens(user)
        response = self.client.post(reverse('logout'), {'refresh': tokens['refresh']},
                                    HTTP_AUTHORIZATION=f'Bearer {tokens["access"]}')
        self.assertEqual(response.status_code, status.HTTP_205_RESET_CONTENT)

    def test_logout_invalid_token(self):
        user = User.objects.create_user(username='testuser', password='testpass123', email='t@t.com')
        tokens = get_tokens(user)
        response = self.client.post(reverse('logout'), {'refresh': 'invalidtoken'},
                                    HTTP_AUTHORIZATION=f'Bearer {tokens["access"]}')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_token_refresh(self):
        user = User.objects.create_user(username='testuser', password='testpass123', email='t@t.com')
        tokens = get_tokens(user)
        response = self.client.post(reverse('token_refresh'), {'refresh': tokens['refresh']})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('access', response.data)


class UserProfileAPITests(APITestCase):
    # Тесты профиля: получение своих данных, редактирование,
    # запрет на редактирование чужого профиля (404)

    def setUp(self):
        self.user = User.objects.create_user(username='testuser', password='testpass123', email='t@t.com')
        self.tokens = get_tokens(self.user)

    def test_get_profile(self):
        response = self.client.get(reverse('users_list'),
                                   HTTP_AUTHORIZATION=f'Bearer {self.tokens["access"]}')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data[0]['username'], 'testuser')

    def test_get_profile_unauthorized(self):
        response = self.client.get(reverse('users_list'))
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_update_profile(self):
        response = self.client.patch(f'/users/{self.user.id}/',
                                     {'first_name': 'John'},
                                     HTTP_AUTHORIZATION=f'Bearer {self.tokens["access"]}',
                                     format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['first_name'], 'John')

    def test_update_other_user_profile(self):
        other = User.objects.create_user(username='other', password='pass123', email='o@t.com')
        response = self.client.patch(f'/users/{other.id}/',
                                     {'first_name': 'Hacker'},
                                     HTTP_AUTHORIZATION=f'Bearer {self.tokens["access"]}',
                                     format='json')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)


class CarAPITests(APITestCase):
    # Тесты CRUD автомобилей: создание (только owner), редактирование (только владелец),
    # поиск, фильтрация, удаление

    def setUp(self):
        self.owner = User.objects.create_user(username='owner', password='pass123', email='o@t.com', is_owner=True)
        self.renter = User.objects.create_user(username='renter', password='pass123', email='r@t.com')
        self.owner_tokens = get_tokens(self.owner)
        self.renter_tokens = get_tokens(self.renter)
        self.car_data = {
            'brand': 'Toyota', 'model_name': 'Camry', 'year': 2020,
            'fuel_type': 'petrol', 'transmission': 'auto', 'mileage': 50000,
            'price_per_day': 50, 'description': 'Nice car', 'location': 'Moscow'
        }
        self.car = Car.objects.create(owner=self.owner, **self.car_data)

    def test_list_cars(self):
        response = self.client.get(reverse('car_list'))
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_create_car_as_owner(self):
        response = self.client.post(reverse('car_list'), self.car_data,
                                    HTTP_AUTHORIZATION=f'Bearer {self.owner_tokens["access"]}',
                                    format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_create_car_as_renter(self):
        response = self.client.post(reverse('car_list'), self.car_data,
                                    HTTP_AUTHORIZATION=f'Bearer {self.renter_tokens["access"]}',
                                    format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_create_car_unauthorized(self):
        response = self.client.post(reverse('car_list'), self.car_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_owner_cars_list(self):
        response = self.client.get(reverse('car_owner_list'),
                                   HTTP_AUTHORIZATION=f'Bearer {self.owner_tokens["access"]}')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)

    def test_update_own_car(self):
        response = self.client.patch(f'/car/{self.car.id}/', {'price_per_day': 100},
                                     HTTP_AUTHORIZATION=f'Bearer {self.owner_tokens["access"]}',
                                     format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_update_other_car(self):
        other_owner = User.objects.create_user(username='owner2', password='pass123', is_owner=True)
        other_tokens = get_tokens(other_owner)
        response = self.client.patch(f'/car/{self.car.id}/', {'price_per_day': 100},
                                     HTTP_AUTHORIZATION=f'Bearer {other_tokens["access"]}',
                                     format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_delete_own_car(self):
        car = Car.objects.create(owner=self.owner, brand='BMW', model_name='X5', year=2021,
                                 fuel_type='diesel', transmission='auto', mileage=0,
                                 price_per_day=100, description='', location='Moscow')
        response = self.client.delete(f'/car/{car.id}/',
                                      HTTP_AUTHORIZATION=f'Bearer {self.owner_tokens["access"]}')
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

    def test_search_cars(self):
        Car.objects.create(owner=self.owner, brand='BMW', model_name='X5', year=2021,
                           fuel_type='diesel', transmission='auto', mileage=30000,
                           price_per_day=100, description='Luxury SUV', location='SPB')
        response = self.client.get(f'{reverse("car_list")}?search=BMW')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertGreaterEqual(len(response.data['results']), 1)

    def test_filter_by_fuel(self):
        response = self.client.get(f'{reverse("car_list")}?fuel_type=petrol')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_car_detail(self):
        response = self.client.get(f'/car/{self.car.id}/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['brand'], 'Toyota')

    def test_car_detail_not_found(self):
        response = self.client.get('/car/99999/')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)


class CarImageAPITests(APITestCase):
    # Тесты загрузки фотографий: одиночная, массовая (bulk), удаление.
    # Проверяется, что чужие пользователи не могут загружать/удалять фото

    def setUp(self):
        self.owner = User.objects.create_user(username='owner', password='pass123', is_owner=True)
        self.renter = User.objects.create_user(username='renter', password='pass123')
        self.owner_tokens = get_tokens(self.owner)
        self.renter_tokens = get_tokens(self.renter)
        self.car = Car.objects.create(
            owner=self.owner, brand='Toyota', model_name='Camry', year=2020,
            fuel_type='petrol', transmission='auto', mileage=50000,
            price_per_day=50, description='', location='Moscow'
        )

    def test_upload_image(self):
        img = create_test_image()
        response = self.client.post(reverse('car_image_upload'),
                                    {'car_id': self.car.id, 'image': img},
                                    HTTP_AUTHORIZATION=f'Bearer {self.owner_tokens["access"]}',
                                    format='multipart')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_upload_image_not_owner(self):
        img = create_test_image()
        response = self.client.post(reverse('car_image_upload'),
                                    {'car_id': self.car.id, 'image': img},
                                    HTTP_AUTHORIZATION=f'Bearer {self.renter_tokens["access"]}',
                                    format='multipart')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_bulk_upload_images(self):
        img1 = create_test_image()
        img2 = create_test_image()
        response = self.client.post(reverse('car_image_bulk_upload'),
                                    {'car_id': self.car.id, 'images': [img1, img2]},
                                    HTTP_AUTHORIZATION=f'Bearer {self.owner_tokens["access"]}',
                                    format='multipart')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(len(response.data), 2)

    def test_delete_image(self):
        car_image = CarImage.objects.create(car=self.car, image=create_test_image())
        response = self.client.delete(f'/car/image/{car_image.id}/',
                                      HTTP_AUTHORIZATION=f'Bearer {self.owner_tokens["access"]}')
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

    def test_delete_image_not_owner(self):
        car_image = CarImage.objects.create(car=self.car, image=create_test_image())
        response = self.client.delete(f'/car/image/{car_image.id}/',
                                      HTTP_AUTHORIZATION=f'Bearer {self.renter_tokens["access"]}')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)


class RentalAPITests(APITestCase):
    # Тесты аренды: создание заявки, проверка дат, пересечение броней,
    # подтверждение/отклонение/завершение владельцем или арендатором

    def setUp(self):
        self.owner = User.objects.create_user(username='owner', password='pass123', is_owner=True, email='o@t.com')
        self.renter = User.objects.create_user(username='renter', password='pass123', email='r@t.com')
        self.owner_tokens = get_tokens(self.owner)
        self.renter_tokens = get_tokens(self.renter)
        self.car = Car.objects.create(
            owner=self.owner, brand='Toyota', model_name='Camry', year=2020,
            fuel_type='petrol', transmission='auto', mileage=50000,
            price_per_day=50, description='', location='Moscow'
        )
        self.rental_data = {
            'car_id': self.car.id,
            'start_date': (date.today() + timedelta(days=30)).isoformat(),
            'end_date': (date.today() + timedelta(days=35)).isoformat(),
        }

    def test_create_rental(self):
        response = self.client.post(reverse('rental_list'), self.rental_data,
                                    HTTP_AUTHORIZATION=f'Bearer {self.renter_tokens["access"]}',
                                    format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_create_rental_unauthorized(self):
        response = self.client.post(reverse('rental_list'), self.rental_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_create_rental_past_date(self):
        data = {**self.rental_data, 'start_date': (date.today() - timedelta(days=1)).isoformat()}
        response = self.client.post(reverse('rental_list'), data,
                                    HTTP_AUTHORIZATION=f'Bearer {self.renter_tokens["access"]}',
                                    format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_confirm_rental(self):
        rental = Rental.objects.create(
            car=self.car, renter=self.renter,
            start_date=date.today() + timedelta(days=30),
            end_date=date.today() + timedelta(days=35),
            total_price=300, status='pending'
        )
        response = self.client.post(f'/rental/{rental.id}/confirm/',
                                    HTTP_AUTHORIZATION=f'Bearer {self.owner_tokens["access"]}')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        rental.refresh_from_db()
        self.assertEqual(rental.status, 'confirmed')

    def test_confirm_not_owner(self):
        rental = Rental.objects.create(
            car=self.car, renter=self.renter,
            start_date=date.today() + timedelta(days=30),
            end_date=date.today() + timedelta(days=35),
            total_price=300, status='pending'
        )
        response = self.client.post(f'/rental/{rental.id}/confirm/',
                                    HTTP_AUTHORIZATION=f'Bearer {self.renter_tokens["access"]}')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_reject_rental(self):
        rental = Rental.objects.create(
            car=self.car, renter=self.renter,
            start_date=date.today() + timedelta(days=30),
            end_date=date.today() + timedelta(days=35),
            total_price=300, status='pending'
        )
        response = self.client.post(f'/rental/{rental.id}/reject/',
                                    HTTP_AUTHORIZATION=f'Bearer {self.owner_tokens["access"]}')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        rental.refresh_from_db()
        self.assertEqual(rental.status, 'canceled')

    def test_complete_rental(self):
        rental = Rental.objects.create(
            car=self.car, renter=self.renter,
            start_date=date.today() - timedelta(days=5),
            end_date=date.today() - timedelta(days=1),
            total_price=300, status='active'
        )
        response = self.client.post(f'/rental/{rental.id}/complete/',
                                    HTTP_AUTHORIZATION=f'Bearer {self.renter_tokens["access"]}')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        rental.refresh_from_db()
        self.assertEqual(rental.status, 'completed')

    def test_complete_rental_not_renter(self):
        rental = Rental.objects.create(
            car=self.car, renter=self.renter,
            start_date=date.today() - timedelta(days=5),
            end_date=date.today() - timedelta(days=1),
            total_price=300, status='active'
        )
        response = self.client.post(f'/rental/{rental.id}/complete/',
                                    HTTP_AUTHORIZATION=f'Bearer {self.owner_tokens["access"]}')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_create_rental_overlapping_dates(self):
        Rental.objects.create(
            car=self.car, renter=self.renter,
            start_date=date.today() + timedelta(days=28),
            end_date=date.today() + timedelta(days=32),
            total_price=250, status='confirmed'
        )
        response = self.client.post(reverse('rental_list'), self.rental_data,
                                    HTTP_AUTHORIZATION=f'Bearer {self.renter_tokens["access"]}',
                                    format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_rental_price_hidden_from_admin(self):
        # Админ не видит цены аренды (финансы пользователей анонимны)
        admin = User.objects.create_user(username='admin', password='pass123', is_staff=True)
        admin_tokens = get_tokens(admin)
        Rental.objects.create(
            car=self.car, renter=self.renter,
            start_date=date.today() + timedelta(days=30),
            end_date=date.today() + timedelta(days=35),
            total_price=300, status='pending'
        )
        response = self.client.get(reverse('rental_list'),
                                   HTTP_AUTHORIZATION=f'Bearer {admin_tokens["access"]}')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertNotIn('total_price', response.data['results'][0])

    def test_rental_price_visible_to_participants(self):
        # Участник (арендатор) видит цену своей аренды
        Rental.objects.create(
            car=self.car, renter=self.renter,
            start_date=date.today() + timedelta(days=30),
            end_date=date.today() + timedelta(days=35),
            total_price=300, status='pending'
        )
        response = self.client.get(reverse('rental_list'),
                                   HTTP_AUTHORIZATION=f'Bearer {self.renter_tokens["access"]}')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('total_price', response.data['results'][0])


class FeedbackAPITests(APITestCase):
    # Тесты отзывов: создание (только участники завершённой аренды),
    # запрет дублей и удаление (только автор или админ)

    def setUp(self):
        self.owner = User.objects.create_user(username='owner', password='pass123', is_owner=True, email='o@t.com')
        self.renter = User.objects.create_user(username='renter', password='pass123', email='r@t.com')
        self.owner_tokens = get_tokens(self.owner)
        self.renter_tokens = get_tokens(self.renter)
        self.car = Car.objects.create(
            owner=self.owner, brand='Toyota', model_name='Camry', year=2020,
            fuel_type='petrol', transmission='auto', mileage=50000,
            price_per_day=50, description='', location='Moscow'
        )
        self.rental = Rental.objects.create(
            car=self.car, renter=self.renter,
            start_date=date.today() - timedelta(days=10),
            end_date=date.today() - timedelta(days=5),
            total_price=300, status='completed'
        )

    def test_create_feedback_car(self):
        response = self.client.post(reverse('feedbacks-list'), {
            'rental_id': self.rental.id, 'feedback_type': 'car',
            'rating': 5, 'comment': 'Excellent!'
        }, HTTP_AUTHORIZATION=f'Bearer {self.renter_tokens["access"]}', format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_create_feedback_renter(self):
        response = self.client.post(reverse('feedbacks-list'), {
            'rental_id': self.rental.id, 'feedback_type': 'renter',
            'rating': 4, 'comment': 'Good renter'
        }, HTTP_AUTHORIZATION=f'Bearer {self.owner_tokens["access"]}', format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_create_feedback_not_participant(self):
        stranger = User.objects.create_user(username='stranger', password='pass123', email='s@t.com')
        stranger_tokens = get_tokens(stranger)
        response = self.client.post(reverse('feedbacks-list'), {
            'rental_id': self.rental.id, 'feedback_type': 'car',
            'rating': 5, 'comment': 'Hack'
        }, HTTP_AUTHORIZATION=f'Bearer {stranger_tokens["access"]}', format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_create_feedback_not_completed(self):
        active_rental = Rental.objects.create(
            car=self.car, renter=self.renter,
            start_date=date.today(), end_date=date.today() + timedelta(days=3),
            total_price=200, status='active'
        )
        response = self.client.post(reverse('feedbacks-list'), {
            'rental_id': active_rental.id, 'feedback_type': 'car',
            'rating': 5, 'comment': 'Too soon'
        }, HTTP_AUTHORIZATION=f'Bearer {self.renter_tokens["access"]}', format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_duplicate_feedback(self):
        Feedback.objects.create(rental=self.rental, feedback_type='car', author=self.renter, rating=5, comment='Nice')
        response = self.client.post(reverse('feedbacks-list'), {
            'rental_id': self.rental.id, 'feedback_type': 'car',
            'rating': 4, 'comment': 'Duplicate'
        }, HTTP_AUTHORIZATION=f'Bearer {self.renter_tokens["access"]}', format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_delete_feedback_by_author(self):
        # Автор отзыва может удалить свой отзыв
        fb = Feedback.objects.create(rental=self.rental, feedback_type='car', author=self.renter, rating=5, comment='Nice')
        response = self.client.delete(f'/feedback/{fb.id}/',
                                      HTTP_AUTHORIZATION=f'Bearer {self.renter_tokens["access"]}')
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Feedback.objects.filter(id=fb.id).exists())

    def test_delete_feedback_not_author(self):
        # Участник аренды, но НЕ автор (владелец машины) не может удалить чужой отзыв
        fb = Feedback.objects.create(rental=self.rental, feedback_type='car', author=self.renter, rating=5, comment='Nice')
        response = self.client.delete(f'/feedback/{fb.id}/',
                                      HTTP_AUTHORIZATION=f'Bearer {self.owner_tokens["access"]}')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertTrue(Feedback.objects.filter(id=fb.id).exists())

    def test_delete_feedback_by_admin(self):
        # Администратор может удалить любой отзыв
        admin = User.objects.create_user(username='admin', password='pass123', is_staff=True)
        admin_tokens = get_tokens(admin)
        fb = Feedback.objects.create(rental=self.rental, feedback_type='car', author=self.renter, rating=5, comment='Nice')
        response = self.client.delete(f'/feedback/{fb.id}/',
                                      HTTP_AUTHORIZATION=f'Bearer {admin_tokens["access"]}')
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

    def test_update_feedback_not_author(self):
        # Участник аренды, но НЕ автор (владелец машины) не может редактировать чужой отзыв
        fb = Feedback.objects.create(rental=self.rental, feedback_type='car', author=self.renter, rating=5, comment='Nice')
        response = self.client.patch(f'/feedback/{fb.id}/', {'rating': 1},
                                     HTTP_AUTHORIZATION=f'Bearer {self.owner_tokens["access"]}', format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        fb.refresh_from_db()
        self.assertEqual(fb.rating, 5)


class FavoriteAPITests(APITestCase):
    # Тесты избранного: добавление, запрет дублей, список, удаление

    def setUp(self):
        self.user = User.objects.create_user(username='user', password='pass123')
        self.tokens = get_tokens(self.user)
        self.owner = User.objects.create_user(username='owner', password='pass123', is_owner=True)
        self.car = Car.objects.create(
            owner=self.owner, brand='Toyota', model_name='Camry', year=2020,
            fuel_type='petrol', transmission='auto', mileage=50000,
            price_per_day=50, description='', location='Moscow'
        )

    def test_add_favorite(self):
        response = self.client.post(reverse('favorites_list'), {'car_id': self.car.id},
                                    HTTP_AUTHORIZATION=f'Bearer {self.tokens["access"]}', format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_add_duplicate_favorite(self):
        Favorite.objects.create(user=self.user, car=self.car)
        response = self.client.post(reverse('favorites_list'), {'car_id': self.car.id},
                                    HTTP_AUTHORIZATION=f'Bearer {self.tokens["access"]}', format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_list_favorites(self):
        Favorite.objects.create(user=self.user, car=self.car)
        response = self.client.get(reverse('favorites_list'),
                                   HTTP_AUTHORIZATION=f'Bearer {self.tokens["access"]}')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)

    def test_delete_favorite(self):
        fav = Favorite.objects.create(user=self.user, car=self.car)
        response = self.client.delete(f'/favorites/{fav.id}/',
                                      HTTP_AUTHORIZATION=f'Bearer {self.tokens["access"]}')
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)


class ChatAPITests(APITestCase):
    # Тесты чата: список чатов участника, детали чата, отправка сообщений
    # (и запрет писать тем, кто не участвует в аренде)

    def setUp(self):
        self.owner = User.objects.create_user(username='owner', password='pass123', is_owner=True, email='o@t.com')
        self.renter = User.objects.create_user(username='renter', password='pass123', email='r@t.com')
        self.owner_tokens = get_tokens(self.owner)
        self.renter_tokens = get_tokens(self.renter)
        self.car = Car.objects.create(
            owner=self.owner, brand='Toyota', model_name='Camry', year=2020,
            fuel_type='petrol', transmission='auto', mileage=50000,
            price_per_day=50, description='', location='Moscow'
        )
        self.rental = Rental.objects.create(
            car=self.car, renter=self.renter,
            start_date=date.today() + timedelta(days=30),
            end_date=date.today() + timedelta(days=35),
            total_price=300, status='pending'
        )
        self.chat = self.rental.chat

    def test_list_chats(self):
        response = self.client.get(reverse('chat_list'),
                                   HTTP_AUTHORIZATION=f'Bearer {self.owner_tokens["access"]}')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)

    def test_send_message(self):
        response = self.client.post(reverse('chat_message_create'),
                                    {'chat_id': self.chat.id, 'message': 'Hello!'},
                                    HTTP_AUTHORIZATION=f'Bearer {self.renter_tokens["access"]}',
                                    format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_send_message_not_participant(self):
        stranger = User.objects.create_user(username='stranger', password='pass123', email='s@t.com')
        stranger_tokens = get_tokens(stranger)
        response = self.client.post(reverse('chat_message_create'),
                                    {'chat_id': self.chat.id, 'message': 'Spam'},
                                    HTTP_AUTHORIZATION=f'Bearer {stranger_tokens["access"]}',
                                    format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_chat_detail(self):
        response = self.client.get(f'/chat/{self.chat.id}/',
                                   HTTP_AUTHORIZATION=f'Bearer {self.owner_tokens["access"]}')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('messages', response.data)


class ComplaintAPITests(APITestCase):
    # Тесты жалоб: создание, список своих жалоб, обязательная авторизация

    def setUp(self):
        self.user = User.objects.create_user(username='user', password='pass123', email='u@t.com')
        self.target = User.objects.create_user(username='target', password='pass123', email='t@t.com')
        self.tokens = get_tokens(self.user)

    def test_create_complaint(self):
        response = self.client.post(reverse('complaints_list'), {
            'target_user_id': self.target.id,
            'reason': 'Spam',
            'description': 'Sending spam messages'
        }, HTTP_AUTHORIZATION=f'Bearer {self.tokens["access"]}', format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_list_complaints(self):
        Complaint.objects.create(author=self.user, target_user=self.target, reason='Spam', description='x')
        response = self.client.get(reverse('complaints_list'),
                                   HTTP_AUTHORIZATION=f'Bearer {self.tokens["access"]}')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)

    def test_create_complaint_unauthorized(self):
        response = self.client.post(reverse('complaints_list'), {
            'target_user_id': self.target.id,
            'reason': 'Spam',
            'description': 'x'
        }, format='json')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class VerificationAPITests(APITestCase):
    # Тесты верификации email/телефона: отправка кода и подтверждение
    # (проверяется, что флаг email_verified становится True)

    def setUp(self):
        self.user = User.objects.create_user(username='user', password='pass123', email='u@t.com')
        self.tokens = get_tokens(self.user)

    def test_send_verification(self):
        response = self.client.post(reverse('send_verification'), {'verification_type': 'email'},
                                    HTTP_AUTHORIZATION=f'Bearer {self.tokens["access"]}', format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_confirm_verification(self):
        code = VerificationCode.objects.create(
            user=self.user, code='123456', verification_type='email',
            expires_at=timezone.now() + timedelta(minutes=10)
        )
        response = self.client.post(reverse('confirm_verification'),
                                    {'verification_type': 'email', 'code': '123456'},
                                    HTTP_AUTHORIZATION=f'Bearer {self.tokens["access"]}', format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.user.refresh_from_db()
        self.assertTrue(self.user.email_verified)

    def test_confirm_wrong_code(self):
        VerificationCode.objects.create(
            user=self.user, code='123456', verification_type='email',
            expires_at=timezone.now() + timedelta(minutes=10)
        )
        response = self.client.post(reverse('confirm_verification'),
                                    {'verification_type': 'email', 'code': '000000'},
                                    HTTP_AUTHORIZATION=f'Bearer {self.tokens["access"]}', format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class PasswordResetAPITests(APITestCase):
    # Тесты сброса пароля: запрос кода на email, подтверждение кода
    # и смена пароля (проверяется, что новый пароль работает)

    def setUp(self):
        self.user = User.objects.create_user(username='user', password='pass123', email='u@t.com')
        self.user2 = User.objects.create_user(username='user2', password='pass123', email='u2@t.com')

    def test_password_reset_request(self):
        response = self.client.post(reverse('password_reset'), {'email': 'u@t.com'}, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_password_reset_request_nonexistent_email(self):
        response = self.client.post(reverse('password_reset'), {'email': 'no@t.com'}, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_password_reset_confirm(self):
        VerificationCode.objects.create(
            user=self.user, code='654321', verification_type='password_reset',
            expires_at=timezone.now() + timedelta(minutes=10)
        )
        response = self.client.post(reverse('password_reset_confirm'), {
            'email': 'u@t.com', 'code': '654321', 'new_password': 'newpass123'
        }, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password('newpass123'))

    def test_password_reset_wrong_code(self):
        VerificationCode.objects.create(
            user=self.user, code='654321', verification_type='password_reset',
            expires_at=timezone.now() + timedelta(minutes=10)
        )
        response = self.client.post(reverse('password_reset_confirm'), {
            'email': 'u@t.com', 'code': '000000', 'new_password': 'newpass123'
        }, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class CalendarAPITests(APITestCase):
    # Тесты календаря доступности: отдаёт статус каждого дня месяца (free/booked/blocked/past)

    def setUp(self):
        self.owner = User.objects.create_user(username='owner', password='pass123', is_owner=True)
        self.car = Car.objects.create(
            owner=self.owner, brand='Toyota', model_name='Camry', year=2020,
            fuel_type='petrol', transmission='auto', mileage=50000,
            price_per_day=50, description='', location='Moscow'
        )

    def test_calendar(self):
        now = timezone.now()
        response = self.client.get(f'/car/{self.car.id}/calendar/?year={now.year}&month={now.month}')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('days', response.data)

    def test_calendar_not_found(self):
        response = self.client.get('/car/99999/calendar/')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)


class AvailableCarAPITests(APITestCase):
    # Тесты поиска свободных машин по датам:
    # машина с бронью на эти даты не должна попадать в выдачу

    def setUp(self):
        self.owner = User.objects.create_user(username='owner', password='pass123', is_owner=True)
        self.car = Car.objects.create(
            owner=self.owner, brand='Toyota', model_name='Camry', year=2020,
            fuel_type='petrol', transmission='auto', mileage=50000,
            price_per_day=50, description='', location='Moscow'
        )

    def test_available_cars(self):
        start = date.today() + timedelta(days=30)
        end = date.today() + timedelta(days=35)
        response = self.client.get(
            f'{reverse("car_available")}?start_date={start.isoformat()}&end_date={end.isoformat()}'
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn(self.car.id, [c['id'] for c in response.data['results']])

    def test_available_cars_booked_excluded(self):
        renter = User.objects.create_user(username='renter', password='pass123')
        start = date.today() + timedelta(days=30)
        end = date.today() + timedelta(days=35)
        Rental.objects.create(
            car=self.car, renter=renter,
            start_date=start, end_date=end,
            total_price=300, status='confirmed'
        )
        response = self.client.get(
            f'{reverse("car_available")}?start_date={start.isoformat()}&end_date={end.isoformat()}'
        )
        self.assertNotIn(self.car.id, [c['id'] for c in response.data['results']])


class StatsAPITests(APITestCase):
    # Тесты статистики: глобальная доступна всем,
    # статистика владельца — только пользователям с is_owner=True

    def test_global_stats(self):
        response = self.client.get(reverse('stats'))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('cars_total', response.data)
        self.assertIn('users_total', response.data)

    def test_owner_stats(self):
        owner = User.objects.create_user(username='owner', password='pass123', is_owner=True)
        tokens = get_tokens(owner)
        response = self.client.get(reverse('owner_stats'),
                                   HTTP_AUTHORIZATION=f'Bearer {tokens["access"]}')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('total_earnings', response.data)

    def test_owner_stats_forbidden_for_renter(self):
        renter = User.objects.create_user(username='renter', password='pass123')
        tokens = get_tokens(renter)
        response = self.client.get(reverse('owner_stats'),
                                   HTTP_AUTHORIZATION=f'Bearer {tokens["access"]}')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)


class CarUnavailableDateAPITests(APITestCase):
    # Тесты заблокированных дат: владелец может заблокировать дни своей машины

    def setUp(self):
        self.owner = User.objects.create_user(username='owner', password='pass123', is_owner=True)
        self.owner_tokens = get_tokens(self.owner)
        self.car = Car.objects.create(
            owner=self.owner, brand='Toyota', model_name='Camry', year=2020,
            fuel_type='petrol', transmission='auto', mileage=50000,
            price_per_day=50, description='', location='Moscow'
        )

    def test_block_dates(self):
        start = date.today() + timedelta(days=20)
        end = date.today() + timedelta(days=25)
        response = self.client.post(f'/car/{self.car.id}/unavailable/', {
            'start_date': start.isoformat(), 'end_date': end.isoformat(), 'reason': 'Maintenance'
        }, HTTP_AUTHORIZATION=f'Bearer {self.owner_tokens["access"]}', format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_list_blocked_dates(self):
        CarUnavailableDate.objects.create(car=self.car, start_date=date(2025, 1, 1), end_date=date(2025, 1, 5))
        response = self.client.get(f'/car/{self.car.id}/unavailable/',
                                   HTTP_AUTHORIZATION=f'Bearer {self.owner_tokens["access"]}')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)


class AdminUserAPITests(APITestCase):
    # Тесты админ-управления пользователями (для дашборда админа во фронте):
    # список, блокировка, верификация, назначение ролей — только для staff

    def setUp(self):
        self.admin = User.objects.create_user(username='admin', password='pass123', is_staff=True)
        self.admin_tokens = get_tokens(self.admin)
        self.user = User.objects.create_user(username='user', password='pass123', email='u@t.com')

    def test_admin_list_users(self):
        response = self.client.get(reverse('admin_users_list'),
                                   HTTP_AUTHORIZATION=f'Bearer {self.admin_tokens["access"]}')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)

    def test_admin_users_forbidden_for_regular_user(self):
        user_tokens = get_tokens(self.user)
        response = self.client.get(reverse('admin_users_list'),
                                   HTTP_AUTHORIZATION=f'Bearer {user_tokens["access"]}')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_admin_block_user(self):
        # Блокировка = is_active: False (пользователь не сможет зайти)
        response = self.client.patch(f'/admin/users/{self.user.id}/', {'is_active': False},
                                     HTTP_AUTHORIZATION=f'Bearer {self.admin_tokens["access"]}', format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.user.refresh_from_db()
        self.assertFalse(self.user.is_active)

    def test_admin_verify_user(self):
        # Подтверждение личности
        response = self.client.patch(f'/admin/users/{self.user.id}/', {'is_verified': True},
                                     HTTP_AUTHORIZATION=f'Bearer {self.admin_tokens["access"]}', format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.user.refresh_from_db()
        self.assertTrue(self.user.is_verified)

    def test_admin_assign_owner_role(self):
        # Назначение роли владельца
        response = self.client.patch(f'/admin/users/{self.user.id}/', {'is_owner': True},
                                     HTTP_AUTHORIZATION=f'Bearer {self.admin_tokens["access"]}', format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.user.refresh_from_db()
        self.assertTrue(self.user.is_owner)

    def test_admin_cannot_change_superuser(self):
        # Обычный staff не может менять суперпользователя
        superuser = User.objects.create_superuser(username='root', password='pass123')
        response = self.client.patch(f'/admin/users/{superuser.id}/', {'is_active': False},
                                     HTTP_AUTHORIZATION=f'Bearer {self.admin_tokens["access"]}', format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)


class AdminComplaintAPITests(APITestCase):
    # Тесты: админ может менять статус жалобы и отвечать на неё через API

    def setUp(self):
        self.admin = User.objects.create_user(username='admin', password='pass123', is_staff=True)
        self.admin_tokens = get_tokens(self.admin)
        self.user = User.objects.create_user(username='user', password='pass123', email='u@t.com')
        self.user_tokens = get_tokens(self.user)
        self.target = User.objects.create_user(username='target', password='pass123', email='t@t.com')
        self.complaint = Complaint.objects.create(
            author=self.user, target_user=self.target, reason='Spam', description='x'
        )

    def test_admin_update_complaint_status_and_response(self):
        response = self.client.patch(f'/complaints/{self.complaint.id}/', {
            'status': 'resolved', 'admin_response': 'Мы разобрались'
        }, HTTP_AUTHORIZATION=f'Bearer {self.admin_tokens["access"]}', format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.complaint.refresh_from_db()
        self.assertEqual(self.complaint.status, 'resolved')
        self.assertEqual(self.complaint.admin_response, 'Мы разобрались')

    def test_user_cannot_change_status(self):
        # У обычного пользователя поля status/admin_response — read_only
        response = self.client.patch(f'/complaints/{self.complaint.id}/', {'status': 'resolved'},
                                     HTTP_AUTHORIZATION=f'Bearer {self.user_tokens["access"]}', format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.complaint.refresh_from_db()
        self.assertEqual(self.complaint.status, 'pending')


class AnalyticsAPITests(APITestCase):
    # Тесты аналитики: личный кабинет (свой дашборд) и дашборд админа

    def setUp(self):
        self.owner = User.objects.create_user(username='owner', password='pass123', is_owner=True, email='o@t.com')
        self.owner_tokens = get_tokens(self.owner)
        self.admin = User.objects.create_user(username='admin', password='pass123', is_staff=True)
        self.admin_tokens = get_tokens(self.admin)
        self.renter = User.objects.create_user(username='renter', password='pass123', email='rr@t.com')
        self.car = Car.objects.create(
            owner=self.owner, brand='Toyota', model_name='Camry', year=2020,
            fuel_type='petrol', transmission='auto', mileage=50000,
            price_per_day=50, description='', location='Moscow'
        )
        # Аренда на 5 дней (1-5 января). Status completed — сигналы не создают чат
        self.rental = Rental.objects.create(
            car=self.car, renter=self.renter,
            start_date=date(2025, 1, 1), end_date=date(2025, 1, 5),
            total_price=250, status='completed'
        )

    def test_owner_analytics(self):
        response = self.client.get(reverse('analytics'),
                                   HTTP_AUTHORIZATION=f'Bearer {self.owner_tokens["access"]}')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('rentals_by_status', response.data)
        self.assertIn('revenue_by_month', response.data)
        self.assertIn('cars_by_brand', response.data)
        # Сдаваемость: машина сдавалась 5 дней, 1 аренда
        self.assertIn('cars_rental_days', response.data)
        self.assertEqual(response.data['cars_rental_days'][0]['rental_days'], 5)
        self.assertEqual(response.data['cars_rental_days'][0]['rentals_count'], 1)

    def test_admin_analytics(self):
        response = self.client.get(reverse('admin_analytics'),
                                   HTTP_AUTHORIZATION=f'Bearer {self.admin_tokens["access"]}')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('cars_by_brand', response.data)
        self.assertIn('rental_statuses', response.data)
        # Активность без денег: есть число аренд по месяцам, НЕТ доходов
        self.assertIn('rentals_by_month', response.data)
        self.assertNotIn('revenue_total', response.data)
        self.assertNotIn('revenue_by_month', response.data)
        # Топ машин по дням на всей платформе
        self.assertIn('top_cars_by_days', response.data)
        self.assertEqual(response.data['top_cars_by_days'][0]['rental_days'], 5)
        self.assertEqual(response.data['rental_days_total'], 5)

    def test_admin_analytics_forbidden_for_regular_user(self):
        response = self.client.get(reverse('admin_analytics'),
                                   HTTP_AUTHORIZATION=f'Bearer {self.owner_tokens["access"]}')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)


class OperationsAPITests(APITestCase):
    # Тесты журнала операций: у пользователя — свои, у админа — все

    def setUp(self):
        self.owner = User.objects.create_user(username='owner', password='pass123', is_owner=True, email='o@t.com')
        self.renter = User.objects.create_user(username='renter', password='pass123', email='r@t.com')
        self.admin = User.objects.create_user(username='admin', password='pass123', is_staff=True)
        self.renter_tokens = get_tokens(self.renter)
        self.admin_tokens = get_tokens(self.admin)
        self.car = Car.objects.create(
            owner=self.owner, brand='Toyota', model_name='Camry', year=2020,
            fuel_type='petrol', transmission='auto', mileage=50000,
            price_per_day=50, description='', location='Moscow'
        )
        # Статус completed — чтобы сигналы не создавали чат и не слали уведомления
        self.rental = Rental.objects.create(
            car=self.car, renter=self.renter,
            start_date=date(2025, 1, 1), end_date=date(2025, 1, 5),
            total_price=250, status='completed'
        )

    def test_user_operations(self):
        response = self.client.get(reverse('operations'),
                                   HTTP_AUTHORIZATION=f'Bearer {self.renter_tokens["access"]}')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['type'], 'rental')
        self.assertEqual(response.data[0]['status'], 'completed')

    def test_admin_operations(self):
        response = self.client.get(reverse('admin_operations'),
                                   HTTP_AUTHORIZATION=f'Bearer {self.admin_tokens["access"]}')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data[0]['renter'], 'renter')
        self.assertEqual(response.data[0]['owner'], 'owner')
        # Админ не должен видеть суммы операций (финансы пользователей анонимны)
        self.assertNotIn('amount', response.data[0])

    def test_operations_unauthorized(self):
        response = self.client.get(reverse('operations'))
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class AuditLogAPITests(APITestCase):
    # Тесты журнала аудита: запись при важных действиях и просмотр только админом

    def setUp(self):
        self.admin = User.objects.create_user(username='admin', password='pass123', is_staff=True)
        self.admin_tokens = get_tokens(self.admin)
        self.target = User.objects.create_user(username='target', password='pass123', email='t@t.com')

    def test_admin_list_audit(self):
        response = self.client.get(reverse('admin_audit'),
                                   HTTP_AUTHORIZATION=f'Bearer {self.admin_tokens["access"]}')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('results', response.data)

    def test_audit_forbidden_for_regular_user(self):
        user = User.objects.create_user(username='user', password='pass123')
        tokens = get_tokens(user)
        response = self.client.get(reverse('admin_audit'),
                                   HTTP_AUTHORIZATION=f'Bearer {tokens["access"]}')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_register_creates_audit(self):
        response = self.client.post(reverse('register'), {
            'username': 'newuser', 'email': 'n@t.com', 'password': 'pass123'
        }, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(AuditLog.objects.filter(action='user.registered').exists())

    def test_block_user_creates_audit(self):
        response = self.client.patch(f'/admin/users/{self.target.id}/', {'is_active': False},
                                     HTTP_AUTHORIZATION=f'Bearer {self.admin_tokens["access"]}', format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(AuditLog.objects.filter(action='user.blocked', user=self.admin).exists())

    def test_complaint_status_creates_audit(self):
        complaint = Complaint.objects.create(
            author=self.target, target_user=self.admin, reason='Spam', description='x'
        )
        response = self.client.patch(f'/complaints/{complaint.id}/', {'status': 'resolved'},
                                     HTTP_AUTHORIZATION=f'Bearer {self.admin_tokens["access"]}', format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(AuditLog.objects.filter(action='complaint.status_changed').exists())

    def test_regular_edit_does_not_create_audit(self):
        # Обычное редактирование профиля пользователем НЕ пишется в аудит
        user_tokens = get_tokens(self.target)
        response = self.client.patch(f'/users/{self.target.id}/', {'first_name': 'John'},
                                     HTTP_AUTHORIZATION=f'Bearer {user_tokens["access"]}', format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(AuditLog.objects.count(), 0)
