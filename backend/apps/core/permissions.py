from rest_framework.permissions import BasePermission, SAFE_METHODS

from .models import Membership, UserRole


class IsLabelOwnerOrReadOnly(BasePermission):
    """
    Members can read label data.
    Only owners can update label data.
    Label deletion is disabled.
    """

    def has_permission(self, request, view):
        if request.method == "DELETE":
            return False

        return bool(
            request.user
            and request.user.is_authenticated
        )

    def has_object_permission(self, request, view, obj):
        if request.method in SAFE_METHODS:
            return True

        return Membership.objects.filter(
            user=request.user,
            label=obj,
            role=UserRole.LABEL_OWNER,
        ).exists()