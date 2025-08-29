from django.contrib import admin
from .models import PartyCategory, Party, PartyRSVP, PartyComment, PartyLike

@admin.register(PartyCategory)
class PartyCategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug', 'is_active', 'sort_order')
    list_filter = ('is_active',)
    search_fields = ('name', 'description')
    prepopulated_fields = {'slug': ('name',)}

@admin.register(Party)
class PartyAdmin(admin.ModelAdmin):
    list_display = ('title', 'host', 'category', 'start_date', 'privacy_level', 'status', 'attendee_count')
    list_filter = ('privacy_level', 'status', 'category', 'is_featured', 'created_at')
    search_fields = ('title', 'description', 'host__email')
    prepopulated_fields = {'slug': ('title',)}
    readonly_fields = ('views_count', 'likes_count', 'shares_count')

@admin.register(PartyRSVP)
class PartyRSVPAdmin(admin.ModelAdmin):
    list_display = ('party', 'user', 'status', 'plus_ones', 'approved_by_host', 'checked_in')
    list_filter = ('status', 'approved_by_host', 'checked_in', 'created_at')
    search_fields = ('party__title', 'user__email')

@admin.register(PartyComment)
class PartyCommentAdmin(admin.ModelAdmin):
    list_display = ('party', 'user', 'content_preview', 'is_pinned', 'created_at')
    list_filter = ('is_pinned', 'is_edited', 'created_at')
    search_fields = ('party__title', 'user__email', 'content')
    
    def content_preview(self, obj):
        return obj.content[:50] + "..." if len(obj.content) > 50 else obj.content
    content_preview.short_description = 'Content Preview'
