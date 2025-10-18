# apps/email_service/views.py
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from drf_yasg.utils import swagger_auto_schema
from .tasks import send_generic_email_task, is_celery_healthy
from .utils import HMACAuthentication
from .models import EmailLog
from rest_framework import serializers


class EmailLogSerializer(serializers.ModelSerializer):
    class Meta:
        model = EmailLog
        fields = '__all__'


class EmailViewSet(viewsets.ViewSet):
    authentication_classes = [HMACAuthentication]
    permission_classes = []

    @swagger_auto_schema(
        operation_description="Send an email via Celery task",
        request_body={
            'type': 'object',
            'properties': {
                'user_email': {'type': 'string', 'format': 'email'},
                'email_type': {'type': 'string', 'enum': ['otp', 'confirmation', 'reset_link']},
                'subject': {'type': 'string'},
                'action': {'type': 'string'},
                'message': {'type': 'string'},
                'otp': {'type': 'string', 'nullable': True},
                'link': {'type': 'string', 'format': 'uri', 'nullable': True},
                'link_text': {'type': 'string', 'nullable': True},
            },
            'required': ['user_email', 'email_type', 'subject', 'action', 'message']
        },
        responses={200: 'Email queued successfully'}
    )
    @action(detail=False, methods=['post'], url_path='send-email')
    def send_email(self, request):
        data = request.data
        required_fields = ['user_email', 'email_type', 'subject', 'action', 'message']

        if not all(field in data for field in required_fields):
            return Response({'error': 'Missing required fields'}, status=status.HTTP_400_BAD_REQUEST)

        if data['email_type'] not in ['otp', 'confirmation', 'reset_link']:
            return Response({'error': 'Invalid email_type'}, status=status.HTTP_400_BAD_REQUEST)

        # Log the email request
        email_log = EmailLog.objects.create(
            email=data['user_email'],
            email_type=data['email_type'],
            subject=data['subject'],
            action=data['action'],
            message=data['message'],
            otp=data.get('otp'),
            link=data.get('link'),
            link_text=data.get('link_text'),
            status='queued'
        )

        # Queue email task or mark as pending if Celery is down
        if is_celery_healthy():
            send_generic_email_task.apply_async(
                kwargs={
                    'user_email': data['user_email'],
                    'email_type': data['email_type'],
                    'subject': data['subject'],
                    'action': data['action'],
                    'message': data['message'],
                    'otp': data.get('otp'),
                    'link': data.get('link'),
                    'link_text': data.get('link_text'),
                    'email_log_id': email_log.id
                }
            )
        else:
            email_log.status = 'pending'
            email_log.error = 'Celery unavailable, email queued for later processing'
            email_log.save()

        return Response(
            {'status': 'queued', 'email_type': data['email_type'], 'email': data['user_email']},
            status=status.HTTP_200_OK
        )

    @swagger_auto_schema(operation_description="List email logs")
    @action(detail=False, methods=['get'], url_path='logs')
    def list_logs(self, request):
        logs = EmailLog.objects.all()
        serializer = EmailLogSerializer(logs, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)