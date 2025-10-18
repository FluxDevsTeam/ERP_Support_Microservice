from django.contrib.sites import requests
from rest_framework import permissions
from apps.billing.utils import IdentityServiceClient


class IsSuperuser(permissions.BasePermission):
    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated and request.user.is_superuser


class IsCEO(permissions.BasePermission):
    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated and request.user.role == 'ceo'


class CanInitiatePayment(permissions.BasePermission):
    def has_permission(self, request, view):
        if request.user.is_superuser:
            return True
        if request.user.role == 'ceo' and view.action == 'create':
            serializer = view.get_serializer(data=request.data)
            if serializer.is_valid():
                subscription = serializer.validated_data['subscription_id']
                client = IdentityServiceClient(request=request)
                try:
                    tenant = client.get_tenant(subscription.tenant_id)
                    return tenant['id'] == request.user.tenant.id
                except requests.RequestException:
                    return False
        return False


class CanViewPayment(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        if request.user.is_superuser:
            return True
        if request.user.role == 'ceo':
            client = IdentityServiceClient(request=request)
            try:
                tenant = client.get_tenant(obj.subscription.tenant_id)
                return tenant['id'] == request.user.tenant.id
            except requests.RequestException:
                return False
        return False
