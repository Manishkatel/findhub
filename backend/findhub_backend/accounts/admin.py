from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User, UserProfile

@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = ('email', 'username', 'first_name', 'last_name', 'user_type', 'is_verified', 'is_premium', 'date_joined')
    list_filter = ('user_type', 'is_verified', 'is_premium', 'date_joined')
    search_fields = ('email', 'username', 'first_name', 'last_name')
    ordering = ('-date_joined',)
    
    fieldsets = BaseUserAdmin.fieldsets + (
        ('Additional Info', {
            'fields': ('user_type', 'is_verified', 'is_premium', 'premium_expires_at', 'phone_number', 'timezone', 'language')
        }),
    )

@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'location', 'privacy_level', 'total_parties_created', 'total_parties_attended')
    list_filter = ('privacy_level', 'created_at')
    search_fields = ('user__email', 'user__username', 'location')
