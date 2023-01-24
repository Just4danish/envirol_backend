from rest_framework import permissions

class IsFoodwatchUser(permissions.BasePermission):
    def has_permission(self, request, view):
        if request.user.user_class == 'Foodwatch' and request.user.user_status == 'Activated':
            return True

class IsEnvirolUser(permissions.BasePermission):
    def has_permission(self, request, view):
        if request.user.user_class == 'Envirol' and request.user.user_status == 'Activated':
            return True

class IsGTCCUser(permissions.BasePermission):
    def has_permission(self, request, view):
        if request.user.user_class == 'GTCC' and request.user.user_status == 'Activated':
            return True

class IsEntityUser(permissions.BasePermission):
    def has_permission(self, request, view):
        if request.user.user_class == 'Entity' and request.user.user_status == 'Activated':
            return True

class IsDriver(permissions.BasePermission):
    def has_permission(self, request, view):
        if request.user.user_type == 'Driver' and request.user.user_status == 'Activated':
            return True

class IsOperator(permissions.BasePermission):
    def has_permission(self, request, view):
        if request.user.user_type == 'Operator' and request.user.user_status == 'Activated':
            return True