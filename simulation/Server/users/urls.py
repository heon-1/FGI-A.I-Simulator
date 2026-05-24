"""
User app URL configuration
"""
from django.urls import path
from . import views

urlpatterns = [
    path('profile/', views.get_profile, name='user-profile'),
    path('verify/', views.verify_token, name='verify-token'),
    path('organization/create/', views.create_organization, name='create-organization'),
]
