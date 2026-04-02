# api/urls.py
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    NetworkTrafficViewSet,
    ThreatIncidentViewSet,
    ResponseRuleViewSet,
    LogEntryViewSet,
)

router = DefaultRouter()
router.register(r'traffic', NetworkTrafficViewSet)
router.register(r'incidents', ThreatIncidentViewSet)
router.register(r'rules', ResponseRuleViewSet)
router.register(r'logs', LogEntryViewSet)

urlpatterns = [
    path('', include(router.urls)),
]