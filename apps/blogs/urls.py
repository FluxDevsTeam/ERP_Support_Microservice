from django.urls import path
from .views import (
    BlogPostViewSet, 
    CommentViewSet, 
    PublicBlogPostViewSet
)

app_name = 'blogs'

urlpatterns = [
    # Blog post management endpoints (superadmin only for write operations)
    path('posts/', BlogPostViewSet.as_view({'get': 'list', 'post': 'create'}), name='blog_posts'),
    path('posts/<uuid:pk>/', BlogPostViewSet.as_view({'get': 'retrieve', 'patch': 'partial_update', 'delete': 'destroy'}), name='blog_posts_detail'),
    path('posts/<uuid:pk>/publish/', BlogPostViewSet.as_view({'post': 'publish'}), name='blog_posts_publish'),
    path('posts/<uuid:pk>/unpublish/', BlogPostViewSet.as_view({'post': 'unpublish'}), name='blog_posts_unpublish'),
    path('posts/<uuid:pk>/comments/', BlogPostViewSet.as_view({'get': 'comments'}), name='blog_posts_comments'),
    
    # Comment management endpoints
    path('comments/', CommentViewSet.as_view({'get': 'list', 'post': 'create'}), name='comments'),
    path('comments/<uuid:pk>/', CommentViewSet.as_view({'get': 'retrieve', 'patch': 'partial_update', 'delete': 'destroy'}), name='comments_detail'),
    
    # Public blog endpoints (read-only for published posts)
    path('public/posts/', PublicBlogPostViewSet.as_view({'get': 'list'}), name='public_blog_posts_list'),
    path('public/posts/<uuid:pk>/', PublicBlogPostViewSet.as_view({'get': 'retrieve'}), name='public_blog_posts_detail'),
]