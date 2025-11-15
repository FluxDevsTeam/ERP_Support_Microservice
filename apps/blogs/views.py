from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter
from django.db.models import Q
from django.shortcuts import get_object_or_404
from django.utils import timezone
from drf_yasg.utils import swagger_auto_schema

from .models import BlogPost, Comment
from .serializers import (
    BlogPostListSerializer,
    BlogPostDetailSerializer,
    BlogPostCreateUpdateSerializer,
    CommentSerializer,
    CommentListSerializer,
    CommentDetailSerializer,
    CommentCreateUpdateSerializer
)
from .permissions import (
    IsSuperuser,
    IsSuperuserOrReadOnly,
    IsCommenterOrSuperuser, 
    IsAuthenticatedForComments,
    CanReadPublishedPosts
)
from .utils import get_request_role, get_request_tenant, swagger_helper
from .pagination import BlogPagination
import logging

logger = logging.getLogger('blogs')


class BlogPostViewSet(viewsets.ModelViewSet):
    """
    ViewSet for blog posts with permission-based access control.
    
    - Superusers: Full CRUD access
    - Public: Read access to published posts only
    """
    queryset = BlogPost.objects.all()
    permission_classes = [IsSuperuserOrReadOnly]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['status', 'author_user_id']
    search_fields = ['title', 'content', 'excerpt', 'tags', 'author_name']
    ordering_fields = ['created_at', 'updated_at', 'title', 'published_at']
    ordering = ['-created_at']
    pagination_class = BlogPagination
    
    def get_queryset(self):
        """
        Filter queryset based on user permissions and query parameters.
        """
        user = self.request.user
        
        # If user is superuser, show all posts
        if user.is_authenticated and user.is_superuser:
            return BlogPost.objects.all()
        
        # For non-superusers, only show published posts
        return BlogPost.objects.filter(status='published', published_at__isnull=False)
    
    def get_serializer_class(self):
        """
        Return appropriate serializer based on action.
        """
        if self.action == 'list':
            return BlogPostListSerializer
        elif self.action in ['create', 'update', 'partial_update']:
            return BlogPostCreateUpdateSerializer
        else:
            return BlogPostDetailSerializer
    
    def get_permissions(self):
        """
        Set permissions based on action.
        """
        if self.action in ['list', 'retrieve']:
            # Public read access to published posts
            return [AllowAny()]
        else:
            return [IsSuperuserOrReadOnly()]
    
    @swagger_helper("Blog Posts", "BlogPost")
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)
    
    @swagger_helper("Blog Posts", "BlogPost")
    def retrieve(self, request, *args, **kwargs):
        return super().retrieve(request, *args, **kwargs)
    
    @swagger_helper("Blog Posts", "BlogPost")
    def create(self, request, *args, **kwargs):
        return super().create(request, *args, **kwargs)
    
    @swagger_helper("Blog Posts", "BlogPost")
    def partial_update(self, request, *args, **kwargs):
        return super().partial_update(request, *args, **kwargs)
    
    @swagger_helper("Blog Posts", "BlogPost")
    def destroy(self, request, *args, **kwargs):
        return super().destroy(request, *args, **kwargs)
    
    @swagger_helper("Blog Posts", "BlogPost")
    @action(detail=True, methods=['post'], permission_classes=[IsSuperuser])
    def publish(self, request, pk=None):
        """
        Action to publish a blog post (superuser only).
        """
        if not request.user.is_superuser:
            return Response(
                {'detail': 'Only superusers can publish posts.'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        post = self.get_object()
        post.status = 'published'
        post.published_at = timezone.now()
        post.save()
        
        serializer = self.get_serializer(post)
        return Response(serializer.data)
    
    @swagger_helper("Blog Posts", "BlogPost")
    @action(detail=True, methods=['post'], permission_classes=[IsSuperuser])
    def unpublish(self, request, pk=None):
        """
        Action to unpublish a blog post (superuser only).
        """
        if not request.user.is_superuser:
            return Response(
                {'detail': 'Only superusers can unpublish posts.'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        post = self.get_object()
        post.status = 'draft'
        post.save()
        
        serializer = self.get_serializer(post)
        return Response(serializer.data)
    
    @swagger_helper("Blog Posts", "BlogPost")
    @action(detail=True, methods=['get'], permission_classes=[AllowAny])
    def comments(self, request, pk=None):
        """
        Get all comments for a blog post.
        """
        post = self.get_object()
        
        # Only show published posts to public
        if not (request.user.is_authenticated and request.user.is_superuser):
            if post.status != 'published' or post.published_at is None:
                return Response(
                    {'detail': 'Post not found or not published.'},
                    status=status.HTTP_404_NOT_FOUND
                )
        
        comments = post.comments.all()
        serializer = CommentSerializer(comments, many=True, context={'request': request})
        return Response(serializer.data)


class CommentViewSet(viewsets.ModelViewSet):
    """
    ViewSet for blog comments.

    - Authenticated users: Create comments
    - Comment authors: Edit their own comments
    - Superusers: Full CRUD access
    - Public: Read access to all comments
    """
    queryset = Comment.objects.all()
    permission_classes = [IsCommenterOrSuperuser]
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    filterset_fields = ['blog_post']
    ordering = ['created_at']

    def get_serializer_class(self):
        """
        Return appropriate serializer based on action.
        """
        if self.action == 'list':
            return CommentListSerializer
        elif self.action in ['create', 'update', 'partial_update']:
            return CommentCreateUpdateSerializer
        else:
            return CommentDetailSerializer
    
    def get_queryset(self):
        """
        Filter queryset based on user permissions.
        """
        user = self.request.user
        
        if user.is_authenticated and user.is_superuser:
            return Comment.objects.all()
        
        # For non-superusers, show all comments (no approval needed)
        return Comment.objects.all()
    
    def get_permissions(self):
        """
        Set permissions based on action.
        """
        if self.action == 'create':
            return [IsAuthenticatedForComments()]
        elif self.action in ['update', 'partial_update', 'destroy']:
            return [IsCommenterOrSuperuser()]
        else:
            return [AllowAny()]
    
    def get_serializer_context(self):
        """
        Add blog post to serializer context if provided in kwargs.
        """
        context = super().get_serializer_context()
        
        # Get blog_post from URL kwargs
        blog_post_id = self.kwargs.get('blog_post_id')
        if blog_post_id:
            context['blog_post'] = get_object_or_404(BlogPost, pk=blog_post_id)
        
        return context
    
    @swagger_helper("Comments", "Comment")
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)
    
    @swagger_helper("Comments", "Comment")
    def retrieve(self, request, *args, **kwargs):
        return super().retrieve(request, *args, **kwargs)
    
    @swagger_helper("Comments", "Comment")
    def create(self, request, *args, **kwargs):
        return super().create(request, *args, **kwargs)
    
    @swagger_helper("Comments", "Comment")
    def partial_update(self, request, *args, **kwargs):
        return super().partial_update(request, *args, **kwargs)
    
    @swagger_helper("Comments", "Comment")
    def destroy(self, request, *args, **kwargs):
        return super().destroy(request, *args, **kwargs)


class PublicBlogPostViewSet(viewsets.ReadOnlyModelViewSet):
    """
    Public read-only access to published blog posts.
    
    - Anyone: Read access to published posts and their comments
    """
    serializer_class = BlogPostListSerializer
    permission_classes = [AllowAny]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['tags']
    search_fields = ['title', 'content', 'excerpt', 'tags']
    ordering_fields = ['created_at', 'updated_at', 'title', 'published_at']
    ordering = ['-published_at']
    pagination_class = BlogPagination
    
    def get_queryset(self):
        """
        Only return published blog posts.
        """
        return BlogPost.objects.filter(
            status='published',
            published_at__isnull=False
        )
    
    def get_serializer_class(self):
        """
        Return appropriate serializer based on action.
        """
        if self.action == 'list':
            return BlogPostListSerializer
        else:
            return BlogPostDetailSerializer
    
    @swagger_helper("Public Blog Posts", "BlogPost")
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)
    
    @swagger_helper("Public Blog Posts", "BlogPost")
    def retrieve(self, request, *args, **kwargs):
        return super().retrieve(request, *args, **kwargs)