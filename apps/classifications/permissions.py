from rest_framework import permissions


class IsAuthenticatedOrReadOnly(permissions.BasePermission):
    """
    Custom permission to allow:
    - Read-only access for everyone
    - Write access only for authenticated users
    """
    def has_permission(self, request, view):
        # Allow read methods (GET, HEAD, OPTIONS) for everyone
        if request.method in permissions.SAFE_METHODS:
            return True
        
        # Write methods require authentication
        return request.user and request.user.is_authenticated


class IsOwnerOrReadOnly(permissions.BasePermission):
    """
    Custom permission to only allow owners of an object to edit it.
    """
    def has_object_permission(self, request, view, obj):
        # Read permissions are allowed to any request
        if request.method in permissions.SAFE_METHODS:
            return True
        
        # Write permissions are only allowed to the owner
        return obj.user == request.user


class IsGoldUserOrReadOnly(permissions.BasePermission):
    """
    Only allow gold users to write, everyone can read
    """
    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return True
        
        return (request.user and 
                request.user.is_authenticated and 
                hasattr(request.user, 'classification_profile') and
                request.user.classification_profile.is_gold_user)
