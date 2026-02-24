from rest_framework.permissions import BasePermission, SAFE_METHODS
from common.constant import UserRoletype

class IsSuperAdminOrAdminWriteElseReadOnly(BasePermission):
    """
    superadmin OR admin → full access
    agent/basic_user → read only
    """
    def has_permission(self, request, view):
        user = request.user
        if not user or not user.is_authenticated:
            return False
        if request.method in SAFE_METHODS:
            return True
        if user.is_superuser:
            return True
        if getattr(user, "role", None) == UserRoletype.ADMIN:
            return True
        return False