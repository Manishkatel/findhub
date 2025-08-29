from django.db import models
from django.contrib.auth import get_user_model
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils import timezone
from taggit.managers import TaggableManager
import uuid
from decimal import Decimal
from apps.core.models import BaseModel

User = get_user_model()

class PartyCategory(BaseModel):
    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    icon = models.CharField(max_length=50, blank=True)
    color = models.CharField(max_length=7, default="#007bff")
    is_active = models.BooleanField(default=True)
    sort_order = models.PositiveIntegerField(default=0)
    
    class Meta:
        db_table = 'party_categories'
        verbose_name = 'Party Category'
        verbose_name_plural = 'Party Categories'
        ordering = ['sort_order', 'name']
    
    def __str__(self):
        return self.name


class Party(BaseModel):
    PRIVACY_CHOICES = [
        ('public', 'Public'),
        ('private', 'Private'),
        ('friends_only', 'Friends Only'),
        ('invite_only', 'Invite Only'),
    ]
    
    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('published', 'Published'),
        ('cancelled', 'Cancelled'),
        ('completed', 'Completed'),
    ]
    
    RSVP_CHOICES = [
        ('open', 'Open RSVP'),
        ('approval', 'Requires Approval'),
        ('invite_only', 'Invite Only'),
        ('closed', 'RSVP Closed'),
    ]
    
    # Basic Information
    title = models.CharField(max_length=200)
    slug = models.SlugField(max_length=220, unique=True)
    description = models.TextField()
    short_description = models.CharField(max_length=300, blank=True)
    
    # Relationships
    host = models.ForeignKey(User, on_delete=models.CASCADE, related_name='hosted_parties')
    co_hosts = models.ManyToManyField(User, blank=True, related_name='co_hosted_parties')
    category = models.ForeignKey(PartyCategory, on_delete=models.SET_NULL, null=True, blank=True)
    
    # DateTime Information
    start_date = models.DateTimeField()
    end_date = models.DateTimeField()
    timezone = models.CharField(max_length=50, default='UTC')
    rsvp_deadline = models.DateTimeField(null=True, blank=True)
    
    # Location Information
    location_name = models.CharField(max_length=200, blank=True)
    address = models.TextField(blank=True)
    latitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    longitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    is_virtual = models.BooleanField(default=False)
    virtual_link = models.URLField(blank=True)
    virtual_platform = models.CharField(max_length=50, blank=True)
    
    # Party Settings
    privacy_level = models.CharField(max_length=15, choices=PRIVACY_CHOICES, default='private')
    status = models.CharField(max_length=15, choices=STATUS_CHOICES, default='draft')
    rsvp_type = models.CharField(max_length=15, choices=RSVP_CHOICES, default='open')
    max_attendees = models.PositiveIntegerField(null=True, blank=True)
    min_age = models.PositiveIntegerField(null=True, blank=True, validators=[MinValueValidator(0), MaxValueValidator(100)])
    max_age = models.PositiveIntegerField(null=True, blank=True, validators=[MinValueValidator(0), MaxValueValidator(100)])
    
    # Pricing
    is_paid = models.BooleanField(default=False)
    ticket_price = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))
    currency = models.CharField(max_length=3, default='USD')
    
    # Additional Information
    dress_code = models.CharField(max_length=100, blank=True)
    bring_items = models.TextField(blank=True)
    house_rules = models.TextField(blank=True)
    contact_phone = models.CharField(max_length=20, blank=True)
    contact_email = models.EmailField(blank=True)
    
    # Media
    featured_image = models.ImageField(upload_to='parties/featured/%Y/%m/', null=True, blank=True)
    
    # Engagement
    tags = TaggableManager(blank=True)
    views_count = models.PositiveIntegerField(default=0)
    likes_count = models.PositiveIntegerField(default=0)
    shares_count = models.PositiveIntegerField(default=0)
    
    # Metadata
    allow_comments = models.BooleanField(default=True)
    allow_photos = models.BooleanField(default=True)
    allow_plus_ones = models.BooleanField(default=False)
    is_featured = models.BooleanField(default=False)
    is_recurring = models.BooleanField(default=False)
    
    class Meta:
        db_table = 'parties'
        verbose_name = 'Party'
        verbose_name_plural = 'Parties'
        ordering = ['-start_date']
    
    def __str__(self):
        return self.title
    
    @property
    def is_past(self):
        return self.end_date < timezone.now()
    
    @property
    def is_upcoming(self):
        return self.start_date > timezone.now()
    
    @property
    def can_rsvp(self):
        if self.rsvp_type == 'closed':
            return False
        if self.rsvp_deadline and timezone.now() > self.rsvp_deadline:
            return False
        if self.is_past:
            return False
        return True
    
    @property
    def attendee_count(self):
        return self.rsvps.filter(status='attending').count()


class PartyRSVP(BaseModel):
    RSVP_CHOICES = [
        ('attending', 'Attending'),
        ('maybe', 'Maybe'),
        ('not_attending', 'Not Attending'),
    ]
    
    party = models.ForeignKey(Party, on_delete=models.CASCADE, related_name='rsvps')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='party_rsvps')
    status = models.CharField(max_length=15, choices=RSVP_CHOICES, default='attending')
    plus_ones = models.PositiveIntegerField(default=0)
    message = models.TextField(blank=True)
    dietary_restrictions = models.TextField(blank=True)
    approved_by_host = models.BooleanField(default=False)
    checked_in = models.BooleanField(default=False)
    checked_in_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        db_table = 'party_rsvps'
        unique_together = ['party', 'user']
    
    def __str__(self):
        return f"{self.user.email} - {self.party.title} ({self.status})"


class PartyComment(BaseModel):
    party = models.ForeignKey(Party, on_delete=models.CASCADE, related_name='comments')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='party_comments')
    parent = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True, related_name='replies')
    content = models.TextField()
    is_edited = models.BooleanField(default=False)
    is_pinned = models.BooleanField(default=False)
    
    class Meta:
        db_table = 'party_comments'
        ordering = ['-is_pinned', '-created_at']
    
    def __str__(self):
        return f"Comment by {self.user.email} on {self.party.title}"


class PartyLike(BaseModel):
    party = models.ForeignKey(Party, on_delete=models.CASCADE, related_name='likes')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='party_likes')
    
    class Meta:
        db_table = 'party_likes'
        unique_together = ['party', 'user']
    
    def __str__(self):
        return f"{self.user.email} likes {self.party.title}" 
