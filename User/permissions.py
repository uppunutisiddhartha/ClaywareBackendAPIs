from rest_framework.permissions import BasePermission

class IsCustomer(BasePermission):
    message = "Only Autharised to perform this action"

    def has_permission(self, request, view):
        return (
            request.user and
            
            request.user.is_authenticated and
            request.user.role == 'user'
        )
    

