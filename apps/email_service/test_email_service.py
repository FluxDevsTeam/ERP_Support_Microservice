# apps/email_service/tests/test_email_service.py
import os
import django
import sys
import json
from django.test import TestCase
from django.conf import settings
from rest_framework.test import APIClient
from rest_framework import status
import jwt
from datetime import datetime, timedelta
from unittest.mock import patch, MagicMock

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'your_project.settings')
django.setup()

from apps.email_service.models import EmailLog, EmailConfiguration
from apps.email_service.serializers import SendEmailSerializer

class EmailEndpointTest(TestCase):
    def setUp(self):
        """Set up test data and client"""
        self.client = APIClient()
        self.email_url = "/api/v1/email-service/send-email/"
        self.test_email = "suskidee@gmail.com"
        
        # Ensure email configuration exists
        EmailConfiguration.get_instance()

    def generate_microservice_token(self, service_name="test-service", expires_minutes=5):
        """Generate a valid microservice JWT token"""
        payload = {
            'type': 'microservice',
            'service': service_name,
            'iat': datetime.utcnow(),
            'exp': datetime.utcnow() + timedelta(minutes=expires_minutes)
        }
        return jwt.encode(payload, settings.SUPPORT_JWT_SECRET_KEY, algorithm='HS256')

    def test_minimal_email_with_valid_jwt(self):
        """Test sending email with only user_email (minimal data)"""
        print("\n=== Test 1: Minimal email with only user_email ===")
        
        token = self.generate_microservice_token()
        
        # Minimal data - only required field
        email_data = {
            'user_email': self.test_email
        }
        
        response = self.client.post(
            self.email_url,
            data=json.dumps(email_data),
            content_type='application/json',
            HTTP_SUPPORT_MICROSERVICE_AUTH=token
        )
        
        print(f"Status Code: {response.status_code}")
        print(f"Response: {json.dumps(response.json(), indent=2)}")
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.json()['status'], 'queued')
        self.assertEqual(response.json()['email'], self.test_email)
        self.assertEqual(response.json()['email_type'], 'general')  # Should use default

    def test_email_with_custom_message_only(self):
        """Test sending email with custom message only"""
        print("\n=== Test 2: Email with custom message only ===")
        
        token = self.generate_microservice_token()
        
        email_data = {
            'user_email': self.test_email,
            'message': 'Welcome to our platform! This is a custom message.'
        }
        
        response = self.client.post(
            self.email_url,
            data=json.dumps(email_data),
            content_type='application/json',
            HTTP_SUPPORT_MICROSERVICE_AUTH=token
        )
        
        print(f"Status Code: {response.status_code}")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_otp_email_with_otp_field(self):
        """Test sending OTP email with otp field"""
        print("\n=== Test 3: OTP email with otp field ===")
        
        token = self.generate_microservice_token()
        
        email_data = {
            'user_email': self.test_email,
            'email_type': 'otp',
            'otp': '123456'
        }
        
        response = self.client.post(
            self.email_url,
            data=json.dumps(email_data),
            content_type='application/json',
            HTTP_SUPPORT_MICROSERVICE_AUTH=token
        )
        
        print(f"Status Code: {response.status_code}")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_otp_email_without_otp_field(self):
        """Test sending OTP email without otp field (should work now)"""
        print("\n=== Test 4: OTP email without otp field (should work) ===")
        
        token = self.generate_microservice_token()
        
        email_data = {
            'user_email': self.test_email,
            'email_type': 'otp'
            # No otp field - should use defaults
        }
        
        response = self.client.post(
            self.email_url,
            data=json.dumps(email_data),
            content_type='application/json',
            HTTP_SUPPORT_MICROSERVICE_AUTH=token
        )
        
        print(f"Status Code: {response.status_code}")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_reset_link_email_with_link(self):
        """Test sending reset link email with link field"""
        print("\n=== Test 5: Reset link email with link field ===")
        
        token = self.generate_microservice_token()
        
        email_data = {
            'user_email': self.test_email,
            'email_type': 'reset_link',
            'link': 'https://example.com/reset-password'
        }
        
        response = self.client.post(
            self.email_url,
            data=json.dumps(email_data),
            content_type='application/json',
            HTTP_SUPPORT_MICROSERVICE_AUTH=token
        )
        
        print(f"Status Code: {response.status_code}")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_reset_link_email_without_link(self):
        """Test sending reset link email without link field (should work now)"""
        print("\n=== Test 6: Reset link email without link field (should work) ===")
        
        token = self.generate_microservice_token()
        
        email_data = {
            'user_email': self.test_email,
            'email_type': 'reset_link'
            # No link field - should use defaults
        }
        
        response = self.client.post(
            self.email_url,
            data=json.dumps(email_data),
            content_type='application/json',
            HTTP_SUPPORT_MICROSERVICE_AUTH=token
        )
        
        print(f"Status Code: {response.status_code}")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_confirmation_email_complete(self):
        """Test sending complete confirmation email"""
        print("\n=== Test 7: Complete confirmation email ===")
        
        token = self.generate_microservice_token()
        
        email_data = {
            'user_email': self.test_email,
            'email_type': 'confirmation',
            'subject': 'Confirm Your Account',
            'action': 'account_confirmation',
            'message': 'Please confirm your account by clicking the link below.',
            'link': 'https://example.com/confirm',
            'link_text': 'Confirm Account'
        }
        
        response = self.client.post(
            self.email_url,
            data=json.dumps(email_data),
            content_type='application/json',
            HTTP_SUPPORT_MICROSERVICE_AUTH=token
        )
        
        print(f"Status Code: {response.status_code}")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_email_without_jwt(self):
        """Test sending email without JWT token (should fail)"""
        print("\n=== Test 8: Email without JWT (should fail) ===")
        
        email_data = {
            'user_email': self.test_email,
            'message': 'This should fail without JWT.'
        }
        
        response = self.client.post(
            self.email_url,
            data=json.dumps(email_data),
            content_type='application/json'
        )
        
        print(f"Status Code: {response.status_code}")
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_email_with_expired_jwt(self):
        """Test sending email with expired JWT token (should fail)"""
        print("\n=== Test 9: Email with expired JWT (should fail) ===")
        
        payload = {
            'type': 'microservice',
            'service': 'test-service',
            'iat': datetime.utcnow() - timedelta(hours=1),
            'exp': datetime.utcnow() - timedelta(minutes=30)
        }
        expired_token = jwt.encode(payload, settings.SUPPORT_JWT_SECRET_KEY, algorithm='HS256')
        
        email_data = {
            'user_email': self.test_email,
            'message': 'This should fail with expired JWT.'
        }
        
        response = self.client.post(
            self.email_url,
            data=json.dumps(email_data),
            content_type='application/json',
            HTTP_SUPPORT_MICROSERVICE_AUTH=expired_token
        )
        
        print(f"Status Code: {response.status_code}")
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_email_with_invalid_jwt_secret(self):
        """Test sending email with JWT signed with wrong secret (should fail)"""
        print("\n=== Test 10: Email with invalid JWT secret (should fail) ===")
        
        payload = {
            'type': 'microservice',
            'service': 'test-service',
            'iat': datetime.utcnow(),
            'exp': datetime.utcnow() + timedelta(minutes=5)
        }
        invalid_token = jwt.encode(payload, 'wrong-secret-key', algorithm='HS256')
        
        email_data = {
            'user_email': self.test_email,
            'message': 'This should fail with invalid JWT secret.'
        }
        
        response = self.client.post(
            self.email_url,
            data=json.dumps(email_data),
            content_type='application/json',
            HTTP_SUPPORT_MICROSERVICE_AUTH=invalid_token
        )
        
        print(f"Status Code: {response.status_code}")
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_email_with_invalid_email(self):
        """Test sending email with invalid email format (should fail)"""
        print("\n=== Test 11: Email with invalid email format (should fail) ===")
        
        token = self.generate_microservice_token()
        
        email_data = {
            'user_email': 'invalid-email',
            'message': 'This should fail with invalid email.'
        }
        
        response = self.client.post(
            self.email_url,
            data=json.dumps(email_data),
            content_type='application/json',
            HTTP_SUPPORT_MICROSERVICE_AUTH=token
        )
        
        print(f"Status Code: {response.status_code}")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_email_with_missing_user_email(self):
        """Test sending email without user_email (should fail)"""
        print("\n=== Test 12: Email without user_email (should fail) ===")
        
        token = self.generate_microservice_token()
        
        email_data = {
            'message': 'This should fail without user_email.'
        }
        
        response = self.client.post(
            self.email_url,
            data=json.dumps(email_data),
            content_type='application/json',
            HTTP_SUPPORT_MICROSERVICE_AUTH=token
        )
        
        print(f"Status Code: {response.status_code}")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_email_different_service_names(self):
        """Test sending email with different microservice names"""
        print("\n=== Test 13: Testing different microservice names ===")
        
        services = ['identity-ms', 'notification-ms', 'payment-ms', 'support-ms']
        
        for service in services:
            print(f"Testing with service: {service}")
            token = self.generate_microservice_token(service_name=service)
            
            email_data = {
                'user_email': self.test_email,
                'message': f'Test email from {service} service.'
            }
            
            response = self.client.post(
                self.email_url,
                data=json.dumps(email_data),
                content_type='application/json',
                HTTP_SUPPORT_MICROSERVICE_AUTH=token
            )
            
            print(f"  Status: {response.status_code}")
            self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_email_with_additional_fields(self):
        """Test sending email with additional custom fields"""
        print("\n=== Test 14: Email with additional custom fields ===")
        
        token = self.generate_microservice_token()
        
        email_data = {
            'user_email': self.test_email,
            'subject': 'Custom Notification',
            'message': 'This email has additional fields.',
            'custom_field': 'Custom value',
            'another_field': 'Another value',
            'user_name': 'John Doe'
        }
        
        response = self.client.post(
            self.email_url,
            data=json.dumps(email_data),
            content_type='application/json',
            HTTP_SUPPORT_MICROSERVICE_AUTH=token
        )
        
        print(f"Status Code: {response.status_code}")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_all_email_types_with_minimal_data(self):
        """Test all email types with minimal required data"""
        print("\n=== Test 15: All email types with minimal data ===")
        
        token = self.generate_microservice_token()
        email_types = ['otp', 'confirmation', 'reset_link', 'general']
        
        for email_type in email_types:
            print(f"Testing {email_type} with minimal data...")
            
            email_data = {
                'user_email': self.test_email,
                'email_type': email_type
            }
            
            response = self.client.post(
                self.email_url,
                data=json.dumps(email_data),
                content_type='application/json',
                HTTP_SUPPORT_MICROSERVICE_AUTH=token
            )
            
            print(f"  {email_type}: Status {response.status_code}")
            self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_email_log_creation_celery_unavailable(self):
        """Test email log creation when Celery is unavailable"""
        print("\n=== Test 17: Email log creation (Celery unavailable) ===")
        
        # Don't mock Celery - let it use the actual behavior
        token = self.generate_microservice_token()
        
        # Clear existing logs
        EmailLog.objects.all().delete()
        
        email_data = {
            'user_email': self.test_email,
            'subject': 'Test Celery Unavailable',
            'message': 'Testing when Celery is down.'
        }
        
        response = self.client.post(
            self.email_url,
            data=json.dumps(email_data),
            content_type='application/json',
            HTTP_SUPPORT_MICROSERVICE_AUTH=token
        )
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Verify email log was created
        email_log = EmailLog.objects.last()
        self.assertIsNotNone(email_log)
        self.assertEqual(email_log.email, self.test_email)
        
        # When Celery is unavailable, status could be 'pending' or 'queued'
        # Both are valid, so we just check that it's one of them
        self.assertIn(email_log.status, ['queued', 'pending'])


def run_all_tests():
    """Function to run all tests and print summary"""
    print("🚀 Starting Email Service Endpoint Tests")
    print("=" * 50)
    
    test_instance = EmailEndpointTest()
    test_instance.setUp()
    
    tests = [
        test_instance.test_minimal_email_with_valid_jwt,
        test_instance.test_email_with_custom_message_only,
        test_instance.test_otp_email_with_otp_field,
        test_instance.test_otp_email_without_otp_field,
        test_instance.test_reset_link_email_with_link,
        test_instance.test_reset_link_email_without_link,
        test_instance.test_confirmation_email_complete,
        test_instance.test_email_without_jwt,
        test_instance.test_email_with_expired_jwt,
        test_instance.test_email_with_invalid_jwt_secret,
        test_instance.test_email_with_invalid_email,
        test_instance.test_email_with_missing_user_email,
        test_instance.test_email_different_service_names,
        test_instance.test_email_with_additional_fields,
        test_instance.test_all_email_types_with_minimal_data,
        test_instance.test_email_log_creation,
        test_instance.test_email_log_creation_celery_unavailable,
    ]
    
    passed = 0
    failed = 0
    
    for test in tests:
        try:
            test()
            passed += 1
            print("✅ PASS\n")
        except AssertionError as e:
            failed += 1
            print(f"❌ FAIL: {e}\n")
        except Exception as e:
            failed += 1
            print(f"💥 ERROR: {e}\n")
    
    print("=" * 50)
    print(f"📊 Test Summary: {passed} passed, {failed} failed, {len(tests)} total")
    
    if failed == 0:
        print("🎉 All tests passed! Email service is working correctly.")
    else:
        print("💥 Some tests failed. Check the output above for details.")
    
    return passed, failed


if __name__ == "__main__":
    run_all_tests()