from rest_framework import permissions

class IsAdminOrReadOnly(permissions.BasePermission):
    """
    السماح فقط للـ Admin بإضافة أو تعديل أو حذف، والباقي يمكنهم القراءة فقط.
    """
    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:  # GET, HEAD, OPTIONS
            return True
        return request.user.is_authenticated and request.user.is_staff


class IsOrderOwnerOrAdmin(permissions.BasePermission):
    """
    - المستخدم العادي يشوف طلباته فقط
    - الـ Admin يشوف ويعدل على الكل
    """
    def has_object_permission(self, request, view, obj):
        return request.user.is_staff or obj.customer == request.user
