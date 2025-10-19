from django.contrib import admin
from django.utils.html import format_html
from .models import EmailConfiguration, EmailLog


@admin.register(EmailConfiguration)
class EmailConfigurationAdmin(admin.ModelAdmin):
    fieldsets = (
        ('General Settings', {
            'fields': ('brand_name', 'brand_logo', 'site_url')
        }),
        ('Support Information', {
            'fields': ('support_email', 'support_phone_number')
        }),
        ('Legal', {
            'fields': ('terms_of_service',)
        }),
        ('JWT Authentication', {
            'fields': (
                'jwt_secret_key',
                'jwt_algorithm',
                'jwt_expiration_minutes',
                'jwt_issuer'
            ),
            'classes': ('collapse',),
            'description': 'JWT configuration for microservice authentication'
        }),
        ('Social Media Links', {
            'fields': (
                'facebook_link',
                'instagram_link', 
                'twitter_link',
                'linkedin_link',
                'tiktok_link'
            ),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )
    
    readonly_fields = ('created_at', 'updated_at', 'logo_preview', 'jwt_secret_key')
    
    def get_fieldsets(self, request, obj=None):
        """Override to add logo preview if brand_logo exists"""
        fieldsets = list(super().get_fieldsets(request, obj))
        
        # Add logo preview to the first fieldset if logo exists
        if obj and obj.brand_logo:
            general_fields = list(fieldsets[0][1]['fields'])
            if 'logo_preview' not in general_fields:
                general_fields.append('logo_preview')
            fieldsets[0][1]['fields'] = tuple(general_fields)
        
        return fieldsets
    
    def logo_preview(self, obj):
        """Display a preview of the brand logo"""
        if obj.brand_logo:
            return format_html(
                '<img src="{}" style="max-width: 200px; max-height: 100px; border: 1px solid #ccc; border-radius: 4px;" />',
                obj.brand_logo.url
            )
        return "No logo uploaded"
    logo_preview.short_description = "Logo Preview"
    
    def has_add_permission(self, request):
        """Prevent adding more than one configuration"""
        if EmailConfiguration.objects.exists():
            return False
        return super().has_add_permission(request)
    
    def has_delete_permission(self, request, obj=None):
        """Prevent deletion of the configuration"""
        return False
    
    list_display = ('brand_name', 'support_email', 'has_social_links', 'updated_at')
    list_display_links = ('brand_name',)
    
    def has_social_links(self, obj):
        """Check if any social media links are configured"""
        return obj.has_social_links()
    has_social_links.boolean = True
    has_social_links.short_description = "Social Links"


@admin.register(EmailLog)
class EmailLogAdmin(admin.ModelAdmin):
    list_display = ('email', 'subject', 'email_type', 'status', 'created_at', 'sent_at')
    list_filter = ('email_type', 'status', 'created_at')
    search_fields = ('email', 'subject', 'message')
    readonly_fields = ('created_at', 'sent_at')
    
    fieldsets = (
        ('Email Details', {
            'fields': ('email', 'email_type', 'subject', 'status')
        }),
        ('Content', {
            'fields': ('action', 'message', 'otp', 'link', 'link_text')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'sent_at'),
            'classes': ('collapse',)
        }),
        ('Error Information', {
            'fields': ('error',),
            'classes': ('collapse',)
        })
    )
    
    def has_add_permission(self, request):
        """Prevent manual creation of email logs"""
        return False
    
    def has_change_permission(self, request, obj=None):
        """Make email logs read-only"""
        return False
    
    def has_delete_permission(self, request, obj=None):
        """Allow deletion of email logs"""
        return True