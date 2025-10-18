from rest_framework import serializers
from .models import Payment
from apps.billing.models import Subscription


class InitiateSerializer(serializers.Serializer):
    subscription_id = serializers.PrimaryKeyRelatedField(queryset=Subscription.objects.all())
    provider = serializers.ChoiceField(choices=['flutterwave', 'paystack'])


class PaymentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Payment
        fields = ['id', 'subscription', 'amount', 'payment_date', 'transaction_id', 'status', 'provider']
        read_only_fields = ['amount', 'payment_date', 'transaction_id', 'status', 'provider']
