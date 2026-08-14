from rest_framework.permissions import BasePermission


class IsProductReviewer(BasePermission):
    """
    Allows access only to active Product Review Team members.
    """

    message = "You are not authorized to access the Product Review Team."

    def has_permission(self, request, view):

        return (
            request.user
            and request.user.is_authenticated
            and request.user.role == "product_reviewer"
            and request.user.account_status == "active"
        )