from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import BlogPostViewSet, CommentViewSet, PublicBlogPostViewSet

app_name = 'blogs'

# Create router and register viewsets
router = DefaultRouter()
router.register(r'posts', BlogPostViewSet, basename='blogpost')
router.register(r'comments', CommentViewSet, basename='comment')
router.register(r'public', PublicBlogPostViewSet, basename='public')

urlpatterns = [
    # API routes
    path('api/', include(router.urls)),
    
    # Additional nested routes for comments on specific blog posts
    path('api/posts/<int:blog_post_id>/comments/', 
         CommentViewSet.as_view({'get': 'list', 'post': 'create'}), 
         name='post-comments'),
]

# Alternative URL patterns for better organization
# Uncomment and use these if you prefer explicit URL patterns over router patterns

# from .views import (
#     BlogPostListView, 
#     BlogPostDetailView, 
#     BlogPostCreateView,
#     BlogPostUpdateView,
#     BlogPostDeleteView,
#     CommentCreateView,
# )

# urlpatterns = [
#     # Blog post URLs
#     path('', BlogPostListView.as_view(), name='post-list'),
#     path('create/', BlogPostCreateView.as_view(), name='post-create'),
#     path('<slug:slug>/', BlogPostDetailView.as_view(), name='post-detail'),
#     path('<slug:slug>/edit/', BlogPostUpdateView.as_view(), name='post-edit'),
#     path('<slug:slug>/delete/', BlogPostDeleteView.as_view(), name='post-delete'),
#     
#     # Comment URLs
#     path('<slug:slug>/comments/', CommentCreateView.as_view(), name='post-comments'),
#     
#     # Admin URLs (if using class-based views)
#     path('admin/', include(router.urls)),
# ]