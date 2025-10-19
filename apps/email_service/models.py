# apps/email_service/models.py
from django.db import models
from django.core.exceptions import ValidationError
import os


class EmailLog(models.Model):
    email = models.EmailField()
    email_type = models.CharField(max_length=50)
    subject = models.CharField(max_length=255)
    action = models.CharField(max_length=100)
    message = models.TextField()
    otp = models.CharField(max_length=10, null=True, blank=True)
    link = models.URLField(null=True, blank=True)
    link_text = models.CharField(max_length=100, null=True, blank=True)
    status = models.CharField(max_length=20, default='queued')
    created_at = models.DateTimeField(auto_now_add=True)
    sent_at = models.DateTimeField(null=True, blank=True)
    error = models.TextField(null=True, blank=True)

    def __str__(self):
        return f"{self.email} - {self.subject} ({self.status})"

    class Meta:
        ordering = ['-created_at']


class EmailConfiguration(models.Model):
    """Singleton model for email service configuration"""
    support_email = models.EmailField(blank=True, help_text="Support email address")
    support_phone_number = models.CharField(max_length=20, blank=True, help_text="Support phone number")
    brand_name = models.CharField(max_length=100, default="KidsDesignCompany", help_text="Brand name for emails")
    brand_logo = models.ImageField(upload_to='email_logos/', blank=True, null=True, help_text="Brand logo image")
    terms_of_service = models.URLField(blank=True, help_text="Terms of service URL")
    site_url = models.URLField(blank=True, help_text="Main website URL")
    
    # SMTP Configuration
    email_backend = models.CharField(max_length=100, default='django.core.mail.backends.smtp.EmailBackend', help_text="Email backend to use")
    smtp_host = models.CharField(max_length=255, blank=True, help_text="SMTP server hostname")
    smtp_port = models.PositiveIntegerField(default=587, help_text="SMTP server port")
    smtp_username = models.CharField(max_length=255, blank=True, help_text="SMTP username")
    smtp_password = models.CharField(max_length=255, blank=True, help_text="SMTP password")
    smtp_use_tls = models.BooleanField(default=True, help_text="Use TLS for SMTP connection")
    smtp_use_ssl = models.BooleanField(default=False, help_text="Use SSL for SMTP connection")
    
    # Social media links
    facebook_link = models.URLField(blank=True, help_text="Facebook page URL")
    instagram_link = models.URLField(blank=True, help_text="Instagram profile URL")
    twitter_link = models.URLField(blank=True, help_text="Twitter/X profile URL")
    linkedin_link = models.URLField(blank=True, help_text="LinkedIn profile URL")
    tiktok_link = models.URLField(blank=True, help_text="TikTok profile URL")
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Email Configuration - {self.brand_name}"

    def save(self, *args, **kwargs):
        """Ensure only one configuration exists"""
        if not self.pk and EmailConfiguration.objects.exists():
            raise ValidationError("Only one EmailConfiguration instance is allowed")
        
        super().save(*args, **kwargs)

    def get_brand_logo_url(self):
        """Get the brand logo URL, handling both relative and absolute paths"""
        if self.brand_logo:
            return self.brand_logo.url
        
        from django.conf import settings
        if hasattr(settings, 'BRAND_LOGO_FILENAME'):
            logo_path = os.path.join(
                settings.MEDIA_URL,
                'email_logos',
                settings.BRAND_LOGO_FILENAME
            )
            return logo_path
        
        return 'https://tse4.mm.bing.net/th/id/OIP.rcKRRDLHGEu5lWcn6vbKcAHaHa?rs=1&pid=ImgDetMain'

    def get_social_links(self):
        """Get all social media links as a dictionary"""
        return {
            'facebook': self.facebook_link,
            'instagram': self.instagram_link,
            'twitter': self.twitter_link,
            'linkedin': self.linkedin_link,
            'tiktok': self.tiktok_link,
        }

    def has_social_links(self):
        """Check if any social media links are configured"""
        return any(self.get_social_links().values())

    @classmethod
    def get_instance(cls):
        """Get or create the singleton instance"""
        instance, created = cls.objects.get_or_create(pk=1)
        return instance

    class Meta:
        verbose_name = "Email Configuration"
        verbose_name_plural = "Email Configuration"