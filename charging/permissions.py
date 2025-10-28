from rest_framework import permissions

class IsOperator(permissions.BasePermission):
    """Allow access only to operators"""
    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated and (
            request.user.is_operator or request.user.is_staff
        )


class IsMaintenanceStaff(permissions.BasePermission):
    """Allow access only to maintenance staff"""
    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated and (
            request.user.is_maintenance or request.user.is_staff
        )