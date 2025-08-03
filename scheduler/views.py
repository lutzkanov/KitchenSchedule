from rest_framework import viewsets, permissions
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from .models import User, Shift, WeeklySchedule, PTORequest, LunchBreakOverride, ShiftPreference
from .serializers import (
    UserSerializer, ShiftSerializer, WeeklyScheduleSerializer,
    PTORequestSerializer, LunchBreakOverrideSerializer, ShiftPreferenceSerializer
)

# Custom permission classes
class IsAdminOrReadOnly(permissions.BasePermission):
    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return True
        return request.user.is_authenticated and request.user.role == 'admin'

class IsAdminOrOwner(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        if request.user.role == 'admin':
            return True
        return obj.employee == request.user

# ViewSets
class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [IsAdminOrReadOnly]

class ShiftViewSet(viewsets.ModelViewSet):
    queryset = Shift.objects.all()
    serializer_class = ShiftSerializer
    permission_classes = [IsAdminOrReadOnly]

class WeeklyScheduleViewSet(viewsets.ModelViewSet):
    queryset = WeeklySchedule.objects.all()
    serializer_class = WeeklyScheduleSerializer
    permission_classes = [permissions.IsAuthenticated, IsAdminOrOwner]

    def get_queryset(self):
        user = self.request.user
        if user.role == 'admin':
            return WeeklySchedule.objects.all()
        return WeeklySchedule.objects.filter(employee=user)

class PTORequestViewSet(viewsets.ModelViewSet):
    queryset = PTORequest.objects.all()
    serializer_class = PTORequestSerializer
    permission_classes = [permissions.IsAuthenticated, IsAdminOrOwner]

    def get_queryset(self):
        user = self.request.user
        if user.role == 'admin':
            return PTORequest.objects.all()
        return PTORequest.objects.filter(employee=user)

class LunchBreakOverrideViewSet(viewsets.ModelViewSet):
    queryset = LunchBreakOverride.objects.all()
    serializer_class = LunchBreakOverrideSerializer
    permission_classes = [permissions.IsAuthenticated, IsAdminOrOwner]

    def get_queryset(self):
        user = self.request.user
        if user.role == 'admin':
            return LunchBreakOverride.objects.all()
        return LunchBreakOverride.objects.filter(schedule__employee=user)

class ShiftPreferenceViewSet(viewsets.ModelViewSet):
    queryset = ShiftPreference.objects.all()
    serializer_class = ShiftPreferenceSerializer
    permission_classes = [permissions.IsAuthenticated, IsAdminOrOwner]

    def get_queryset(self):
        user = self.request.user
        if user.role == 'admin':
            return ShiftPreference.objects.all()
        return ShiftPreference.objects.filter(employee=user)

# ✅ /me/ endpoint
@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def current_user_view(request):
    serializer = UserSerializer(request.user)
    return Response(serializer.data)
