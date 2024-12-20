from rest_framework import permissions

class IsOwnerOrAdmin(permissions.BasePermission):
    """
    Custom permission to only allow owners of an account or admins to edit it.
    """
    def has_object_permission(self, request, view, obj):
        # Allow admin users
        if request.user.is_staff:
            return True
            
        # Allow the owner of the account
        return obj == request.user