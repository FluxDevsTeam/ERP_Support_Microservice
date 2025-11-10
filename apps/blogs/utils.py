import requests
import logging
from django.conf import settings
from typing import Dict, Any, Optional
from drf_yasg.utils import swagger_auto_schema
from .pagination import BLOG_PAGINATION_PARAMS

logger = logging.getLogger('blogs')


class IdentityServiceClient:
    def __init__(self, request=None):
        self.request = request
        self.base_url = settings.IDENTITY_MICROSERVICE_URL

    def get_user(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Get user information from identity microservice"""
        try:
            headers = self._get_headers()
            response = requests.get(f"{self.base_url}/api/v1/user/{user_id}", headers=headers, timeout=5)
            response.raise_for_status()
            logger.info(f"User {user_id} retrieved from identity service")
            return response.json()
        except Exception as e:
            logger.error(f"Failed to get user {user_id}: {str(e)}")
            return None

    def get_users(self, tenant_id: str = None) -> list:
        """Get users from identity microservice"""
        try:
            headers = self._get_headers()
            params = {'tenant_id': tenant_id} if tenant_id else None
            response = requests.get(f"{self.base_url}/api/v1/user/management/", headers=headers, params=params, timeout=5)
            response.raise_for_status()
            data = response.json()
            results = data.get('results') if isinstance(data, dict) else None
            logger.info(f"Users retrieved from identity service; count={data.get('count') if isinstance(data, dict) else 'unknown'}")
            return results if results is not None else (data if data is not None else [])
        except Exception as e:
            logger.error(f"Failed to get users: {str(e)}")
            return []

    def _get_headers(self) -> Dict[str, str]:
        """Get headers for identity service requests"""
        headers = {'Content-Type': 'application/json'}
        if self.request:
            # First try to get token from request headers
            auth_header = self.request.headers.get('Authorization')
            if auth_header:
                headers['Authorization'] = auth_header
                logger.debug(f"Using Authorization header from request: {auth_header[:15]}...")
            # Fallback to user object if no header found
            elif hasattr(self.request, 'user') and self.request.user.is_authenticated:
                access_token = getattr(self.request.user, 'access_token', None)
                if not access_token:
                    access_token = getattr(self.request.user, 'auth_token', None)
                
                if access_token:
                    headers['Authorization'] = f"JWT {access_token}"
                    logger.debug(f"Using Authorization header from user: JWT {access_token[:10]}...")
                else:
                    logger.debug("No access token found in request headers or user object")
        return headers


def get_request_role(request) -> Optional[str]:
    """Normalize and return a role string from the request or user object.

    Checks several common locations that identity systems use for storing role:
    - request.role
    - request.user.role
    - request.user.user_role
    - request.user.user_role_lowercase

    Returns the role as lowercase string or None if not found.
    """
    if not request:
        return None
    # direct request.role
    role = getattr(request, 'role', None)
    if role:
        return role.lower()
    # try user attributes
    user = getattr(request, 'user', None)
    if not user:
        return None
    for attr in ('role', 'user_role', 'user_role_lowercase'):
        if hasattr(user, attr):
            val = getattr(user, attr)
            if val:
                return val.lower() if isinstance(val, str) else None
    # sometimes role may be set under a nested dict like user.role['name'] etc. try best-effort
    try:
        val = getattr(user, 'role', None)
        if isinstance(val, dict) and 'name' in val:
            return str(val['name']).lower()
    except Exception:
        pass
    return None


def get_request_tenant(request) -> Optional[str]:
    """Get tenant ID from request or user object"""
    if not request:
        return None
    # direct request.tenant
    tenant = getattr(request, 'tenant', None)
    if tenant:
        return str(tenant)
    # try user.tenant
    user = getattr(request, 'user', None)
    if user and hasattr(user, 'tenant'):
        tenant = getattr(user, 'tenant', None)
        return str(tenant) if tenant else None
    return None


def swagger_helper(tags, model):
    """Decorator for Swagger API documentation following email service pattern"""
    def decorators(func):
        descriptions = {
            "list": f"Retrieve a list of {model}",
            "retrieve": f"Retrieve details of a specific {model}",
            "create": f"Create a new {model}",
            "update": f"Update a {model}",
            "partial_update": f"Partially update a {model}",
            "destroy": f"Delete a {model}",
            "publish": f"Publish a {model}",
            "unpublish": f"Unpublish a {model}",
            "approve": f"Approve a {model}",
            "reject": f"Reject a {model}",
            "comments": f"Get comments for a {model}",
        }

        action_type = func.__name__
        get_description = descriptions.get(action_type, f"{action_type} {model}")
        return swagger_auto_schema(
            manual_parameters=BLOG_PAGINATION_PARAMS, 
            operation_id=f"{action_type} {model}", 
            operation_description=get_description, 
            tags=[tags]
        )(func)

    return decorators