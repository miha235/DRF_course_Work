from rest_framework.permissions import BasePermission


class IsOwnerOrReadOnly(BasePermission):
    def has_object_permission(self, request, view, obj):
        if request.method in ['GET']:
            return obj.is_public or obj.user == request.user
        return obj.user == request.user
