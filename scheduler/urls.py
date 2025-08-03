from django.urls import include, path
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'users', views.UserViewSet)
router.register(r'shifts', views.ShiftViewSet)
router.register(r'schedules', views.WeeklyScheduleViewSet)
router.register(r'pto', views.PTORequestViewSet)
router.register(r'lunchbreaks', views.LunchBreakOverrideViewSet)
router.register(r'preferences', views.ShiftPreferenceViewSet)

urlpatterns = [
    path('', include(router.urls)),
    path('me/', views.current_user_view),  # ✅ New endpoint for current user
]
