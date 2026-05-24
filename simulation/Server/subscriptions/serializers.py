from rest_framework import serializers
from .models import SubscriptionPlan, UserSubscription, OrganizationSubscription, PaymentHistory


class SubscriptionPlanSerializer(serializers.ModelSerializer):
    """구독 플랜 정보"""
    class Meta:
        model = SubscriptionPlan
        fields = [
            'id', 'name', 'plan_type', 'price', 'price_per_user',
            'billing_cycle', 'currency', 'features', 'is_active'
        ]
        read_only_fields = ['id']


class UserSubscriptionSerializer(serializers.ModelSerializer):
    """개인 구독 정보"""
    plan = SubscriptionPlanSerializer(read_only=True)
    is_active = serializers.ReadOnlyField()
    is_trial = serializers.ReadOnlyField()
    
    class Meta:
        model = UserSubscription
        fields = [
            'id', 'plan', 'status', 'current_period_start', 'current_period_end',
            'canceled_at', 'trial_end', 'is_active', 'is_trial',
            'payment_method', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class OrganizationSubscriptionSerializer(serializers.ModelSerializer):
    """조직 구독 정보 (유저당 비용)"""
    plan = SubscriptionPlanSerializer(read_only=True)
    is_active = serializers.ReadOnlyField()
    monthly_cost = serializers.ReadOnlyField()
    used_seats = serializers.ReadOnlyField()
    available_seats = serializers.ReadOnlyField()
    
    class Meta:
        model = OrganizationSubscription
        fields = [
            'id', 'plan', 'status', 'seat_count', 'used_seats', 'available_seats',
            'monthly_cost', 'current_period_start', 'current_period_end',
            'canceled_at', 'trial_end', 'is_active',
            'payment_method', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class PaymentHistorySerializer(serializers.ModelSerializer):
    """결제 내역"""
    class Meta:
        model = PaymentHistory
        fields = [
            'id', 'amount', 'currency', 'status', 'description',
            'payment_method', 'paid_at', 'refunded_at', 'created_at'
        ]
        read_only_fields = ['id', 'created_at']


# =============================================================================
# Request Serializers
# =============================================================================

class CreateUserSubscriptionSerializer(serializers.Serializer):
    """개인 프로 구독 생성 요청"""
    plan_id = serializers.UUIDField()
    payment_method = serializers.CharField(max_length=50, required=False, default='')


class CreateOrganizationSubscriptionSerializer(serializers.Serializer):
    """조직 구독 생성 요청 (유저당 비용)"""
    plan_id = serializers.UUIDField()
    seat_count = serializers.IntegerField(min_value=1, default=1)
    payment_method = serializers.CharField(max_length=50, required=False, default='')


class UpdateSeatCountSerializer(serializers.Serializer):
    """좌석 수 변경 요청"""
    seat_count = serializers.IntegerField(min_value=1)
