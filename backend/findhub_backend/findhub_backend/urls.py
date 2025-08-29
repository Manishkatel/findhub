from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from drf_spectacular.views import (
    SpectacularAPIView,
    SpectacularRedocView,
    SpectacularSwaggerView,
)
from rest_framework import permissions
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework import status

@api_view(['GET'])
@permission_classes([permissions.AllowAny])
def health_check(request):
    return Response({
        'status': 'healthy',
        'message': 'Party Spark Creator Hub API is running',
        'version': '1.0.0'
    }, status=status.HTTP_200_OK)

@api_view(['GET'])
@permission_classes([permissions.AllowAny])
def api_info(request):
    return Response({
        'api_name': 'FIND_HUB API',
        'version': '1.0.0', 
        'description': 'A comprehensive API for event and clubs management',
        'documentation': {
            'swagger': f"{request.build_absolute_uri('/')[:-1]}/api/docs/",
            'redoc': f"{request.build_absolute_uri('/')[:-1]}/api/redoc/"
        },
    })

urlpatterns = [
    path('admin/', admin.site.urls),
    path('health/', health_check, name='health_check'),
    path('api/info/', api_info, name='api_info'),
    
    # API Documentation
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    path('api/docs/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
    path('api/redoc/', SpectacularRedocView.as_view(url_name='schema'), name='redoc'),
    
    # API v1 endpoints
    path('api/v1/auth/', include('apps.accounts.urls')),
    path('api/v1/parties/', include('apps.parties.urls')),
    path('api/v1/invitations/', include('apps.invitations.urls')),
    path('api/v1/notifications/', include('apps.notifications.urls')),
    path('api/v1/media/', include('apps.media.urls')),
    path('api/v1/analytics/', include('apps.analytics.urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)

admin.site.site_header = "Party Spark Creator Hub Admin"
admin.site.site_title = "Party Spark Admin"
admin.site.index_title = "Welcome to Party Spark Administration" 
