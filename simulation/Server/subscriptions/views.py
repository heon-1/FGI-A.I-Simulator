"""
Subscription views for payment and billing management
"""
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from django.shortcuts import get_object_or_404
from django.utils import timezone
from datetime import timedelta

from users.models import UserProfile, Organization, OrganizationMember
from users.views import get_or_create_user_profile

from .models import SubscriptionPlan, UserSubscription, OrganizationSubscription, PaymentHistory
from .serializers import (
    SubscriptionPlanSerializer, 
    UserSubscriptionSerializer, 
    OrganizationSubscriptionSerializer, 
    PaymentHistorySerializer,
    CreateUserSubscriptionSerializer, 
    CreateOrganizationSubscriptionSerializer,
    UpdateSeatCountSerializer
)


# =============================================================================
# Subscription Plans
# =============================================================================

@api_view(['GET'])
@permission_classes([AllowAny])
def list_subscription_plans(request):
    """
    사용 가능한 구독 플랜 목록 조회
    """
    plans = SubscriptionPlan.objects.filter(is_active=True)
    serializer = SubscriptionPlanSerializer(plans, many=True)
    
    return Response({
        'success': True,
        'data': serializer.data
    })


# =============================================================================
# User (Personal) Subscription - Pro Plan
# =============================================================================

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_user_subscription(request):
    """
    현재 사용자의 구독 정보 조회
    """
    supabase_user = request.user
    profile = get_or_create_user_profile(supabase_user)
    
    try:
        subscription = UserSubscription.objects.get(user=profile)
        serializer = UserSubscriptionSerializer(subscription)
        return Response({
            'success': True,
            'data': serializer.data
        })
    except UserSubscription.DoesNotExist:
        return Response({
            'success': True,
            'data': None,
            'message': 'No active subscription'
        })


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def create_user_subscription(request):
    """
    개인 프로 구독 생성
    """
    serializer = CreateUserSubscriptionSerializer(data=request.data)
    if not serializer.is_valid():
        return Response({
            'success': False,
            'error': serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)
    
    supabase_user = request.user
    profile = get_or_create_user_profile(supabase_user)
    
    # 이미 구독이 있는지 확인
    if hasattr(profile, 'subscription') and profile.subscription.is_active:
        return Response({
            'success': False,
            'error': 'Active subscription already exists'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    # 플랜 조회
    plan_id = serializer.validated_data['plan_id']
    try:
        plan = SubscriptionPlan.objects.get(id=plan_id, is_active=True)
    except SubscriptionPlan.DoesNotExist:
        return Response({
            'success': False,
            'error': 'Invalid plan'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    # 개인 플랜인지 확인
    if plan.plan_type not in ['free', 'pro']:
        return Response({
            'success': False,
            'error': 'This plan is for organizations only'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    # 구독 생성
    now = timezone.now()
    period_end = now + timedelta(days=30) if plan.billing_cycle == 'monthly' else now + timedelta(days=365)
    
    subscription = UserSubscription.objects.create(
        user=profile,
        plan=plan,
        status='active',
        current_period_start=now,
        current_period_end=period_end,
        payment_method=serializer.validated_data.get('payment_method', '')
    )
    
    # 결제 내역 생성 (무료 플랜이 아닌 경우)
    if plan.price > 0:
        PaymentHistory.objects.create(
            user_subscription=subscription,
            amount=plan.price,
            currency=plan.currency,
            status='completed',
            description=f'{plan.name} subscription',
            paid_at=now
        )
    
    return Response({
        'success': True,
        'data': UserSubscriptionSerializer(subscription).data
    }, status=status.HTTP_201_CREATED)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def cancel_user_subscription(request):
    """
    개인 구독 취소
    """
    supabase_user = request.user
    profile = get_or_create_user_profile(supabase_user)
    
    try:
        subscription = UserSubscription.objects.get(user=profile)
    except UserSubscription.DoesNotExist:
        return Response({
            'success': False,
            'error': 'No subscription found'
        }, status=status.HTTP_404_NOT_FOUND)
    
    if subscription.status == 'canceled':
        return Response({
            'success': False,
            'error': 'Subscription already canceled'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    subscription.status = 'canceled'
    subscription.canceled_at = timezone.now()
    subscription.save()
    
    return Response({
        'success': True,
        'data': UserSubscriptionSerializer(subscription).data
    })


# =============================================================================
# Organization Subscription - Team Plan (Per User Cost)
# =============================================================================

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_organization_subscription(request, org_id):
    """
    조직의 구독 정보 조회
    """
    supabase_user = request.user
    profile = get_or_create_user_profile(supabase_user)
    
    # 조직 멤버인지 확인
    organization = get_object_or_404(Organization, id=org_id)
    if not OrganizationMember.objects.filter(organization=organization, user=profile).exists():
        return Response({
            'success': False,
            'error': 'Not a member of this organization'
        }, status=status.HTTP_403_FORBIDDEN)
    
    try:
        subscription = OrganizationSubscription.objects.get(organization=organization)
        serializer = OrganizationSubscriptionSerializer(subscription)
        return Response({
            'success': True,
            'data': serializer.data
        })
    except OrganizationSubscription.DoesNotExist:
        return Response({
            'success': True,
            'data': None,
            'message': 'No active subscription'
        })


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def create_organization_subscription(request, org_id):
    """
    조직 구독 생성 (유저당 비용)
    """
    serializer = CreateOrganizationSubscriptionSerializer(data=request.data)
    if not serializer.is_valid():
        return Response({
            'success': False,
            'error': serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)
    
    supabase_user = request.user
    profile = get_or_create_user_profile(supabase_user)
    
    # 조직 및 권한 확인
    organization = get_object_or_404(Organization, id=org_id)
    membership = OrganizationMember.objects.filter(
        organization=organization, 
        user=profile,
        role__in=['owner', 'admin']
    ).first()
    
    if not membership:
        return Response({
            'success': False,
            'error': 'Only owners or admins can manage subscriptions'
        }, status=status.HTTP_403_FORBIDDEN)
    
    # 이미 구독이 있는지 확인
    if hasattr(organization, 'subscription') and organization.subscription.is_active:
        return Response({
            'success': False,
            'error': 'Active subscription already exists'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    # 플랜 조회
    plan_id = serializer.validated_data['plan_id']
    try:
        plan = SubscriptionPlan.objects.get(id=plan_id, is_active=True)
    except SubscriptionPlan.DoesNotExist:
        return Response({
            'success': False,
            'error': 'Invalid plan'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    # 조직용 플랜인지 확인
    if plan.plan_type != 'team':
        return Response({
            'success': False,
            'error': 'This plan is for individual users only'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    seat_count = serializer.validated_data.get('seat_count', 1)
    
    # 구독 생성
    now = timezone.now()
    period_end = now + timedelta(days=30) if plan.billing_cycle == 'monthly' else now + timedelta(days=365)
    
    subscription = OrganizationSubscription.objects.create(
        organization=organization,
        plan=plan,
        status='active',
        seat_count=seat_count,
        current_period_start=now,
        current_period_end=period_end,
        payment_method=serializer.validated_data.get('payment_method', '')
    )
    
    # 결제 내역 생성 (유저당 비용 × 좌석 수)
    total_amount = plan.price_per_user * seat_count
    if total_amount > 0:
        PaymentHistory.objects.create(
            organization_subscription=subscription,
            amount=total_amount,
            currency=plan.currency,
            status='completed',
            description=f'{plan.name} subscription ({seat_count} seats)',
            paid_at=now,
            metadata={'seat_count': seat_count, 'price_per_user': str(plan.price_per_user)}
        )
    
    return Response({
        'success': True,
        'data': OrganizationSubscriptionSerializer(subscription).data
    }, status=status.HTTP_201_CREATED)


@api_view(['PATCH'])
@permission_classes([IsAuthenticated])
def update_organization_seats(request, org_id):
    """
    조직 좌석 수 변경
    """
    serializer = UpdateSeatCountSerializer(data=request.data)
    if not serializer.is_valid():
        return Response({
            'success': False,
            'error': serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)
    
    supabase_user = request.user
    profile = get_or_create_user_profile(supabase_user)
    
    # 조직 및 권한 확인
    organization = get_object_or_404(Organization, id=org_id)
    membership = OrganizationMember.objects.filter(
        organization=organization, 
        user=profile,
        role__in=['owner', 'admin']
    ).first()
    
    if not membership:
        return Response({
            'success': False,
            'error': 'Only owners or admins can manage subscriptions'
        }, status=status.HTTP_403_FORBIDDEN)
    
    try:
        subscription = OrganizationSubscription.objects.get(organization=organization)
    except OrganizationSubscription.DoesNotExist:
        return Response({
            'success': False,
            'error': 'No subscription found'
        }, status=status.HTTP_404_NOT_FOUND)
    
    new_seat_count = serializer.validated_data['seat_count']
    current_members = subscription.used_seats
    
    # 현재 멤버 수보다 적게 설정할 수 없음
    if new_seat_count < current_members:
        return Response({
            'success': False,
            'error': f'Cannot reduce seats below current member count ({current_members})'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    old_seat_count = subscription.seat_count
    subscription.seat_count = new_seat_count
    subscription.save()
    
    # 좌석 추가 결제 내역 (증가한 경우)
    if new_seat_count > old_seat_count:
        added_seats = new_seat_count - old_seat_count
        additional_cost = subscription.plan.price_per_user * added_seats
        
        if additional_cost > 0:
            PaymentHistory.objects.create(
                organization_subscription=subscription,
                amount=additional_cost,
                currency=subscription.plan.currency,
                status='completed',
                description=f'Added {added_seats} seat(s)',
                paid_at=timezone.now(),
                metadata={'added_seats': added_seats, 'price_per_user': str(subscription.plan.price_per_user)}
            )
    
    return Response({
        'success': True,
        'data': OrganizationSubscriptionSerializer(subscription).data
    })


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def cancel_organization_subscription(request, org_id):
    """
    조직 구독 취소
    """
    supabase_user = request.user
    profile = get_or_create_user_profile(supabase_user)
    
    # 조직 및 권한 확인
    organization = get_object_or_404(Organization, id=org_id)
    membership = OrganizationMember.objects.filter(
        organization=organization, 
        user=profile,
        role__in=['owner', 'admin']
    ).first()
    
    if not membership:
        return Response({
            'success': False,
            'error': 'Only owners or admins can manage subscriptions'
        }, status=status.HTTP_403_FORBIDDEN)
    
    try:
        subscription = OrganizationSubscription.objects.get(organization=organization)
    except OrganizationSubscription.DoesNotExist:
        return Response({
            'success': False,
            'error': 'No subscription found'
        }, status=status.HTTP_404_NOT_FOUND)
    
    if subscription.status == 'canceled':
        return Response({
            'success': False,
            'error': 'Subscription already canceled'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    subscription.status = 'canceled'
    subscription.canceled_at = timezone.now()
    subscription.save()
    
    return Response({
        'success': True,
        'data': OrganizationSubscriptionSerializer(subscription).data
    })


# =============================================================================
# Payment History
# =============================================================================

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_payment_history(request):
    """
    결제 내역 조회 (개인 + 본인이 속한 조직)
    """
    supabase_user = request.user
    profile = get_or_create_user_profile(supabase_user)
    
    # 개인 결제 내역
    user_payments = PaymentHistory.objects.filter(
        user_subscription__user=profile
    )
    
    # 소속 조직 결제 내역
    user_orgs = Organization.objects.filter(
        organizationmember__user=profile
    )
    org_payments = PaymentHistory.objects.filter(
        organization_subscription__organization__in=user_orgs
    )
    
    # 합치고 정렬
    all_payments = (user_payments | org_payments).order_by('-created_at')
    
    serializer = PaymentHistorySerializer(all_payments, many=True)
    
    return Response({
        'success': True,
        'data': serializer.data
    })
