# apps/email_service/tests/test_email_service.py
import unittest
import requests
import hmac
import hashlib
import base64
from datetime import datetime
from django.test import TestCase
from apps.email_service.models import EmailLog, EmailConfiguration
import json
import logging

logger = logging.getLogger('apps.email_service')

class EmailServiceTests(TestCase):
    def setUp(self):
        """Set up test data."""
        logger.debug("Setting up EmailServiceTests")
        # Create or update EmailConfiguration instance
        try:
            self.email_config, created = EmailConfiguration.objects.get_or_create(
                id=1,  # Assuming singleton pattern with id=1
                defaults={
                    'support_email': 'support@example.com',
                    'brand_name': 'TestBrand',
                    'site_url': 'https://example.com',
                    'hmac_secret_key': 'iwbefebvWBFBIRYBGHbvbvUBBWEJFNVDJVDS11JHVQEF2343241HB41H4B4H3141414J'
                }
            )
            if not created:
                self.email_config.hmac_secret_key = 'iwbefebvWBFBIRYBGHbvbvUBBWEJFNVDJVDS11JHVQEF2343241HB41H4B4H3141414J'
                self.email_config.save()
                logger.debug("Updated existing EmailConfiguration with new hmac_secret_key")
            logger.debug(f"EmailConfiguration hmac_secret_key: {self.email_config.hmac_secret_key}")
        except Exception as e:
            logger.error(f"Failed to set up EmailConfiguration: {str(e)}")
            raise

        self.hmac_secret = self.email_config.hmac_secret_key
        self.service_name = 'identity-ms'
        self.support_ms_url = 'http://localhost:8888/api/v1/email-service/send-email/'  # Port 8888

    def generate_hmac_signature(self, method, path, timestamp, payload):
        """Generate HMAC signature for the request."""
        payload_str = json.dumps(payload, separators=(',', ':'))  # Match server's request.body.decode('utf-8')
        message = f"{method}{path}{timestamp}{payload_str}"
        logger.debug(f"HMAC Message: {message}")
        logger.debug(f"Payload String: {payload_str}")
        signature = hmac.new(
            key=self.hmac_secret.encode('utf-8'),
            msg=message.encode('utf-8'),
            digestmod=hashlib.sha256
        ).digest()
        signature_b64 = base64.b64encode(signature).decode('utf-8')
        logger.debug(f"Generated HMAC Signature: {signature_b64}")
        return signature_b64

    def test_send_email_to_suskidee(self):
        """Test sending an email to suskidee@gmail.com."""
        email_data = {
            'user_email': 'suskidee@gmail.com',
            'email_type': 'otp',
            'subject': 'Your OTP Code',
            'action': 'verify',
            'message': 'Please use the OTP below to verify your account.',
            'otp': '123456'
        }
        
        timestamp = datetime.now().isoformat()
        signature = self.generate_hmac_signature(
            method='POST',
            path='/api/v1/email-service/send-email/',
            timestamp=timestamp,
            payload=email_data
        )
        
        headers = {
            'X-HMAC-Signature': signature,
            'X-Timestamp': timestamp,
            'X-Service-Name': self.service_name,
            'Content-Type': 'application/json'
        }
        
        payload_str = json.dumps(email_data, separators=(',', ':'))
        logger.debug(f"Sending request with headers: {headers}")
        logger.debug(f"Request body: {payload_str}")
        response = requests.post(self.support_ms_url, data=payload_str.encode('utf-8'), headers=headers)
        
        if response.status_code != 200:
            logger.error(f"Request failed: {response.status_code} - {response.text}")
            self.fail(f"Request failed with status {response.status_code}: {response.text}")
        
        response_data = response.json()
        self.assertEqual(response_data['status'], 'queued', f"Email not queued: {response_data}")
        self.assertEqual(response_data['email'], 'suskidee@gmail.com', "Email address mismatch")
        
        # Verify email log was created
        try:
            email_log = EmailLog.objects.get(email='suskidee@gmail.com')
            self.assertEqual(email_log.email_type, 'otp', "Email type mismatch")
            self.assertEqual(email_log.status, 'queued', "Email log status not queued")
        except EmailLog.DoesNotExist:
            self.fail("EmailLog not created for suskidee@gmail.com")

if __name__ == '__main__':
    unittest.main()