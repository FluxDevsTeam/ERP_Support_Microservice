from django.urls import path
from .views import (
    BlogPostViewSet, 
    CommentViewSet, 
    PublicBlogPostViewSet
)

app_name = 'blogs'

urlpatterns = [
    # Blog post management endpoints (superadmin only for write operations)
    path('posts/', BlogPostViewSet.as_view({'get': 'list'}), name='blog_posts_list'),
    path('posts/create/', BlogPostViewSet.as_view({'post': 'create'}), name='blog_posts_create'),
    path('posts/<uuid:pk>/', BlogPostViewSet.as_view({'get': 'retrieve'}), name='blog_posts_detail'),
    path('posts/<uuid:pk>/update/', BlogPostViewSet.as_view({'patch': 'partial_update'}), name='blog_posts_update'),
    path('posts/<uuid:pk>/delete/', BlogPostViewSet.as_view({'delete': 'destroy'}), name='blog_posts_delete'),
    path('posts/<uuid:pk>/publish/', BlogPostViewSet.as_view({'post': 'publish'}), name='blog_posts_publish'),
    path('posts/<uuid:pk>/unpublish/', BlogPostViewSet.as_view({'post': 'unpublish'}), name='blog_posts_unpublish'),
    path('posts/<uuid:pk>/comments/', BlogPostViewSet.as_view({'get': 'comments'}), name='blog_posts_comments'),
    
    # Comment management endpoints
    path('comments/', CommentViewSet.as_view({'get': 'list'}), name='comments_list'),
    path('comments/<uuid:pk>/', CommentViewSet.as_view({'get': 'retrieve'}), name='comments_detail'),
    path('comments/create/', CommentViewSet.as_view({'post': 'create'}), name='comments_create'),
    path('comments/<uuid:pk>/update/', CommentViewSet.as_view({'patch': 'partial_update'}), name='comments_update'),
    path('comments/<uuid:pk>/delete/', CommentViewSet.as_view({'delete': 'destroy'}), name='comments_delete'),
    
    # Public blog endpoints (read-only for published posts)
    path('public/posts/', PublicBlogPostViewSet.as_view({'get': 'list'}), name='public_blog_posts_list'),
    path('public/posts/<uuid:pk>/', PublicBlogPostViewSet.as_view({'get': 'retrieve'}), name='public_blog_posts_detail'),
]