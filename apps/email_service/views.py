# apps/email_service/views.py
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from drf_yasg.utils import swagger_auto_schema
from django.db.models import Count, Q
from django.utils import timezone

from .tasks import send_generic_email_task, is_celery_healthy
from .permissions import IsSuperuser, AllowAnySendEmail
from .models import EmailLog, EmailConfiguration
from .serializers import (
    EmailLogSerializer, 
    SendEmailSerializer, 
    EmailStatsSerializer,
    EmailTypeStatsSerializer,
    EmailConfigurationSerializer
)


class EmailSendViewSet(viewsets.ViewSet):
    """ViewSet for sending emails, allowing HMAC or superuser authentication."""
    permission_classes = [AllowAnySendEmail]

    @swagger_auto_schema(
        operation_description="Send an email via Celery task",
        request_body=SendEmailSerializer,
        responses={200: 'Email queued successfully'},
        manual_parameters=[
            {
                'name': 'X-HMAC-Signature',
                'in': 'header',
                'type': 'string',
                'required': True,
                'description': 'HMAC signature for microservice authentication'
            },
            {
                'name': 'X-Timestamp',
                'in': 'header',
                'type': 'string',
                'required': True,
                'description': 'ISO timestamp of the request'
            },
            {
                'name': 'X-Service-Name',
                'in': 'header',
                'type': 'string',
                'required': False,
                'description': 'Name of the requesting microservice (default: identity-ms)'
            }
        ]
    )
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
            email_log = EmailLog.objects.create(
                email=validated_data['user_email'],
                email_type=validated_data['email_type'],
                subject=validated_data['subject'],
                action=validated_data['action'],
                message=validated_data['message'],
                otp=validated_data.get('otp'),
                link=validated_data.get('link'),
                link_text=validated_data.get('link_text'),
                status='queued'
            )

            if is_celery_healthy():
                send_generic_email_task.apply_async(
                    kwargs={
                        'user_email': validated_data['user_email'],
                        'email_type': validated_data['email_type'],
                        'subject': validated_data['subject'],
                        'action': validated_data['action'],
                        'message': validated_data['message'],
                        'otp': validated_data.get('otp'),
                        'link': validated_data.get('link'),
                        'link_text': validated_data.get('link_text'),
                        'email_log_id': email_log.id
                    }
                )
            else:
                email_log.status = 'pending'
                email_log.error = 'Celery unavailable, email queued for later processing'
                email_log.save()

            return Response({
                'status': 'queued', 
                'email_type': validated_data['email_type'], 
                'email': validated_data['user_email'],
                'email_log_id': email_log.id
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            return Response({
                'error': 'Failed to queue email',
                'details': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class EmailAdminViewSet(viewsets.ViewSet):
    """ViewSet for administrative email actions, restricted to superusers."""
    permission_classes = [IsSuperuser]

    @swagger_auto_schema(operation_description="List email logs")
    @action(detail=False, methods=['get'], url_path='logs')
    def list_logs(self, request):
        queryset = EmailLog.objects.all()
        
        email_type = request.query_params.get('email_type')
        if email_type:
            queryset = queryset.filter(email_type=email_type)
        
        status_filter = request.query_params.get('status')
        if status_filter:
            queryset = queryset.filter(status=status_filter)
        
        email = request.query_params.get('email')
        if email:
            queryset = queryset.filter(email__icontains=email)
        
        start_date = request.query_params.get('start_date')
        end_date = request.query_params.get('end_date')
        if start_date:
            try:
                start_date = timezone.datetime.fromisoformat(start_date)
                queryset = queryset.filter(created_at__gte=start_date)
            except ValueError:
                pass
        if end_date:
            try:
                end_date = timezone.datetime.fromisoformat(end_date)
                queryset = queryset.filter(created_at__lte=end_date)
            except ValueError:
                pass
        
        limit = request.query_params.get('limit', 50)
        try:
            limit = int(limit)
            if limit > 200:
                limit = 200
            if limit < 1:
                limit = 1
        except ValueError:
            limit = 50
        
        logs = queryset[:limit]
        serializer = EmailLogSerializer(logs, many=True)
        return Response({
            'count': len(serializer.data),
            'results': serializer.data
        }, status=status.HTTP_200_OK)
    
    @swagger_auto_schema(operation_description="Get email statistics")
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
    
    @swagger_auto_schema(operation_description="Get email type statistics")
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


class EmailConfigurationViewSet(viewsets.ViewSet):
    """ViewSet for email configuration, restricted to superusers."""
    permission_classes = [IsSuperuser]
    
    @swagger_auto_schema(
        operation_description="Get current email configuration",
        responses={200: EmailConfigurationSerializer}
    )
    def list(self, request):
        config = EmailConfiguration.get_instance()
        serializer = EmailConfigurationSerializer(config)
        return Response(serializer.data, status=status.HTTP_200_OK)
    
    @swagger_auto_schema(
        operation_description="Update email configuration",
        request_body=EmailConfigurationSerializer,
        responses={200: EmailConfigurationSerializer}
    )
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
    
    @swagger_auto_schema(
        operation_description="Reset HMAC secret key",
        responses={200: 'HMAC secret key reset successfully'}
    )
    @action(detail=False, methods=['post'], url_path='reset-hmac-secret')
    def reset_hmac_secret(self, request):
        import secrets
        config = EmailConfiguration.get_instance()
        config.hmac_secret_key = secrets.token_urlsafe(32)
        config.save()
        
        return Response({
            'message': 'HMAC secret key reset successfully',
            'note': 'All existing HMAC signatures are now invalid'
        }, status=status.HTTP_200_OK)
    
    @swagger_auto_schema(
        operation_description="Test SMTP connection",
        responses={200: 'SMTP connection test successful'}
    )
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