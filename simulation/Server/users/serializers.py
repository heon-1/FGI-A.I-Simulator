from rest_framework import serializers
from .models import UserProfile, Organization, OrganizationMember

class OrganizationSerializer(serializers.ModelSerializer):
    role = serializers.SerializerMethodField()
    
    class Meta:
        model = Organization
        fields = ['id', 'name', 'created_at', 'role']
        read_only_fields = ['id', 'created_at', 'role']
    
    def get_role(self, obj):
        # This will be populated in the view if user context is available
        user = self.context.get('request').user
        # Since 'user' here is SupabaseUser (custom object), we need to check DB
        # This part might need adjustment depending on how we pass context
        return self.context.get('role', 'member')

class UserProfileSerializer(serializers.ModelSerializer):
    organizations = serializers.SerializerMethodField()
    
    class Meta:
        model = UserProfile
        fields = ['id', 'email', 'full_name', 'avatar_url', 'auth_provider', 'created_at', 'organizations']
        read_only_fields = ['id', 'email', 'created_at', 'organizations']

    def get_organizations(self, obj):
        # Get memberships for this user
        memberships = OrganizationMember.objects.filter(user=obj)
        data = []
        for membership in memberships:
            # Manually build organization data with role
            org_data = OrganizationSerializer(
                membership.organization, 
                context={'role': membership.role}
            ).data
            data.append(org_data)
        return data

class CreateOrganizationSerializer(serializers.Serializer):
    name = serializers.CharField(max_length=200)

class OrganizationMemberSerializer(serializers.ModelSerializer):
    user_email = serializers.EmailField(source='user.email')
    user_name = serializers.CharField(source='user.full_name')
    
    class Meta:
        model = OrganizationMember
        fields = ['user_email', 'user_name', 'role', 'created_at']
