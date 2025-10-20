# apps/email_service/check_email_logs.py
import os
import sys
import django

# Add project root and apps to Python path
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, project_root)
sys.path.insert(0, os.path.join(project_root, 'apps'))

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.development')
django.setup()

from apps.email_service.models import EmailLog

def check_email_logs():
    """Check the status of email logs"""
    print("📊 Checking Email Logs")
    print("=" * 40)
    
    logs = EmailLog.objects.all().order_by('-created_at')[:10]
    
    if not logs:
        print("No email logs found.")
        return
    
    for log in logs:
        print(f"📧 {log.email} | {log.status} | {log.subject} | {log.created_at}")
        if log.error:
            print(f"   ❌ Error: {log.error}")
    
    print(f"\nTotal logs: {EmailLog.objects.count()}")
    print(f"Queued: {EmailLog.objects.filter(status='queued').count()}")
    print(f"Sent: {EmailLog.objects.filter(status='sent').count()}")
    print(f"Failed: {EmailLog.objects.filter(status='failed').count()}")

if __name__ == "__main__":
    check_email_logs()