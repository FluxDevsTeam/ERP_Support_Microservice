# apps/email_service/models.py
from django.db import models

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