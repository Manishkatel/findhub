"""
Serializers for user authentication and account management
"""

from rest_framework import serializers
from rest_framework.validators import UniqueValidator
from django.contrib.auth import authenticate
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from .models import User, UserProfile, UserSettings, UserConnection


class UserRegistrationSerializer(serializers.ModelSerializer):
    """
    Serializer for user registration
    """
    email = serializers.EmailField(
        required=True,
        validators=[UniqueValidator(queryset=User.objects.all())]
    )
    password = serializers.CharField(
        write_only=True,
        required=True,
        validators=[validate_password]
    )
    password_confirm = serializers.CharField(write_only=True, required=True)
    first_name = serializers.CharField(required=True, max_length=30)
    last_name = serializers.CharField(required=True, max_length=30)
    user_type = serializers.ChoiceField(choices=User.USER_TYPES, default='creator')
    
    class Meta:
        model = User
        fields = (
            'email', 'password', 'password_confirm', 'first_name', 'last_name',
            'username', 'user_type', 'phone_number', 'timezone', 'language'
        )
        extra_kwargs = {
            'username': {'required': True},
        }
    
    def validate(self, attrs):
        """Validate password confirmation"""
        if attrs['password'] != attrs['password_confirm']:
            raise serializers.ValidationError({"password": "Password fields didn't match."})
        return attrs
    
    def validate_email(self, value):
        """Additional email validation"""
        if User.objects.filter(email__iexact=value).exists():
            raise serializers.ValidationError("A user with this email already exists.")
        return value.lower()
    
    def validate_username(self, value):
        """Validate username uniqueness"""
        if User.objects.filter(username__iexact=value).exists():
            raise serializers.ValidationError("A user with this username already exists.")
        return value
    
    def create(self, validated_data):
        """Create new user"""
        validated_data.pop('password_confirm')
        password = validated_data.pop('password')
        
        user = User.objects.create_user(
            password=password,
            **validated_data
        )
        
        # Create user profile and settings
        UserProfile.objects.create(user=user)
        UserSettings.objects.create(user=user)
        
        return user


class UserLoginSerializer(serializers.Serializer):
    """
    Serializer for user login
    """
    email = serializers.EmailField(required=True)
    password = serializers.CharField(required=True, write_only=True)
    remember_me = serializers.BooleanField(default=False)
    
    def validate(self, attrs):
        """Validate login credentials"""
        email = attrs.get('email', '').lower()
        password = attrs.get('password', '')
        
        if email and password:
            user = authenticate(
                request=self.context.get('request'),
                username=email,
                password=password
            )
            
            if not user:
                raise serializers.ValidationError(
                    'Unable to log in with provided credentials.'
                )
            
            if not user.is_active:
                raise serializers.ValidationError(
                    'User account is disabled.'
                )
            
            # Update last active
            user.update_last_active()
            
            attrs['user'] = user
            return attrs
        else:
            raise serializers.ValidationError(
                'Must include "email" and "password".'
            )


class UserProfileSerializer(serializers.ModelSerializer):
    """
    Serializer for user profile
    """
    avatar_url = serializers.SerializerMethodField()
    cover_url = serializers.SerializerMethodField()
    full_name = serializers.CharField(source='user.full_name', read_only=True)
    
    class Meta:
        model = UserProfile
        fields = (
            'bio', 'avatar', 'cover_image', 'avatar_url', 'cover_url',
            'location', 'latitude', 'longitude', 'website', 'instagram', 
            'twitter', 'linkedin', 'privacy_level', 'email_notifications', 
            'push_notifications', 'marketing_emails', 'total_parties_created', 
            'total_parties_attended', 'total_invitations_sent', 'reputation_score', 
            'full_name'
        )
        read_only_fields = (
            'total_parties_created', 'total_parties_attended',
            'total_invitations_sent', 'reputation_score'
        )
    
    def get_avatar_url(self, obj):
        """Get avatar URL"""
        return obj.get_avatar_url()
    
    def get_cover_url(self, obj):
        """Get cover image URL"""
        return obj.get_cover_url()


class UserSerializer(serializers.ModelSerializer):
    """
    Main user serializer
    """
    profile = UserProfileSerializer(read_only=True)
    full_name = serializers.CharField(read_only=True)
    is_premium_active = serializers.BooleanField(read_only=True, source='is_premium_active')
    
    class Meta:
        model = User
        fields = (
            'id', 'username', 'email', 'first_name', 'last_name', 'full_name',
            'user_type', 'is_verified', 'is_premium', 'is_premium_active',
            'premium_expires_at', 'phone_number', 'timezone', 'language',
            'date_joined', 'last_login', 'last_active', 'profile'
        )
        read_only_fields = (
            'id', 'is_verified', 'is_premium', 'premium_expires_at',
            'date_joined', 'last_login', 'last_active'
        )


class UserUpdateSerializer(serializers.ModelSerializer):
    """
    Serializer for updating user information
    """
    profile = UserProfileSerializer(required=False)
    
    class Meta:
        model = User
        fields = (
            'first_name', 'last_name', 'username', 'phone_number',
            'timezone', 'language', 'profile'
        )
    
    def update(self, instance, validated_data):
        """Update user and profile"""
        profile_data = validated_data.pop('profile', None)
        
        # Update user fields
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        
        # Update profile fields
        if profile_data and hasattr(instance, 'profile'):
            profile = instance.profile
            for attr, value in profile_data.items():
                setattr(profile, attr, value)
            profile.save()
        
        return instance


class UserSettingsSerializer(serializers.ModelSerializer):
    """
    Serializer for user settings
    """
    class Meta:
        model = UserSettings
        fields = '__all__'
        read_only_fields = ('user', 'created_at', 'updated_at')


class UserConnectionSerializer(serializers.ModelSerializer):
    """
    Serializer for user connections/friendships
    """
    from_user = UserSerializer(read_only=True)
    to_user = UserSerializer(read_only=True)
    
    class Meta:
        model = UserConnection
        fields = (
            'id', 'from_user', 'to_user', 'connection_type', 'status',
            'created_at', 'updated_at'
        )
        read_only_fields = ('id', 'created_at', 'updated_at')


class PasswordChangeSerializer(serializers.Serializer):
    """
    Serializer for password change
    """
    old_password = serializers.CharField(required=True)
    new_password = serializers.CharField(required=True, validators=[validate_password])
    new_password_confirm = serializers.CharField(required=True)
    
    def validate_old_password(self, value):
        """Validate old password"""
        user = self.context['request'].user
        if not user.check_password(value):
            raise serializers.ValidationError("Old password is incorrect.")
        return value
    
    def validate(self, attrs):
        """Validate new password confirmation"""
        if attrs['new_password'] != attrs['new_password_confirm']:
            raise serializers.ValidationError({"new_password": "New password fields didn't match."})
        return attrs
    
    def save(self):
        """Change password"""
        user = self.context['request'].user
        user.set_password(self.validated_data['new_password'])
        user.save()
        return user


class PasswordResetRequestSerializer(serializers.Serializer):
    """
    Serializer for password reset request
    """
    email = serializers.EmailField(required=True)
    
    def validate_email(self, value):
        """Validate email exists"""
        if not User.objects.filter(email__iexact=value).exists():
            raise serializers.ValidationError("No user found with this email address.")
        return value.lower()


class PasswordResetConfirmSerializer(serializers.Serializer):
    """
    Serializer for password reset confirmation
    """
    token = serializers.CharField(required=True)
    new_password = serializers.CharField(required=True, validators=[validate_password])
    new_password_confirm = serializers.CharField(required=True)
    
    def validate(self, attrs):
        """Validate new password confirmation"""
        if attrs['new_password'] != attrs['new_password_confirm']:
            raise serializers.ValidationError({"new_password": "Password fields didn't match."})
        return attrs