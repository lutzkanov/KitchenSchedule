from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User, Shift, WeeklySchedule, PTORequest, LunchBreakOverride, ShiftPreference


admin.site.register(User, UserAdmin)
admin.site.register(Shift)
admin.site.register(WeeklySchedule)
admin.site.register(PTORequest)
admin.site.register(LunchBreakOverride)
admin.site.register(ShiftPreference)

