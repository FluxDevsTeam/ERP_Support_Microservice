# apps/email_service/send_real_email_test.py
import os
import sys
import django
import json
import requests
import jwt
from datetime import datetime, timedelta, timezone

# Add project root and apps to Python path
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, project_root)
sys.path.insert(0, os.path.join(project_root, 'apps'))

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.development')
django.setup()

from django.conf import settings

def send_real_email_test():
    """Send a real email to your inbox"""
    print("🚀 Sending REAL Email Test")
    print("=" * 40)
    
    # Generate JWT token (same as your tests)
    payload = {
        'type': 'microservice',
        'service': 'real-test',
        'iat': datetime.now(timezone.utc),
        'exp': datetime.now(timezone.utc) + timedelta(minutes=5)
    }
    token = jwt.encode(payload, settings.SUPPORT_JWT_SECRET_KEY, algorithm='HS256')
    
    headers = {
        'Support-Microservice-Auth': token,
        'Content-Type': 'application/json'
    }
    
    # Your email service URL
    email_service_url = "http://127.0.0.1:8888/api/v1/email-service/send-email/"
    
    # Test email data
    email_data = {
        'user_email': 'suskidee@gmail.com',
        'email_type': 'general',
        'subject': '🚀 REAL TEST: Email Service is Working!',
        'action': 'real_test',
        'message': 'Congratulations! If you receive this email, your email service is working perfectly! 🎉 This is a real test email sent directly to your inbox.',
        'link': 'https://github.com',
        'link_text': 'Visit GitHub'
    }
    
    print(f"Sending REAL email to: suskidee@gmail.com")
    print(f"Using URL: {email_service_url}")
    print(f"Email data: {json.dumps(email_data, indent=2)}")
    
    try:
        response = requests.post(
            email_service_url,
            json=email_data,
            headers=headers,
            timeout=30
        )
        
        print(f"\nResponse Status: {response.status_code}")
        print(f"Response Body: {json.dumps(response.json(), indent=2)}")
        
        if response.status_code == 200:
            response_data = response.json()
            if response_data.get('status') == 'sent':
                print(f"\n✅ Email sent successfully via {response_data.get('processing_method', 'unknown')} method!")
                print("📧 Email should arrive at: suskidee@gmail.com")
            elif response_data.get('status') == 'queued':
                print("\n✅ Email queued successfully! Check your inbox in a few minutes.")
                print("📧 Email should arrive at: suskidee@gmail.com")
            else:
                print(f"\n⚠️ Email status: {response_data.get('status')}")
                print("📧 Check your inbox for the email.")
        else:
            print(f"\n❌ Failed to send email: {response.text}")
            
    except Exception as e:
        print(f"\n❌ Error: {e}")

if __name__ == "__main__":
    send_real_email_test()