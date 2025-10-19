# apps/email_service/permissions.py
import jwt
from rest_framework import permissions
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework.exceptions import AuthenticationFailed
from django.conf import settings

class IsSuperuser(permissions.BasePermission):
    def has_permission(self, request, view):
        print(f"Checking IsSuperuser: user={request.user}, authenticated={request.user.is_authenticated}, superuser={request.user.is_superuser}")
        return request.user and request.user.is_authenticated and request.user.is_superuser

class IsMicroserviceJWT(permissions.BasePermission):
    """Permission to verify JWT for microservice-to-microservice requests."""
    
    def has_permission(self, request, view):
        # Get the JWT token from microservice-specific header
        jwt_token = request.headers.get('Support-Microservice-Auth')
        print(f"Microservice JWT: Received Support-Microservice-Auth header")

        if not jwt_token:
            print("Missing Support-Microservice-Auth header")
            raise AuthenticationFailed('Missing microservice authentication header')

        try:
            # Get the JWT secret from settings
            jwt_secret = settings.SUPPORT_JWT_SECRET_KEY
            print(f"SUPPORT_JWT_SECRET_KEY configured: {bool(jwt_secret)}")

            if not jwt_secret:
                print("SUPPORT_JWT_SECRET_KEY not configured in settings")
                raise AuthenticationFailed('Microservice JWT secret key not configured')

            # Decode and verify the JWT token
            payload = jwt.decode(
                jwt_token, 
                jwt_secret, 
                algorithms=['HS256'],
                options={'verify_exp': True}
            )
            
            print(f"Microservice JWT Payload: {payload}")
            
            # Verify this is a microservice token
            if payload.get('type') != 'microservice':
                print("Invalid microservice token type")
                raise AuthenticationFailed('Invalid microservice token type')
            
            # Store microservice info in request for logging
            request.microservice_name = payload.get('service', 'unknown')
            print(f"Authenticated microservice: {request.microservice_name}")
            
            print("Microservice JWT Authentication successful")
            return True
            
        except jwt.ExpiredSignatureError:
            print("Microservice JWT token has expired")
            raise AuthenticationFailed('Microservice token has expired')
        except jwt.InvalidTokenError as e:
            print(f"Invalid microservice JWT token: {str(e)}")
            raise AuthenticationFailed(f'Invalid microservice token: {str(e)}')
        except Exception as e:
            print(f"Microservice JWT Authentication failed: {str(e)}")
            raise AuthenticationFailed(f'Microservice authentication failed: {str(e)}')

class AllowAnySendEmail(permissions.BasePermission):
    """Allow email sending with microservice JWT or superuser JWT."""
    
    def has_permission(self, request, view):
        print(f"Checking AllowAnySendEmail for action: {view.action}")
        
        if view.action == 'send_email':
            # Try microservice authentication first
            try:
                microservice_auth = IsMicroserviceJWT().has_permission(request, view)
                if microservice_auth:
                    print("AllowAnySendEmail: Authenticated via microservice JWT")
                    return True
            except AuthenticationFailed as e:
                print(f"Microservice auth failed: {str(e)}")
                # Continue to try superuser auth
            
            # Try superuser authentication
            try:
                superuser_auth = IsSuperuser().has_permission(request, view)
                if superuser_auth:
                    print("AllowAnySendEmail: Authenticated via superuser JWT")
                    return True
            except AuthenticationFailed as e:
                print(f"Superuser auth failed: {str(e)}")
            
            print("AllowAnySendEmail: Both authentication methods failed")
            return False
        
        # For other actions, only allow superusers
        return IsSuperuser().has_permission(request, view)