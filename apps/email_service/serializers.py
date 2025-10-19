# apps/email_service/serializers.py
import logging
from rest_framework import serializers
from .models import EmailLog, EmailConfiguration

logger = logging.getLogger(__name__)


class EmailLogSerializer(serializers.ModelSerializer):
    """Serializer for EmailLog model"""
    
    class Meta:
        model = EmailLog
        fields = [
            'id', 'email', 'email_type', 'subject', 'action', 
            'message', 'otp', 'link', 'link_text', 'status',
            'created_at', 'sent_at', 'error'
        ]
        read_only_fields = ['id', 'created_at', 'sent_at', 'error']


class SendEmailSerializer(serializers.Serializer):
    """Serializer for sending emails"""
    
    EMAIL_TYPES = [
        ('otp', 'One-Time Password'),
        ('confirmation', 'Confirmation Email'),
        ('reset_link', 'Password Reset Link'),
    ]
    
    user_email = serializers.EmailField(required=True)
    email_type = serializers.ChoiceField(choices=EMAIL_TYPES, required=True)
    subject = serializers.CharField(max_length=255, required=True)
    action = serializers.CharField(max_length=100, required=True)
    message = serializers.CharField(required=True)
    otp = serializers.CharField(max_length=10, required=False, allow_null=True, allow_blank=True)
    link = serializers.URLField(required=False, allow_null=True, allow_blank=True)
    link_text = serializers.CharField(max_length=100, required=False, allow_null=True, allow_blank=True)
    
    def validate_user_email(self, value):
        """Validate email format"""
        if not value or '@' not in value:
            raise serializers.ValidationError("Invalid email format")
        return value.lower().strip()
    
    def validate(self, data):
        """Cross-field validation"""
        email_type = data.get('email_type')
        
        if email_type == 'otp' and not data.get('otp'):
            raise serializers.ValidationError({
                'otp': 'OTP is required for otp email type'
            })
        
        if email_type == 'reset_link':
            if not data.get('link'):
                raise serializers.ValidationError({
                    'link': 'Link is required for reset_link email type'
                })
            if not data.get('link_text'):
                data['link_text'] = 'Reset Password'  # Default value
        
        return data


class EmailStatsSerializer(serializers.Serializer):
    """Serializer for email statistics"""
    
    total_emails = serializers.IntegerField(read_only=True)
    successful_emails = serializers.IntegerField(read_only=True)
    failed_emails = serializers.IntegerField(read_only=True)
    pending_emails = serializers.IntegerField(read_only=True)
    success_rate = serializers.FloatField(read_only=True)
    
    
class EmailTypeStatsSerializer(serializers.Serializer):
    """Serializer for email type statistics"""
    
    email_type = serializers.CharField(read_only=True)
    count = serializers.IntegerField(read_only=True)
    success_rate = serializers.FloatField(read_only=True)


class EmailConfigurationSerializer(serializers.ModelSerializer):
    """Serializer for EmailConfiguration model"""
    
    class Meta:
        model = EmailConfiguration
        fields = [
            'id', 'support_email', 'support_phone_number', 'brand_name',
            'brand_logo', 'terms_of_service', 'site_url', 'hmac_secret_key',
            'facebook_link', 'instagram_link', 'twitter_link', 'linkedin_link',
            'tiktok_link', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
        extra_kwargs = {
            'hmac_secret_key': {'write_only': True}
        }
    
    def validate(self, data):
        """Custom validation"""
        return data