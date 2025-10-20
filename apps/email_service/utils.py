import os
from django.core.mail import send_mail
from django.template import Template, Context
from datetime import datetime
from django.conf import settings
from drf_yasg.utils import swagger_auto_schema
from .pagination import PAGINATION_PARAMS


def swagger_helper(tags, model):
    def decorators(func):
        descriptions = {
            "list": f"Retrieve a list of {model}",
            "retrieve": f"Retrieve details of a specific {model}",
            "create": f"Create a new {model}",
            "partial_update": f"Update a {model}",
            "destroy": f"Delete a {model}",
        }

        action_type = func.__name__
        get_description = descriptions.get(action_type, f"{action_type} {model}")
        return swagger_auto_schema(manual_parameters=PAGINATION_PARAMS, operation_id=f"{action_type} {model}", operation_description=get_description, tags=[tags])(func)

    return decorators



def send_generic_email(user_email, email_type=None, subject=None, action=None, message=None, otp=None, link=None, link_text=None, **kwargs):
    from .models import EmailConfiguration
    try:
        # Basic email validation
        if not user_email or not isinstance(user_email, str):
            raise ValueError("Invalid user_email: must be a non-empty string")

        if '@' not in user_email or '.' not in user_email.split('@')[-1]:
            raise ValueError("Invalid email format")

        user_email = user_email.strip().lower()
        
        # Clean and sanitize inputs - only if provided
        subject = subject.strip() if subject else None
        action = action.strip() if action else None
        message = message.strip() if message else None
        otp = otp.strip() if otp else None
        link = link.strip() if link else None
        link_text = link_text.strip() if link_text else None

        email_config = EmailConfiguration.get_instance()

        # Build dynamic context with all available data
        context = {
            'subject': subject or 'Notification',
            'action': action,
            'message': message,
            'otp': otp,
            'link': link,
            'link_text': link_text,
            'site_url': email_config.site_url or getattr(settings, 'SITE_URL', ''),
            'current_year': datetime.now().year,
            'support_email': email_config.support_email,
            'support_phone_number': email_config.support_phone_number,
            'brand_name': email_config.brand_name or 'KidsDesignCompany',
            'brand_logo': email_config.get_brand_logo_url(),
            'terms_of_service': email_config.terms_of_service,
            'social_true': email_config.has_social_links(),
            'fb_link': email_config.facebook_link,
            'ig_link': email_config.instagram_link,
            'x_link': email_config.twitter_link,
            'linkedin_link': email_config.linkedin_link,
            'tiktok_link': email_config.tiktok_link,
        }
        
        # Add any additional kwargs to context
        context.update(kwargs)

        # Template paths
        html_template_path = os.path.join(settings.BASE_DIR, 'apps', 'email_service', 'templates', 'generic_email.html')
        txt_template_path = os.path.join(settings.BASE_DIR, 'apps', 'email_service', 'templates', 'generic_email.txt')

        # Validate template files exist
        if not os.path.exists(html_template_path):
            raise FileNotFoundError(f"HTML template not found at {html_template_path}")
        if not os.path.exists(txt_template_path):
            raise FileNotFoundError(f"Text template not found at {txt_template_path}")

        # Read and render templates
        try:
            with open(html_template_path, 'r', encoding='utf-8') as f:
                html_template = Template(f.read())
            html_message = html_template.render(Context(context))
        except Exception as e:
            raise RuntimeError(f"Failed to render HTML template: {str(e)}")

        try:
            with open(txt_template_path, 'r', encoding='utf-8') as f:
                txt_template = Template(f.read())
            plain_message = txt_template.render(Context(context))
        except Exception as e:
            raise RuntimeError(f"Failed to render text template: {str(e)}")

        # Validate email configuration
        from_email = getattr(settings, 'DEFAULT_FROM_EMAIL', None)
        if not from_email:
            raise RuntimeError("DEFAULT_FROM_EMAIL setting is not configured")

        # Send email
        send_mail(
            subject=subject or 'Notification',
            message=plain_message,
            from_email=from_email,
            recipient_list=[user_email],
            html_message=html_message,
            fail_silently=False,
        )

        return {"status": "success", "email": user_email}

    except ValueError as e:
        return {"status": "failure", "email": user_email,
                "error": f"Validation error: {str(e)}"}
    except FileNotFoundError as e:
        return {"status": "failure", "email": user_email,
                "error": f"Template error: {str(e)}"}
    except RuntimeError as e:
        return {"status": "failure", "email": user_email,
                "error": f"Configuration error: {str(e)}"}
    except Exception as e:
        return {"status": "failure", "email": user_email,
                "error": f"Unexpected error: {str(e)}"}