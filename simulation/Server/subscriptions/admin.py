from django.contrib import admin
from .models import SubscriptionPlan, UserSubscription, OrganizationSubscription, PaymentHistory


@admin.register(SubscriptionPlan)
class SubscriptionPlanAdmin(admin.ModelAdmin):
    list_display = ['name', 'plan_type', 'price', 'price_per_user', 'billing_cycle', 'is_active']
    list_filter = ['plan_type', 'billing_cycle', 'is_active']
    search_fields = ['name']


@admin.register(UserSubscription)
class UserSubscriptionAdmin(admin.ModelAdmin):
    list_display = ['user', 'plan', 'status', 'current_period_start', 'current_period_end']
    list_filter = ['status', 'plan']
    search_fields = ['user__email']
    raw_id_fields = ['user', 'plan']


@admin.register(OrganizationSubscription)
class OrganizationSubscriptionAdmin(admin.ModelAdmin):
    list_display = ['organization', 'plan', 'status', 'seat_count', 'current_period_start', 'current_period_end']
    list_filter = ['status', 'plan']
    search_fields = ['organization__name']
    raw_id_fields = ['organization', 'plan']


@admin.register(PaymentHistory)
class PaymentHistoryAdmin(admin.ModelAdmin):
    list_display = ['id', 'amount', 'currency', 'status', 'paid_at', 'created_at']
    list_filter = ['status', 'currency']
    date_hierarchy = 'created_at'
