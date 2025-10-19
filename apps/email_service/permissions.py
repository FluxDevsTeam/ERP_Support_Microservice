# apps/email_service/permissions.py
import hmac
import hashlib
import base64
from rest_framework import permissions
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework.exceptions import AuthenticationFailed
from django.conf import settings
from .models import EmailConfiguration
import logging
from datetime import datetime, timedelta
import json

logger = logging.getLogger('apps.email_service')

class IsSuperuser(permissions.BasePermission):
    def has_permission(self, request, view):
        logger.debug(f"Checking IsSuperuser: user={request.user}, authenticated={request.user.is_authenticated}, superuser={request.user.is_superuser}")
        return request.user and request.user.is_authenticated and request.user.is_superuser

class IsHMACAuthenticated(permissions.BasePermission):
    """Permission to verify HMAC signature for microservice-to-microservice requests."""
    
    def has_permission(self, request, view):
        # Get the HMAC signature and timestamp from headers
        signature = request.headers.get('X-HMAC-Signature')
        timestamp = request.headers.get('X-Timestamp')
        service_name = request.headers.get('X-Service-Name', 'identity-ms')
        logger.debug(f"HMAC: Received Signature={signature}, Timestamp={timestamp}, Service={service_name}")

        if not signature or not timestamp:
            logger.debug("Missing HMAC signature or timestamp")
            raise AuthenticationFailed('Missing HMAC signature or timestamp')

        try:
            # Get the shared secret from EmailConfiguration
            config = EmailConfiguration.get_instance()
            shared_secret = config.hmac_secret_key
            logger.debug(f"HMAC Secret Key: {shared_secret}")

            if not shared_secret:
                logger.debug("HMAC secret key not configured")
                raise AuthenticationFailed('HMAC secret key not configured')

            # Construct the message to verify
            payload_str = request.body.decode('utf-8')
            message = f"{request.method}{request.path}{timestamp}{payload_str}"
            logger.debug(f"HMAC Message: {message}")
            logger.debug(f"Payload String: {payload_str}")

            computed_signature = hmac.new(
                key=shared_secret.encode('utf-8'),
                msg=message.encode('utf-8'),
                digestmod=hashlib.sha256
            ).digest()
            computed_signature_b64 = base64.b64encode(computed_signature).decode('utf-8')
            logger.debug(f"Computed HMAC Signature: {computed_signature_b64}")

            # Compare signatures securely
            if not hmac.compare_digest(computed_signature_b64, signature):
                logger.debug(f"Signature Mismatch: Received={signature}, Computed={computed_signature_b64}")
                raise AuthenticationFailed('Invalid HMAC signature')

            # Validate timestamp to prevent replay attacks
            try:
                request_time = datetime.fromisoformat(timestamp)
                current_time = datetime.now()
                if abs((current_time - request_time).total_seconds()) > 300:  # 5-minute window
                    logger.debug("Timestamp too old")
                    raise AuthenticationFailed('Timestamp too old or invalid')
            except ValueError:
                logger.debug("Invalid timestamp format")
                raise AuthenticationFailed('Invalid timestamp format')

            logger.debug("HMAC Authentication successful")
            return True
        except Exception as e:
            logger.error(f"HMAC Authentication failed: {str(e)}")
            raise AuthenticationFailed(f'Authentication failed: {str(e)}')

class AllowAnySendEmail(permissions.BasePermission):
    """Allow email sending with HMAC authentication or superuser JWT."""
    
    def has_permission(self, request, view):
        logger.debug(f"Checking AllowAnySendEmail for action: {view.action}")
        if view.action == 'send_email':
            result = IsHMACAuthenticated().has_permission(request, view) or IsSuperuser().has_permission(request, view)
            logger.debug(f"AllowAnySendEmail result: {result}")
            return result
        return IsSuperuser().has_permission(request, view)