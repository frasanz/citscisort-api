"""
URL configuration for CitSciSort project.
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from drf_spectacular.views import SpectacularAPIView, SpectacularRedocView, SpectacularSwaggerView

urlpatterns = [
    path('admin/', admin.site.urls),
    
    # API Documentation
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    path('api/docs/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
    path('api/redoc/', SpectacularRedocView.as_view(url_name='schema'), name='redoc'),
    
    # API Authentication endpoints
    path('api/auth/', include('dj_rest_auth.urls')),
    path('api/auth/', include('apps.authentication.urls')),  # Custom auth endpoints
    path('api/auth/registration/', include('dj_rest_auth.registration.urls')),
    
    # API endpoints
    path('api/', include('apps.abstracts.urls')),
    path('api/', include('apps.classifications.urls')),
]

# Serve media files in development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
