"""
User views for authentication and profile management
"""
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from django.shortcuts import get_object_or_404

from .models import UserProfile, Organization, OrganizationMember
from .serializers import UserProfileSerializer, CreateOrganizationSerializer

def get_or_create_user_profile(supabase_user):
    """Helper to sync Supabase user with local UserProfile"""
    profile, created = UserProfile.objects.get_or_create(id=supabase_user.id, defaults={
        'email': supabase_user.email,
        # Can extract more from user_metadata here if needed
        # 'auth_provider': ... 
    })
    
    # Update email if changed (optional)
    if not created and profile.email != supabase_user.email:
        profile.email = supabase_user.email
        profile.save()
        
    return profile

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_profile(request):
    """
    Get current user profile including organizations.
    Auto-creates profile if not exists (Sign up).
    """
    supabase_user = request.user
    profile = get_or_create_user_profile(supabase_user)
    
    serializer = UserProfileSerializer(profile, context={'request': request})
    
    return Response({
        'success': True,
        'data': serializer.data
    })


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def create_organization(request):
    """Create a new organization"""
    serializer = CreateOrganizationSerializer(data=request.data)
    if not serializer.is_valid():
        return Response({
            'success': False,
            'error': serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)
    
    # Ensure user profile exists
    supabase_user = request.user
    profile = get_or_create_user_profile(supabase_user)
    
    # Create Organization
    org_name = serializer.validated_data['name']
    organization = Organization.objects.create(name=org_name)
    
    # Add creator as owner
    OrganizationMember.objects.create(
        organization=organization,
        user=profile,
        role='owner'
    )
    
    # Return updated profile (which includes the new org)
    profile_serializer = UserProfileSerializer(profile, context={'request': request})
    
    return Response({
        'success': True,
        'data': profile_serializer.data
    }, status=status.HTTP_201_CREATED)


@api_view(['POST'])
@permission_classes([AllowAny])
def verify_token(request):
    """
    Verify if a token is valid.
    Frontend can use this to check authentication status.
    """
    from users.authentication import SupabaseAuthentication
    
    auth = SupabaseAuthentication()
    try:
        result = auth.authenticate(request)
        if result:
            user, token = result
            # Sync DB on verify too
            get_or_create_user_profile(user)
            
            return Response({
                'success': True,
                'data': {
                    'valid': True,
                    'user_id': user.id,
                    'email': user.email,
                }
            })
    except Exception as e:
        pass
    
    return Response({
        'success': True,
        'data': {
            'valid': False,
        }
    })
