from rest_framework import permissions


class IsAdmin(permissions.BasePermission):
    def has_permission(self, request, view):
        return request.user.role == "admin"


class IsSeller(permissions.BasePermission):
    def has_permission(self, request, view):
        return request.user.role == "Seller"


class IsBuyer(permissions.BasePermission):
    def has_permission(self, request, view):
        return request.user.role == "Buyer"