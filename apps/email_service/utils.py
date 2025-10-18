# apps/email_service/utils.py
import os
from django.conf import settings
from django.core.mail import send_mail
from django.template import Template, Context
from django.utils import timezone
from rest_framework import authentication, exceptions
from datetime import datetime
import hmac
import hashlib
import time
from django.conf import settings
from rest_framework import authentication, exceptions
import json

def send_generic_email(user_email, email_type, subject, action, message, otp=None, link=None, link_text=None):
    try:
        valid_email_types = ['otp', 'confirmation', 'reset_link']
        if email_type not in valid_email_types:
            raise ValueError(f"Invalid email_type: must be one of {valid_email_types}")

        context = {
            'subject': subject,
            'action': action,
            'message': message,
            'otp': otp,
            'link': link,
            'link_text': link_text,
            'site_url': settings.SITE_URL,
            'current_year': datetime.now().year,
            'support_email': settings.SUPPORT_EMAIL,
            'support_phone_number': settings.SUPPORT_PHONE_NUMBER,
            'brand_name': settings.BRAND_NAME,
            'brand_logo': 'https://tse4.mm.bing.net/th/id/OIP.rcKRRDLHGEu5lWcn6vbKcAHaHa?rs=1&pid=ImgDetMain',
            'terms_of_service': settings.TERMS_OF_SERVICE,
            'social_true': any(settings.SOCIAL_LINKS.values()),
            'fb_link': settings.SOCIAL_LINKS.get('facebook'),
            'ig_link': settings.SOCIAL_LINKS.get('instagram'),
            'x_link': settings.SOCIAL_LINKS.get('twitter'),
            'linkedin_link': settings.SOCIAL_LINKS.get('linkedin'),
            'tiktok_link': settings.SOCIAL_LINKS.get('tiktok'),
        }

        html_template_path = os.path.join(settings.BASE_DIR, 'apps', 'email_service', 'templates', 'generic_email.html')
        txt_template_path = os.path.join(settings.BASE_DIR, 'apps', 'email_service', 'templates', 'generic_email.txt')

        if not os.path.exists(html_template_path):
            raise FileNotFoundError(f"HTML template not found at {html_template_path}")
        if not os.path.exists(txt_template_path):
            raise FileNotFoundError(f"Text template not found at {txt_template_path}")

        with open(html_template_path, 'r', encoding='utf-8') as f:
            html_template = Template(f.read())
        html_message = html_template.render(Context(context))

        with open(txt_template_path, 'r', encoding='utf-8') as f:
            txt_template = Template(f.read())
        plain_message = txt_template.render(Context(context))

        send_mail(
            subject=subject,
            message=plain_message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[user_email],
            html_message=html_message,
            fail_silently=False,
        )

        return {"status": "success", "email_type": email_type, "email": user_email}
    except Exception as e:
        return {"status": "failure", "email_type": email_type, "email": user_email, "error": str(e)}


class HMACAuthentication(authentication.BaseAuthentication):
    def authenticate(self, request):
        timestamp = request.headers.get('X-Timestamp')
        signature = request.headers.get('X-Signature')

        # Check for missing headers
        if not timestamp or not signature:
            raise exceptions.AuthenticationFailed('Missing X-Timestamp or X-Signature header')

        # Prevent replay attacks (5-minute window)
        try:
            timestamp = int(timestamp)
            current_time = int(time.time())
            if abs(current_time - timestamp) > 300:  # 5 minutes
                raise exceptions.AuthenticationFailed('Timestamp too old or invalid')
        except ValueError:
            raise exceptions.AuthenticationFailed('Invalid timestamp format')

        # Calculate expected signature
        # Ensure consistent JSON serialization (sorted keys, no extra whitespace)
        payload = json.dumps(request.data, sort_keys=True, separators=(',', ':'))
        message = f"{timestamp}:{payload}".encode('utf-8')
        expected_signature = hmac.new(
            settings.EMAIL_SERVICE_SECRET.encode('utf-8'),
            message,
            hashlib.sha256
        ).hexdigest()

        # Compare signatures securely
        if not hmac.compare_digest(signature.encode('utf-8'), expected_signature.encode('utf-8')):
            raise exceptions.AuthenticationFailed('Invalid HMAC signature')

        return (None, None)  # No user object, just allow the request