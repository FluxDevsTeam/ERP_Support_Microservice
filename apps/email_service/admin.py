from django.contrib import admin
from django.utils.html import format_html
from django.contrib import messages
from django.shortcuts import redirect
from django.urls import path
from django.http import HttpResponse
from django.core.mail import send_mail
from django.conf import settings
from .models import EmailConfiguration, EmailLog


@admin.register(EmailConfiguration)
class EmailConfigurationAdmin(admin.ModelAdmin):
    change_form_template = 'admin/email_service/emailconfiguration/change_form.html'
    fieldsets = (
        ('General Settings', {
            'fields': ('brand_name', 'brand_logo', 'site_url')
        }),
        ('Support Information', {
            'fields': ('support_email', 'support_phone_number')
        }),
        ('SMTP Configuration', {
            'fields': (
                'email_backend',
                'smtp_host',
                'smtp_port',
                'smtp_username',
                'smtp_password',
                'smtp_use_tls',
                'smtp_use_ssl'
            ),
            'classes': ('collapse',),
            'description': 'SMTP settings for sending emails'
        }),
        ('Legal', {
            'fields': ('terms_of_service',)
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
    
    readonly_fields = ('created_at', 'updated_at', 'logo_preview')
    
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
    
    def change_view(self, request, object_id, form_url='', extra_context=None):
        """Override change view to add test email button"""
        extra_context = extra_context or {}
        extra_context['show_test_email_button'] = True
        return super().change_view(request, object_id, form_url, extra_context)
    
    list_display = ('brand_name', 'support_email', 'smtp_configured', 'has_social_links', 'updated_at')
    list_display_links = ('brand_name',)
    
    def smtp_configured(self, obj):
        """Check if SMTP is properly configured"""
        return bool(obj.smtp_host and obj.smtp_username)
    smtp_configured.boolean = True
    smtp_configured.short_description = "SMTP Configured"
    
    def get_urls(self):
        """Add custom admin URLs"""
        urls = super().get_urls()
        custom_urls = [
            path('test-email/', self.admin_site.admin_view(self.test_email_view), name='test_email'),
        ]
        return custom_urls + urls
    
    def test_email_view(self, request):
        """Custom view to test email configuration"""
        from django.core.mail import get_connection
        from django.core.mail.backends.smtp import EmailBackend
        
        try:
            config = EmailConfiguration.get_instance()
            
            if not config.smtp_host or not config.smtp_username:
                messages.error(request, 'SMTP configuration is incomplete. Please configure SMTP settings first.')
                return redirect('..')
            
            # Test SMTP connection
            connection = get_connection(
                backend=config.email_backend,
                host=config.smtp_host,
                port=config.smtp_port,
                username=config.smtp_username,
                password=config.smtp_password,
                use_tls=config.smtp_use_tls,
                use_ssl=config.smtp_use_ssl,
                timeout=10
            )
            
            connection.open()
            connection.close()
            
            # Send test email
            test_email = config.support_email or request.user.email
            if test_email:
                send_mail(
                    subject='Test Email - Configuration Successful',
                    message='This is a test email to verify your email configuration is working correctly.',
                    from_email=config.smtp_username,
                    recipient_list=[test_email],
                    fail_silently=False,
                )
                
                # Log the test email
                EmailLog.objects.create(
                    email=test_email,
                    email_type='test',
                    subject='Test Email - Configuration Successful',
                    action='test_email',
                    message='Configuration test email sent successfully',
                    status='success'
                )
                
                messages.success(request, f'Test email sent successfully to {test_email}!')
            else:
                messages.warning(request, 'SMTP connection test successful, but no test email address configured.')
                
        except Exception as e:
            messages.error(request, f'Test failed: {str(e)}')
            
        return redirect('..')
    
    def has_social_links(self, obj):
        """Check if any social media links are configured"""
        return obj.has_social_links()
    has_social_links.boolean = True
    has_social_links.short_description = "Social Links"


@admin.register(EmailLog)
class EmailLogAdmin(admin.ModelAdmin):
    list_display = ('email', 'subject', 'email_type', 'status_colored', 'created_at', 'sent_at')
    list_filter = ('email_type', 'status', 'created_at')
    search_fields = ('email', 'subject', 'message')
    readonly_fields = ('created_at', 'sent_at')
    list_per_page = 50
    date_hierarchy = 'created_at'
    ordering = ('-created_at',)
    
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
    
    def status_colored(self, obj):
        """Display status with color coding"""
        colors = {
            'success': 'green',
            'failed': 'red',
            'pending': 'orange',
            'queued': 'blue'
        }
        color = colors.get(obj.status, 'gray')
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            color,
            obj.status.upper()
        )
    status_colored.short_description = "Status"
    status_colored.admin_order_field = 'status'
    
    actions = ['mark_as_success', 'mark_as_failed', 'mark_as_pending']
    
    def mark_as_success(self, request, queryset):
        """Mark selected emails as successful"""
        updated = queryset.update(status='success')
        self.message_user(request, f'{updated} email(s) marked as successful.')
    mark_as_success.short_description = "Mark selected emails as successful"
    
    def mark_as_failed(self, request, queryset):
        """Mark selected emails as failed"""
        updated = queryset.update(status='failed')
        self.message_user(request, f'{updated} email(s) marked as failed.')
    mark_as_failed.short_description = "Mark selected emails as failed"
    
    def mark_as_pending(self, request, queryset):
        """Mark selected emails as pending"""
        updated = queryset.update(status='pending')
        self.message_user(request, f'{updated} email(s) marked as pending.')
    mark_as_pending.short_description = "Mark selected emails as pending"