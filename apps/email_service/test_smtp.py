# apps/email_service/test_smtp.py
import os
import sys
import django

# Add project root and apps to Python path
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, project_root)
sys.path.insert(0, os.path.join(project_root, 'apps'))

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.development')
django.setup()

from django.core.mail import send_mail
from django.conf import settings

def test_smtp_directly():
    """Test SMTP connection directly"""
    print("🧪 Testing SMTP Connection Directly")
    print("=" * 40)
    
    try:
        send_mail(
            subject='🧪 Direct SMTP Test',
            message='This is a direct SMTP test from Django.',
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=['suskidee@gmail.com'],
            fail_silently=False,
        )
        print("✅ SMTP test email sent successfully!")
        print("📧 Check your inbox for the test email.")
    except Exception as e:
        print(f"❌ SMTP failed: {e}")
        print("\n🔧 Troubleshooting steps:")
        print("1. Check EMAIL_HOST, EMAIL_PORT in settings")
        print("2. Verify EMAIL_HOST_USER and EMAIL_HOST_PASSWORD")
        print("3. For Gmail: Enable 2FA and use App Password")
        print("4. Check if your email provider allows SMTP")

if __name__ == "__main__":
    test_smtp_directly()