# Права доступа (permissions) — кто может делать какие запросы
# Каждый класс проверяет: есть ли у пользователя доступ к действию
# Здесь только те классы, которые реально используются во views.py

from rest_framework import permissions


# Владелец или админ. Используется для создания/редактирования машин
# GET — любой, POST/PUT/DELETE — только владелец или админ
class IsOwnerOrAdmin(permissions.BasePermission):
    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return True
        return request.user.is_authenticated and (request.user.is_owner or request.user.is_staff)

    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            return True
        return request.user == obj.owner or request.user.is_staff


# Только чтение для всех, изменение — только владелец или админ
class IsOwnerOrReadOnly(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            return True
        return request.user == obj.owner or request.user.is_staff


# Участник аренды (арендатор или владелец) или админ
class IsRentalParticipant(permissions.BasePermission):
    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return request.user.is_authenticated
        return request.user.is_authenticated and (request.user.is_renter or request.user.is_staff)

    def has_object_permission(self, request, view, obj):
        if request.user.is_staff:
            return True
        if request.method in permissions.SAFE_METHODS:
            return request.user == obj.renter or request.user == obj.car.owner
        return request.user == obj.renter
