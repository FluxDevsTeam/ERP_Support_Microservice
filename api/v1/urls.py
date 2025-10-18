from django.urls import path, include

urlpatterns = [
    path("email-service/", include("apps.email_service.urls")),
]
