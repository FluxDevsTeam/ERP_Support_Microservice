# apps/email_service/urls.py
from django.urls import path
from .views import EmailSendViewSet, EmailAdminViewSet, EmailConfigurationViewSet

urlpatterns = [
    # Email sending endpoint
    path('send-email/', EmailSendViewSet.as_view({'post': 'send_email'}), name='send_email'),
    
    # Admin endpoints (logs and stats)
    path('logs/', EmailAdminViewSet.as_view({'get': 'list'}), name='email_logs'),
    path('stats/', EmailAdminViewSet.as_view({'get': 'email_stats'}), name='email_stats'),
    path('type-stats/', EmailAdminViewSet.as_view({'get': 'email_type_stats'}), name='email_type_stats'),
    path('logs/<int:pk>/retry/', EmailAdminViewSet.as_view({'post': 'retry_email'}), name='email_retry'),
    
    # Email Configuration URLs
    path('config/', EmailConfigurationViewSet.as_view({'get': 'list', 'patch': 'partial_update'}), name='email_config'),
    path('config/test-smtp/', EmailConfigurationViewSet.as_view({'post': 'test_smtp_connection'}), name='test_smtp_connection'),
]