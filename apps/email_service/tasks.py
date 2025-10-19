# apps/email_service/tasks.py
from celery import shared_task, current_app
from .utils import send_generic_email
from .models import EmailLog
from django.utils import timezone

def is_celery_healthy():
    try:
        current_app.connection().ensure_connection(max_retries=0)
        return True
    except Exception:
        return False

@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def send_generic_email_task(self, user_email, email_type=None, subject=None, action=None, message=None, otp=None, link=None, link_text=None, email_log_id=None, **kwargs):

    start_time = timezone.now()
    email_log = None

    try:
        if email_log_id:
            try:
                email_log = EmailLog.objects.get(id=email_log_id)
            except EmailLog.DoesNotExist:
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
        else:
            # Create new log if no ID provided
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

        email_log.status = 'processing'
        email_log.save(update_fields=['status'])

        # Send email with all parameters
        result = send_generic_email(
            user_email=user_email,
            email_type=email_type,
            subject=subject,
            action=action,
            message=message,
            otp=otp,
            link=link,
            link_text=link_text,
            **kwargs  # Pass any additional fields
        )

        # Update log on success
        if result['status'] == 'success':
            email_log.status = 'sent'
            email_log.sent_at = timezone.now()
            email_log.save(update_fields=['status', 'sent_at'])
            
            # Log performance metrics
            duration = (timezone.now() - start_time).total_seconds()

            return {"status": "success", "email_log_id": email_log.id}
        else:
            email_log.status = 'failed'
            email_log.error = result['error']
            email_log.save(update_fields=['status', 'error'])
            
            # Retry on failure with exponential backoff
            if self.request.retries < self.max_retries:
                retry_delay = 60 * (2 ** self.request.retries)
                raise self.retry(exc=Exception(f"Email sending failed: {result.get('error')}"), countdown=retry_delay)
            
            return {"status": "failure", "email_log_id": email_log.id, "error": result.get('error')}

    except Exception as e:
        error_msg = str(e)
        
        # Update log on failure before retry
        if email_log:
            email_log.status = 'failed'
            email_log.error = error_msg
            email_log.save(update_fields=['status', 'error'])
        
        # Retry on failure with exponential backoff
        if self.request.retries < self.max_retries:
            retry_delay = 60 * (2 ** self.request.retries)
            raise self.retry(exc=e, countdown=retry_delay)
        else:
            # Final failure after retries
            if email_log:
                email_log.error = f"Max retries exceeded: {error_msg}"
                email_log.save(update_fields=['error'])
            return {"status": "failure", "email": user_email, "error": f"Max retries exceeded: {error_msg}"}