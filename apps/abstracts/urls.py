from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import AbstractViewSet

router = DefaultRouter()
router.register(r'abstracts', AbstractViewSet, basename='abstract')

urlpatterns = [
    path('', include(router.urls)),
]
