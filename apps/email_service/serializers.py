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
    
    EMAIL_TYPES = [
        ('otp', 'One-Time Password'),
        ('confirmation', 'Confirmation Email'),
        ('reset_link', 'Password Reset Link'),
        ('general', 'General Notification'),
    ]
    
    user_email = serializers.EmailField(required=True)
    email_type = serializers.ChoiceField(choices=EMAIL_TYPES, required=False, default='general')
    subject = serializers.CharField(max_length=255, required=False, default='Notification')
    action = serializers.CharField(max_length=100, required=False, default='notification')
    message = serializers.CharField(required=False, default='You have a new notification.')
    otp = serializers.CharField(max_length=10, required=False, allow_null=True, allow_blank=True)
    link = serializers.URLField(required=False, allow_null=True, allow_blank=True)
    link_text = serializers.CharField(max_length=100, required=False, allow_null=True, allow_blank=True)
    
    def validate_user_email(self, value):
        """Validate email format"""
        if not value or '@' not in value:
            raise serializers.ValidationError("Invalid email format")
        return value.lower().strip()
    
    def validate(self, data):
        """Cross-field validation - only validate if fields are provided"""
        email_type = data.get('email_type', 'general')
        
        # Only validate OTP requirement if email_type is explicitly set to 'otp'
        if email_type == 'otp':
            if 'otp' in data and not data.get('otp'):
                raise serializers.ValidationError({
                    'otp': 'OTP is required for otp email type'
                })
            elif 'otp' not in data:
                # If email_type is otp but otp field not provided, don't require it
                # The template will just skip OTP section
                pass
        
        # Only validate link requirement if email_type is explicitly set to 'reset_link'
        if email_type == 'reset_link':
            if 'link' in data and not data.get('link'):
                raise serializers.ValidationError({
                    'link': 'Link is required for reset_link email type'
                })
            elif 'link' not in data:
                # If email_type is reset_link but link not provided, don't require it
                # The template will just skip link section
                pass
            
            # Set default link_text only if link is provided
            if data.get('link') and not data.get('link_text'):
                data['link_text'] = 'Reset Password'
        
        # Set defaults for empty optional fields
        if not data.get('subject'):
            data['subject'] = 'Notification'
        
        if not data.get('action'):
            data['action'] = 'notification'
            
        if not data.get('message'):
            data['message'] = 'You have a new notification.'
        
        return data
    
    def to_internal_value(self, data):
        """Handle partial data and set defaults"""
        # Call parent method first
        validated_data = super().to_internal_value(data)
        
        # Ensure we have default values for optional fields
        defaults = {
            'email_type': 'general',
            'subject': 'Notification',
            'action': 'notification', 
            'message': 'You have a new notification.'
        }
        
        for field, default_value in defaults.items():
            if field not in validated_data or validated_data[field] is None:
                validated_data[field] = default_value
        
        return validated_data


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