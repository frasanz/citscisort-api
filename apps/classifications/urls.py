from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework_nested import routers
from .views import (
    CategoryViewSet, UserProfileViewSet,
    ClassificationViewSet, ClassificationSessionViewSet,
    GeneralStatsView, AbstractStatsView, MyStatsView, SavedAbstractViewSet, FollowedDebateViewSet,
    AbstractDebateViewSet, DebateCommentViewSet, NotificationViewSet
)

router = DefaultRouter()
router.register(r'categories', CategoryViewSet, basename='category')
router.register(r'profiles', UserProfileViewSet, basename='userprofile')
router.register(r'classifications', ClassificationViewSet, basename='classification')
router.register(r'sessions', ClassificationSessionViewSet, basename='classificationsession')
router.register(r'saved-abstracts', SavedAbstractViewSet, basename='savedabstract')
router.register(r'followed-debates', FollowedDebateViewSet, basename='followeddebate')
router.register(r'debates', AbstractDebateViewSet, basename='debate')
router.register(r'notifications', NotificationViewSet, basename='notification')

# Nested router for comments within debates
debates_router = routers.NestedDefaultRouter(router, r'debates', lookup='debate')
debates_router.register(r'comments', DebateCommentViewSet, basename='debate-comments')

urlpatterns = [
    path('', include(router.urls)),
    path('', include(debates_router.urls)),
    path('stats/overview/', GeneralStatsView.as_view(), name='general-stats'),
    path('stats/abstracts/', AbstractStatsView.as_view(), name='abstract-stats'),
    path('stats/me/', MyStatsView.as_view(), name='my-stats'),
]
