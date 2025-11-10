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
    
    user_email = serializers.EmailField(required=True)
    email_type = serializers.CharField(max_length=50, required=False, allow_blank=True, allow_null=True)
    subject = serializers.CharField(max_length=255, required=False, allow_blank=True, allow_null=True)
    action = serializers.CharField(max_length=100, required=False, allow_blank=True, allow_null=True)
    message = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    otp = serializers.CharField(max_length=10, required=False, allow_blank=True, allow_null=True)
    link = serializers.URLField(required=False, allow_blank=True, allow_null=True)
    link_text = serializers.CharField(max_length=100, required=False, allow_blank=True, allow_null=True)
    
    def validate_user_email(self, value):
        """Validate email format"""
        if not value or '@' not in value:
            raise serializers.ValidationError("Invalid email format")
        return value.lower().strip()
    
    def validate(self, data):
        """Minimal validation - just ensure data consistency"""
        # Set default link_text if link is provided but link_text is empty
        if data.get('link') and not data.get('link_text'):
            data['link_text'] = 'Click Here'
        
        return data
    
    def to_internal_value(self, data):
        """Handle partial data - no forced defaults"""
        # Call parent method first
        validated_data = super().to_internal_value(data)
        
        # Only clean up empty strings to None for consistency
        for field in ['email_type', 'subject', 'action', 'message', 'otp', 'link', 'link_text']:
            if field in validated_data and validated_data[field] == '':
                validated_data[field] = None
        
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
            'brand_logo', 'terms_of_service', 'site_url',
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