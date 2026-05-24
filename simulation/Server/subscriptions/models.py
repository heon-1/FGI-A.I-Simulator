from django.db import models
from django.utils import timezone
from decimal import Decimal
import uuid


class TimestampedModel(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class SubscriptionPlan(TimestampedModel):
    """
    구독 플랜 정의
    - FREE: 무료 플랜
    - PRO: 개인 프로 플랜 (월정액)
    - TEAM: 조직용 플랜 (유저당 비용)
    """
    PLAN_TYPES = [
        ('free', 'Free'),
        ('pro', 'Pro'),
        ('team', 'Team'),
    ]
    
    BILLING_CYCLES = [
        ('monthly', 'Monthly'),
        ('yearly', 'Yearly'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=100)
    plan_type = models.CharField(max_length=20, choices=PLAN_TYPES)
    
    # 가격 정보
    price = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))  # 개인 프로 월정액
    price_per_user = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))  # 조직용 유저당 비용
    billing_cycle = models.CharField(max_length=20, choices=BILLING_CYCLES, default='monthly')
    currency = models.CharField(max_length=3, default='KRW')
    
    # 플랜 기능/제한
    features = models.JSONField(default=dict, blank=True)  # {"max_simulations": 100, "max_personas": 10, ...}
    is_active = models.BooleanField(default=True)
    
    class Meta:
        ordering = ['price']
    
    def __str__(self):
        return f"{self.name} ({self.plan_type})"


class UserSubscription(TimestampedModel):
    """
    개인 사용자 구독 (Pro 플랜)
    """
    STATUS_CHOICES = [
        ('active', 'Active'),
        ('canceled', 'Canceled'),
        ('expired', 'Expired'),
        ('past_due', 'Past Due'),
        ('trialing', 'Trialing'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.OneToOneField(
        'users.UserProfile', 
        on_delete=models.CASCADE, 
        related_name='subscription'
    )
    plan = models.ForeignKey(
        SubscriptionPlan, 
        on_delete=models.PROTECT, 
        related_name='user_subscriptions'
    )
    
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active')
    
    # 결제 기간
    current_period_start = models.DateTimeField(default=timezone.now)
    current_period_end = models.DateTimeField(null=True, blank=True)
    canceled_at = models.DateTimeField(null=True, blank=True)
    
    # 외부 결제 연동 (Stripe, Toss 등)
    external_subscription_id = models.CharField(max_length=255, blank=True)
    external_customer_id = models.CharField(max_length=255, blank=True)
    payment_method = models.CharField(max_length=50, blank=True)  # 'card', 'bank_transfer' 등
    
    # 트라이얼
    trial_end = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.user.email} - {self.plan.name}"
    
    @property
    def is_active(self):
        return self.status in ['active', 'trialing']
    
    @property
    def is_trial(self):
        if self.trial_end:
            return timezone.now() < self.trial_end
        return False


class OrganizationSubscription(TimestampedModel):
    """
    조직 구독 (Team 플랜 - 유저당 비용)
    """
    STATUS_CHOICES = [
        ('active', 'Active'),
        ('canceled', 'Canceled'),
        ('expired', 'Expired'),
        ('past_due', 'Past Due'),
        ('trialing', 'Trialing'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    organization = models.OneToOneField(
        'users.Organization', 
        on_delete=models.CASCADE, 
        related_name='subscription'
    )
    plan = models.ForeignKey(
        SubscriptionPlan, 
        on_delete=models.PROTECT, 
        related_name='organization_subscriptions'
    )
    
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active')
    
    # 좌석 수 (유저당 과금)
    seat_count = models.PositiveIntegerField(default=1)  # 구매한 좌석 수
    
    # 결제 기간
    current_period_start = models.DateTimeField(default=timezone.now)
    current_period_end = models.DateTimeField(null=True, blank=True)
    canceled_at = models.DateTimeField(null=True, blank=True)
    
    # 외부 결제 연동
    external_subscription_id = models.CharField(max_length=255, blank=True)
    external_customer_id = models.CharField(max_length=255, blank=True)
    payment_method = models.CharField(max_length=50, blank=True)
    
    # 트라이얼
    trial_end = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.organization.name} - {self.plan.name} ({self.seat_count} seats)"
    
    @property
    def is_active(self):
        return self.status in ['active', 'trialing']
    
    @property
    def monthly_cost(self):
        """월간 총 비용 계산 (유저당 비용 × 좌석 수)"""
        return self.plan.price_per_user * self.seat_count
    
    @property
    def used_seats(self):
        """사용 중인 좌석 수"""
        return self.organization.organizationmember_set.count()
    
    @property
    def available_seats(self):
        """남은 좌석 수"""
        return max(0, self.seat_count - self.used_seats)


class PaymentHistory(TimestampedModel):
    """
    결제 내역
    """
    PAYMENT_STATUS = [
        ('pending', 'Pending'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
        ('refunded', 'Refunded'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    # 결제 주체 (개인 또는 조직)
    user_subscription = models.ForeignKey(
        UserSubscription, 
        on_delete=models.SET_NULL, 
        null=True, blank=True, 
        related_name='payments'
    )
    organization_subscription = models.ForeignKey(
        OrganizationSubscription, 
        on_delete=models.SET_NULL, 
        null=True, blank=True, 
        related_name='payments'
    )
    
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    currency = models.CharField(max_length=3, default='KRW')
    status = models.CharField(max_length=20, choices=PAYMENT_STATUS, default='pending')
    
    # 결제 상세
    description = models.CharField(max_length=500, blank=True)
    external_payment_id = models.CharField(max_length=255, blank=True)  # 외부 결제 ID
    payment_method = models.CharField(max_length=50, blank=True)
    
    paid_at = models.DateTimeField(null=True, blank=True)
    refunded_at = models.DateTimeField(null=True, blank=True)
    
    # 메타데이터 (추가 정보)
    metadata = models.JSONField(default=dict, blank=True)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name_plural = 'Payment histories'
    
    def __str__(self):
        return f"Payment {self.id} - {self.amount} {self.currency}"
