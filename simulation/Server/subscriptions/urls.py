"""
Subscription app URL configuration
"""
from django.urls import path
from . import views

urlpatterns = [
    # Subscription Plans
    path('plans/', views.list_subscription_plans, name='subscription-plans'),
    
    # User (Personal) Subscription - Pro Plan
    path('user/', views.get_user_subscription, name='user-subscription'),
    path('user/create/', views.create_user_subscription, name='create-user-subscription'),
    path('user/cancel/', views.cancel_user_subscription, name='cancel-user-subscription'),
    
    # Organization Subscription - Team Plan (Per User Cost)
    path('organization/<uuid:org_id>/', views.get_organization_subscription, name='org-subscription'),
    path('organization/<uuid:org_id>/create/', views.create_organization_subscription, name='create-org-subscription'),
    path('organization/<uuid:org_id>/seats/', views.update_organization_seats, name='update-org-seats'),
    path('organization/<uuid:org_id>/cancel/', views.cancel_organization_subscription, name='cancel-org-subscription'),
    
    # Payment History
    path('payments/', views.get_payment_history, name='payment-history'),
]
