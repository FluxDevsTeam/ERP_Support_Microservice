from rest_framework import serializers
from .models import BlogPost, Comment


class UserInfoSerializer(serializers.Serializer):
    """Serializer for user information from JWT token (following billing service pattern)"""
    user_id = serializers.CharField()
    email = serializers.CharField(allow_blank=True)
    first_name = serializers.CharField(allow_blank=True)
    last_name = serializers.CharField(allow_blank=True)
    full_name = serializers.SerializerMethodField()
    
    def get_user_id(self, obj):
        if hasattr(obj, 'user_user_id'):
            return obj.user_user_id
        elif hasattr(obj, 'author_user_id'):
            return obj.author_user_id
        return None
    
    def get_full_name(self, obj):
        if hasattr(obj, 'user_name') and obj.user_name:
            return obj.user_name
        elif hasattr(obj, 'author_name') and obj.author_name:
            return obj.author_name
        return f"User {self.get_user_id(obj)}"


class AuthorInfoSerializer(serializers.Serializer):
    """Serializer for author information in blog posts"""
    user_id = serializers.IntegerField(source='author_user_id')
    name = serializers.CharField(source='author_name')
    
    def to_representation(self, instance):
        data = super().to_representation(instance)
        # If author_name is not set, create a default one
        if not data.get('name'):
            data['name'] = f"User {data['user_id']}"
        return data


class CommentSerializer(serializers.ModelSerializer):
    """Serializer for blog comments"""
    user = UserInfoSerializer(read_only=True)
    is_reply = serializers.ReadOnlyField()
    
    class Meta:
        model = Comment
        fields = [
            'id', 'blog_post', 'user', 'content', 'is_approved', 
            'parent', 'created_at', 'updated_at', 'is_reply'
        ]
        read_only_fields = ['id', 'is_approved', 'user', 'created_at', 'updated_at', 'is_reply']
    
    def create(self, validated_data):
        # Get the user from the request context (following billing service pattern)
        request = self.context.get('request')
        user = request.user
        
        # Set user information directly (like billing service pattern)
        validated_data['user_user_id'] = str(user.id) if hasattr(user, 'id') else str(user.username)
        
        # Try to get name from various user attributes (following billing service pattern)
        user_name = None
        if hasattr(user, 'first_name') and hasattr(user, 'last_name') and (user.first_name or user.last_name):
            user_name = f"{user.first_name} {user.last_name}".strip()
        elif hasattr(user, 'full_name'):
            user_name = user.full_name
        elif hasattr(user, 'username'):
            user_name = user.username
        else:
            user_name = "Unknown User"
            
        validated_data['user_name'] = user_name
        
        # Get the blog post from URL kwargs
        validated_data['blog_post'] = self.context['blog_post']
        
        return super().create(validated_data)


class BlogPostListSerializer(serializers.ModelSerializer):
    """Serializer for listing blog posts"""
    author = AuthorInfoSerializer(read_only=True)
    comment_count = serializers.ReadOnlyField()
    
    class Meta:
        model = BlogPost
        fields = [
            'id', 'title', 'excerpt', 'author', 'status', 
            'featured_image', 'image_1', 'image_2', 'image_3', 'tags', 'created_at', 'updated_at', 
            'published_at', 'comment_count'
        ]
        read_only_fields = fields


class BlogPostDetailSerializer(serializers.ModelSerializer):
    """Serializer for detailed blog post view"""
    author = AuthorInfoSerializer(read_only=True)
    comments = serializers.SerializerMethodField()
    comment_count = serializers.ReadOnlyField()
    
    class Meta:
        model = BlogPost
        fields = [
            'id', 'title', 'content', 'excerpt', 'author', 
            'status', 'featured_image', 'image_1', 'image_2', 'image_3', 'tags', 'meta_title', 
            'meta_description', 'created_at', 'updated_at', 
            'published_at', 'comment_count', 'is_published', 'comments'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 'published_at', 'comment_count', 'is_published', 'comments']
    
    def get_comments(self, obj):
        # Only show approved comments
        approved_comments = obj.comments.filter(is_approved=True)
        return CommentSerializer(approved_comments, many=True, context=self.context).data


class BlogPostCreateUpdateSerializer(serializers.ModelSerializer):
    """Serializer for creating and updating blog posts"""
    
    class Meta:
        model = BlogPost
        fields = [
            'title', 'content', 'excerpt', 'status', 'featured_image', 'image_1', 'image_2', 'image_3',
            'tags', 'meta_title', 'meta_description'
        ]
    
    def create(self, validated_data):
        # Get the author from the request context (following billing service pattern)
        request = self.context.get('request')
        user = request.user
        
        # Set author information directly (like billing service pattern)
        validated_data['author_user_id'] = str(user.id) if hasattr(user, 'id') else str(user.username)
        
        # Try to get name from various user attributes (following billing service pattern)
        user_name = None
        if hasattr(user, 'first_name') and hasattr(user, 'last_name') and (user.first_name or user.last_name):
            user_name = f"{user.first_name} {user.last_name}".strip()
        elif hasattr(user, 'full_name'):
            user_name = user.full_name
        elif hasattr(user, 'username'):
            user_name = user.username
        else:
            user_name = "Unknown User"
            
        validated_data['author_name'] = user_name
        
        return super().create(validated_data)
    
    def validate_title(self, value):
        """Ensure title is not empty and is unique"""
        if not value.strip():
            raise serializers.ValidationError("Title cannot be empty")
        return value.strip()
    
    def validate_content(self, value):
        """Ensure content is not empty"""
        if not value.strip():
            raise serializers.ValidationError("Content cannot be empty")
        return value.strip()