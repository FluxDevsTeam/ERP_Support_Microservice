from rest_framework import permissions
import logging

logger = logging.getLogger('blogs')


class IsSuperuser(permissions.BasePermission):
    """Permission class that allows only superusers to perform actions"""
    
    def has_permission(self, request, view):
        is_super = request.user.is_superuser
        logger.debug(f"Superuser check for user {getattr(request.user, 'id', None)}: {is_super}")
        return is_super


class IsAuthenticatedForComments(permissions.BasePermission):
    """Permission class that allows authenticated users to create comments"""
    
    def has_permission(self, request, view):
        is_authenticated = request.user.is_authenticated
        logger.debug(f"Authenticated check for user {getattr(request.user, 'id', None)}: {is_authenticated}")
        return is_authenticated


class IsOwnerOrSuperuser(permissions.BasePermission):
    """Permission class that allows users to edit their own content or superusers to edit any"""
    
    def has_permission(self, request, view):
        # Allow read access to all users for published content
        if request.method in permissions.SAFE_METHODS:
            return True
        
        # For write operations, require authentication
        is_authenticated = request.user.is_authenticated
        if not is_authenticated:
            logger.debug(f"Write operation denied: user not authenticated")
            return False
        
        logger.debug(f"Write operation allowed for authenticated user {getattr(request.user, 'id', None)}")
        return True
    
    def has_object_permission(self, request, view, obj):
        # Superusers can do anything
        if request.user.is_superuser:
            logger.debug(f"Full access granted for superuser {getattr(request.user, 'id', None)}")
            return True
        
        # Check if user is the owner of the object
        user_id = str(getattr(request.user, 'id', None))
        object_user_id = getattr(obj, 'user_user_id', None)
        
        if object_user_id and user_id == object_user_id:
            logger.debug(f"Owner access granted for user {user_id} on object {object_user_id}")
            return True
        
        # For read operations, allow access to approved content
        if request.method in permissions.SAFE_METHODS:
            is_approved = getattr(obj, 'is_approved', True)
            logger.debug(f"Read access check: approved={is_approved}")
            return is_approved
        
        logger.debug(f"Access denied: user {user_id} is not owner of {object_user_id}")
        return False


class CanReadPublishedPosts(permissions.BasePermission):
    """Permission class that allows read access to published posts and approved comments"""
    
    def has_object_permission(self, request, view, obj):
        # Check if it's a blog post
        if hasattr(obj, 'status'):
            # For blog posts, only allow access to published posts
            is_published = obj.status == 'published' and getattr(obj, 'published_at', None) is not None
            logger.debug(f"Published post check: {is_published}")
            return is_published
        
        # For comments, only allow access to approved comments
        if hasattr(obj, 'is_approved'):
            is_approved = obj.is_approved
            logger.debug(f"Approved comment check: {is_approved}")
            return is_approved
        
        # Default deny
        return False


class IsSuperuserOrReadOnly(permissions.BasePermission):
    """Permission class that allows superusers full access, others read-only access"""
    
    def has_permission(self, request, view):
        # Allow read access to all users
        if request.method in permissions.SAFE_METHODS:
            logger.debug(f"Read access allowed for {request.method}")
            return True
        
        # For write operations, only superusers
        is_super = request.user.is_superuser
        logger.debug(f"Write operation superuser check: {is_super}")
        return is_super


class IsCommenterOrSuperuser(permissions.BasePermission):
    """Permission class for comment management following billing service pattern"""
    
    def has_permission(self, request, view):
        # Allow read access to all users for approved comments
        if request.method in permissions.SAFE_METHODS:
            return True
        
        # For comment creation, require authentication
        if request.method == 'POST':
            is_authenticated = request.user.is_authenticated
            logger.debug(f"Comment creation authenticated check: {is_authenticated}")
            return is_authenticated
        
        # For edit/delete operations, require authentication
        is_authenticated = request.user.is_authenticated
        logger.debug(f"Comment edit/delete authenticated check: {is_authenticated}")
        return is_authenticated
    
    def has_object_permission(self, request, view, obj):
        # Read access is allowed for all users (no approval needed)
        if request.method in permissions.SAFE_METHODS:
            logger.debug(f"Comment read access: allowed")
            return True
        
        # Superusers can do anything
        if request.user.is_superuser:
            logger.debug(f"Superuser full comment access granted")
            return True
        
        # Users can edit their own comments
        if request.method in ['PUT', 'PATCH']:
            user_id = str(getattr(request.user, 'id', None))
            object_user_id = getattr(obj, 'user_user_id', None)
            is_owner = user_id == object_user_id
            logger.debug(f"Comment owner check: user {user_id} vs object {object_user_id} = {is_owner}")
            return is_owner
        
        # Users can delete their own comments, superusers can delete any
        if request.method == 'DELETE':
            user_id = str(getattr(request.user, 'id', None))
            object_user_id = getattr(obj, 'user_user_id', None)
            is_owner = user_id == object_user_id
            logger.debug(f"Comment delete: user {user_id} vs object {object_user_id} = {is_owner}")
            return is_owner or request.user.is_superuser
        
        return False