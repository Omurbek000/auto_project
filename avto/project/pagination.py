# Пагинация — разбивка списков на страницы
# Клиент передаёт ?page=1&page_size=10 для навигации

from rest_framework.pagination import PageNumberPagination


class CarPagination(PageNumberPagination):
    page_size = 10                       # Элементов на странице по умолчанию
    page_size_query_param = "page_size"  # Можно переопределить: ?page_size=20
    max_page_size = 100                  # Максимум элементов на странице


class RentalPagination(PageNumberPagination):
    page_size = 10
    page_size_query_param = "page_size"
    max_page_size = 100


class FeedbackPagination(PageNumberPagination):
    page_size = 10
    page_size_query_param = "page_size"
    max_page_size = 100


class ChatPagination(PageNumberPagination):
    page_size = 10
    page_size_query_param = "page_size"
    max_page_size = 100


class ComplaintPagination(PageNumberPagination):
    page_size = 10
    page_size_query_param = "page_size"
    max_page_size = 100


class AuditLogPagination(PageNumberPagination):
    page_size = 20
    page_size_query_param = "page_size"
    max_page_size = 100


class OperationPagination(PageNumberPagination):
    page_size = 20
    page_size_query_param = "page_size"
    max_page_size = 100
