import os
from django.core.mail import send_mail
from django.template import Template, Context
from datetime import datetime
from django.conf import settings


def send_generic_email(user_email, email_type, subject, action, message, otp=None, link=None, link_text=None):
    from .models import EmailConfiguration
    try:
        if not user_email or not isinstance(user_email, str):
            raise ValueError("Invalid user_email: must be a non-empty string")

        if '@' not in user_email or '.' not in user_email.split('@')[-1]:
            raise ValueError("Invalid email format")

        valid_email_types = ['otp', 'confirmation', 'reset_link']
        if email_type not in valid_email_types:
            raise ValueError(f"Invalid email_type: must be one of {valid_email_types}")

        if not subject or not isinstance(subject, str) or len(subject.strip()) == 0:
            raise ValueError("Invalid subject: must be a non-empty string")

        if not message or not isinstance(message, str) or len(message.strip()) == 0:
            raise ValueError("Invalid message: must be a non-empty string")

        if email_type == 'otp' and (not otp or not isinstance(otp, str)):
            raise ValueError("OTP is required for otp email type")

        if email_type == 'reset_link' and (not link or not isinstance(link, str)):
            raise ValueError("Link is required for reset_link email type")

        user_email = user_email.strip().lower()
        subject = subject.strip()
        action = action.strip() if action else ''
        message = message.strip()

        email_config = EmailConfiguration.get_instance()

        context = {
            'subject': subject,
            'action': action,
            'message': message,
            'otp': otp,
            'link': link,
            'link_text': link_text or 'Click here',
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
            subject=subject,
            message=plain_message,
            from_email=from_email,
            recipient_list=[user_email],
            html_message=html_message,
            fail_silently=False,
        )

        return {"status": "success", "email_type": email_type, "email": user_email}

    except ValueError as e:
        return {"status": "failure", "email_type": email_type, "email": user_email,
                "error": f"Validation error: {str(e)}"}
    except FileNotFoundError as e:
        return {"status": "failure", "email_type": email_type, "email": user_email,
                "error": f"Template error: {str(e)}"}
    except RuntimeError as e:
        return {"status": "failure", "email_type": email_type, "email": user_email,
                "error": f"Configuration error: {str(e)}"}
    except Exception as e:
        return {"status": "failure", "email_type": email_type, "email": user_email,
                "error": f"Unexpected error: {str(e)}"}
