# apps/email_service/tasks.py
from celery import shared_task, current_app
from celery.exceptions import MaxRetriesExceededError
from .utils import send_generic_email
from .models import EmailLog
from django.utils import timezone

def is_celery_healthy():
    try:
        current_app.connection().ensure_connection(max_retries=0)
        return True
    except Exception:
        return False

@shared_task(bind=True, max_retries=3)
def send_generic_email_task(self, user_email, email_type, subject, action, message, otp=None, link=None, link_text=None):
    # Create email log entry
    email_log = EmailLog.objects.create(
        email=user_email,
        email_type=email_type,
        subject=subject,
        action=action,
        message=message,
        otp=otp,
        link=link,
        link_text=link_text,
        status='queued'
    )

    try:
        result = send_generic_email(
            user_email=user_email,
            email_type=email_type,
            subject=subject,
            action=action,
            message=message,
            otp=otp,
            link=link,
            link_text=link_text
        )

        # Update log on success
        email_log.status = result['status']
        email_log.sent_at = timezone.now()
        if result['status'] == 'failure':
            email_log.error = result['error']
        email_log.save()

        return result
    except Exception as e:
        try:
            # Update log on failure before retry
            email_log.status = 'failed'
            email_log.error = str(e)
            email_log.save()
            self.retry(exc=e, countdown=30)
        except MaxRetriesExceededError:
            # Final failure after retries
            email_log.status = 'failed'
            email_log.error = f"Max retries exceeded: {str(e)}"
            email_log.save()
            return {"status": "failure", "email_type": email_type, "email": user_email, "error": str(e)}