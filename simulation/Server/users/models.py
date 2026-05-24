from django.db import models
import uuid

class TimestampedModel(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True

class UserProfile(TimestampedModel):
    AUTH_PROVIDERS = [
        ('email', 'Email'),
        ('google', 'Google'),
    ]

    # Supabase uses UUIDs for user IDs
    id = models.UUIDField(primary_key=True, editable=False)
    email = models.EmailField(unique=True)
    full_name = models.CharField(max_length=100, blank=True)
    avatar_url = models.URLField(max_length=500, blank=True)
    auth_provider = models.CharField(max_length=20, choices=AUTH_PROVIDERS, default='email')
    
    # User can belong to many organizations
    organizations = models.ManyToManyField(
        'Organization', 
        through='OrganizationMember',
        related_name='members'
    )

    def __str__(self):
        return self.email

class Organization(TimestampedModel):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=200)
    
    def __str__(self):
        return self.name

class OrganizationMember(TimestampedModel):
    ROLES = [
        ('owner', 'Owner'),
        ('admin', 'Admin'),
        ('member', 'Member'),
    ]

    organization = models.ForeignKey(Organization, on_delete=models.CASCADE)
    user = models.ForeignKey(UserProfile, on_delete=models.CASCADE)
    role = models.CharField(max_length=20, choices=ROLES, default='member')

    class Meta:
        unique_together = ('organization', 'user')

    def __str__(self):
        return f"{self.user.email} -> {self.organization.name} ({self.role})"
