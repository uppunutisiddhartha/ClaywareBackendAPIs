from rest_framework.permissions import BasePermission


class IsProductReviewer(BasePermission):

    def has_permission(self, request, view):
        return (
            request.user.is_authenticated
            and request.user.role == "product_reviewer"
            and request.user.account_status == "active"
        )