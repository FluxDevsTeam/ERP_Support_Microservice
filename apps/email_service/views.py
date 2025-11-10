from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from drf_yasg.utils import swagger_auto_schema
from django.db.models import Count, Q
from django.utils import timezone

from apps.email_service.pagination import CustomPagination

from .tasks import send_generic_email_task, is_celery_healthy, send_direct_email
from .permissions import IsSuperuser, AllowAnySendEmail
from .models import EmailLog, EmailConfiguration
from .serializers import (
    EmailLogSerializer,
    SendEmailSerializer,
    EmailStatsSerializer,
    EmailTypeStatsSerializer,
    EmailConfigurationSerializer,
)
from .utils import swagger_helper, send_generic_email
from django.utils import timezone 


class EmailSendViewSet(viewsets.ViewSet):
    """ViewSet for sending emails, allowing microservice JWT or superuser JWT authentication."""
    permission_classes = [AllowAnySendEmail]

    @swagger_helper("Email Send", "SendEmail")
    @action(detail=False, methods=['post'], url_path='send-email')
    def send_email(self, request):
        serializer = SendEmailSerializer(data=request.data)
        
        if not serializer.is_valid():
            return Response({
                'error': 'Validation failed',
                'details': serializer.errors
            }, status=status.HTTP_400_BAD_REQUEST)
        
        validated_data = serializer.validated_data

        try:
            # Log which authentication method was used
            auth_method = "microservice" if hasattr(request, 'microservice_name') else "superuser"
            microservice_name = getattr(request, 'microservice_name', 'N/A')
            
            email_log = EmailLog.objects.create(
                email=validated_data['user_email'],
                email_type=validated_data.get('email_type'),
                subject=validated_data.get('subject'),
                action=validated_data.get('action'),
                message=validated_data.get('message'),
                otp=validated_data.get('otp'),
                link=validated_data.get('link'),
                link_text=validated_data.get('link_text'),
                status='queued'
            )

            if is_celery_healthy():
                # Use Celery for asynchronous processing
                task_kwargs = {
                    'user_email': validated_data['user_email'],
                    'email_type': validated_data.get('email_type'),
                    'subject': validated_data.get('subject'),
                    'action': validated_data.get('action'),
                    'message': validated_data.get('message'),
                    'otp': validated_data.get('otp'),
                    'link': validated_data.get('link'),
                    'link_text': validated_data.get('link_text'),
                    'email_log_id': email_log.id
                }
                
                # Add any additional fields from the request
                for key, value in request.data.items():
                    if key not in task_kwargs and key != 'user_email':
                        task_kwargs[key] = value
                
                send_generic_email_task.apply_async(kwargs=task_kwargs)
                
                return Response({
                    'status': 'queued', 
                    'email_type': validated_data.get('email_type'), 
                    'email': validated_data['user_email'],
                    'email_log_id': email_log.id,
                    'auth_method': auth_method,
                    'processing_method': 'celery'
                }, status=status.HTTP_200_OK)
            else:
                # Send email directly when Celery is unavailable
                # Prepare additional fields from the request
                additional_fields = {k: v for k, v in request.data.items() 
                                   if k not in ['user_email', 'email_type', 'subject', 'action', 'message', 'otp', 'link', 'link_text']}
                
                # Call the direct email sending function
                result = send_direct_email(
                    user_email=validated_data['user_email'],
                    email_type=validated_data.get('email_type'),
                    subject=validated_data.get('subject'),
                    action=validated_data.get('action'),
                    message=validated_data.get('message'),
                    otp=validated_data.get('otp'),
                    link=validated_data.get('link'),
                    link_text=validated_data.get('link_text'),
                    email_log_id=email_log.id,
                    **additional_fields
                )
                
                # Return appropriate response based on result
                if result['status'] == 'success':
                    return Response({
                        'status': 'sent', 
                        'email_type': validated_data.get('email_type'), 
                        'email': validated_data['user_email'],
                        'email_log_id': email_log.id,
                        'auth_method': auth_method,
                        'processing_method': result['processing_method']
                    }, status=status.HTTP_200_OK)
                else:
                    return Response({
                        'status': 'failed', 
                        'email_type': validated_data.get('email_type'), 
                        'email': validated_data['user_email'],
                        'email_log_id': email_log.id,
                        'auth_method': auth_method,
                        'processing_method': result['processing_method'],
                        'error': result.get('error', 'Direct email sending failed')
                    }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            
        except Exception as e:
            return Response({
                'error': 'Failed to queue email',
                'details': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class EmailAdminViewSet(viewsets.ModelViewSet):
    """ViewSet for administrative email actions, restricted to superusers."""
    permission_classes = [IsSuperuser]
    queryset = EmailLog.objects.all()
    pagination_class = CustomPagination

    def get_serializer_class(self):
        if self.action == 'list':
            return EmailLogSerializer
        if self.action == 'email_stats':
            return EmailStatsSerializer
        if self.action == 'email_type_stats':
            return EmailTypeStatsSerializer
        return EmailLogSerializer

    @swagger_helper("Email Admin", "EmailLog")
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

    @swagger_helper("Email Admin", "EmailStats")
    @action(detail=False, methods=['get'], url_path='stats')
    def email_stats(self, request):
        total_emails = EmailLog.objects.count()
        successful_emails = EmailLog.objects.filter(status='success').count()
        failed_emails = EmailLog.objects.filter(status='failed').count()
        pending_emails = EmailLog.objects.filter(status='pending').count()
        
        success_rate = (successful_emails / total_emails * 100) if total_emails > 0 else 0
        
        stats_data = {
            'total_emails': total_emails,
            'successful_emails': successful_emails,
            'failed_emails': failed_emails,
            'pending_emails': pending_emails,
            'success_rate': round(success_rate, 2)
        }
        
        serializer = EmailStatsSerializer(stats_data)
        return Response(serializer.data, status=status.HTTP_200_OK)
    
    @swagger_helper("Email Admin", "EmailTypeStats")
    @action(detail=False, methods=['get'], url_path='type-stats')
    def email_type_stats(self, request):
        type_stats = EmailLog.objects.values('email_type').annotate(
            count=Count('id'),
            success_count=Count('id', filter=Q(status='success'))
        ).order_by('-count')
        
        results = []
        for stat in type_stats:
            success_rate = (stat['success_count'] / stat['count'] * 100) if stat['count'] > 0 else 0
            results.append({
                'email_type': stat['email_type'],
                'count': stat['count'],
                'success_rate': round(success_rate, 2)
            })
        
        serializer = EmailTypeStatsSerializer(results, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @swagger_helper("Email Admin", "EmailRetry")
    @action(detail=True, methods=['post'], url_path='retry')
    def retry_email(self, request, pk=None):
        """Retry sending a failed email log (superadmin only)."""
        try:
            email_log = EmailLog.objects.get(pk=pk)
        except EmailLog.DoesNotExist:
            return Response({
                'error': 'Email log not found'
            }, status=status.HTTP_404_NOT_FOUND)

        if email_log.status not in ['failed', 'pending', 'queued']:
            return Response({
                'error': 'Only failed or pending emails can be retried'
            }, status=status.HTTP_400_BAD_REQUEST)

        payload = {
            'user_email': email_log.email,
            'email_type': email_log.email_type,
            'subject': email_log.subject,
            'action': email_log.action,
            'message': email_log.message,
            'otp': email_log.otp,
            'link': email_log.link,
            'link_text': email_log.link_text,
            'email_log_id': email_log.id,
        }

        try:
            if is_celery_healthy():
                # Queue retry via Celery
                send_generic_email_task.apply_async(kwargs=payload)
                email_log.status = 'queued'
                email_log.save(update_fields=['status'])
                return Response({
                    'status': 'queued',
                    'email_log_id': email_log.id,
                    'email': email_log.email,
                    'message': 'Retry queued successfully',
                    'processing_method': 'celery'
                }, status=status.HTTP_200_OK)
            else:
                # Fallback: direct send
                result = send_direct_email(**payload)
                if result.get('status') == 'success':
                    email_log.status = 'success'
                    email_log.save(update_fields=['status'])
                    return Response({
                        'status': 'sent',
                        'email_log_id': email_log.id,
                        'email': email_log.email,
                        'message': 'Retry sent successfully',
                        'processing_method': result.get('processing_method', 'direct')
                    }, status=status.HTTP_200_OK)
                else:
                    email_log.status = 'failed'
                    email_log.save(update_fields=['status'])
                    return Response({
                        'status': 'failed',
                        'email_log_id': email_log.id,
                        'email': email_log.email,
                        'error': result.get('error', 'Retry failed')
                    }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        except Exception as e:
            email_log.status = 'failed'
            email_log.save(update_fields=['status'])
            return Response({
                'status': 'failed',
                'email_log_id': email_log.id,
                'email': email_log.email,
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class EmailConfigurationViewSet(viewsets.ViewSet):
    """ViewSet for email configuration, restricted to superusers."""
    permission_classes = [IsSuperuser]
    
    @swagger_helper("Email Configuration", "EmailConfiguration")
    def list(self, request):
        config = EmailConfiguration.get_instance()
        serializer = EmailConfigurationSerializer(config)
        return Response(serializer.data, status=status.HTTP_200_OK)
    
    @swagger_helper("Email Configuration", "EmailConfiguration")
    def update(self, request, pk=None):
        config = EmailConfiguration.get_instance()
        serializer = EmailConfigurationSerializer(config, data=request.data, partial=True)
        
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        
        return Response({
            'error': 'Validation failed',
            'details': serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)
    

    @swagger_helper("Email Configuration", "JWTSecret")
    @action(detail=False, methods=['post'], url_path='reset-jwt-secret')
    def reset_jwt_secret(self, request):
        from django.core.management import call_command
        
        try:
            call_command('reset_jwt_secret')
            return Response({
                'message': 'JWT secret key reset successfully'
            }, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({
                'error': 'Failed to reset JWT secret',
                'details': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @swagger_helper("Email Configuration", "SMTPTest")
    @action(detail=False, methods=['post'], url_path='test-smtp')
    def test_smtp_connection(self, request):
        from django.core.mail import get_connection
        from django.core.mail.backends.smtp import EmailBackend
        
        config = EmailConfiguration.get_instance()
        
        try:
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
            
            return Response({
                'message': 'SMTP connection test successful',
                'host': config.smtp_host,
                'port': config.smtp_port
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            return Response({
                'error': 'SMTP connection test failed',
                'details': str(e),
                'host': config.smtp_host,
                'port': config.smtp_port
            }, status=status.HTTP_400_BAD_REQUEST)