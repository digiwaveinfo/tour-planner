from rest_framework.permissions import BasePermission, SAFE_METHODS
from common.constant import UserRoletype

class IsSuperAdminOrAdminWriteElseReadOnly(BasePermission):
    """
    superadmin OR admin → full access
    anyone (even unauthenticated) → read only
    """
    def has_permission(self, request, view):
        if request.method in SAFE_METHODS:
            return True
        user = request.user
        if not user or not user.is_authenticated:
            return False
        if user.is_superuser:
            return True
        if getattr(user, "role", None) == UserRoletype.SUPER_ADMIN:
            return True
        return False

class DayTourPermission(BasePermission):
    def has_permission(self, request, view):
        user = request.user
        if request.method in SAFE_METHODS:
            return True
        if not user or not user.is_authenticated:
            return False
        if user.is_superuser:
            return True
        return user.role in [UserRoletype.SUPER_ADMIN, UserRoletype.AGENT]

class UserPlanPermission(BasePermission):
    """Any authenticated user can manage their own plans."""
    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated