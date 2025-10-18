# apps/email_service/urls.py
from django.urls import path
from .views import EmailViewSet

urlpatterns = [
    path('send-email/', EmailViewSet.as_view({'post': 'send_email'}), name='send_email'),
    path('logs/', EmailViewSet.as_view({'get': 'list_logs'}), name='email_logs'),
]