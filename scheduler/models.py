from django.contrib.auth.models import AbstractUser
from django.db import models
from django.conf import settings
from django.core.exceptions import ValidationError
from django.utils.timezone import localtime
from datetime import time

class User(AbstractUser):
    ROLE_CHOICES = (
        ('admin', 'Admin'),
        ('employee', 'Employee'),
    )
    role = models.CharField(max_length=10, choices=ROLE_CHOICES)

    def __str__(self):
        return f"{self.username} ({self.role})"


class Shift(models.Model):
    SHIFT_TYPES = [
        ('long', 'Long Shift (09:00–22:30)'),
        ('first', 'First Shift (09:00–16:00)'),
        ('second', 'Second Shift (16:00–22:30)'),
        ('off', 'Day Off'),
    ]
    name = models.CharField(max_length=10, choices=SHIFT_TYPES)
    start_time = models.TimeField()
    end_time = models.TimeField()
    duration_hours = models.DecimalField(max_digits=4, decimal_places=2)  # includes break
    default_paid_hours = models.DecimalField(max_digits=4, decimal_places=2)

    def __str__(self):
        return self.get_name_display()


class WeeklySchedule(models.Model):
    employee = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    date = models.DateField()
    shift = models.ForeignKey(Shift, on_delete=models.CASCADE)
    locked = models.BooleanField(default=False)

    class Meta:
        unique_together = ('employee', 'date')

    def clean(self):
        from .models import PTORequest
        has_pto = PTORequest.objects.filter(
            employee=self.employee,
            date=self.date,
            status='approved'
        ).exists()
        if has_pto:
            raise ValidationError("Cannot assign a shift when PTO is approved on this date.")

    def get_effective_start_time(self):
        weekday = self.date.weekday()  # Monday=0, Sunday=6
        if weekday == 2 or weekday == 5:  # Wednesday=2, Saturday=5
            return time(8, 0, 0)  # 08:00 AM start for early shifts
        return self.shift.start_time

    def get_effective_paid_hours(self):
        weekday = self.date.weekday()
        base_hours = float(self.shift.default_paid_hours)
        if weekday == 2 or weekday == 5:
            return base_hours + 1.0  # Add 1 hour for earlier start
        return base_hours

    def __str__(self):
        return f"{self.employee.username} - {self.date} - {self.shift.name}"


class PTORequest(models.Model):
    employee = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    date = models.DateField()
    reason = models.TextField(blank=True)
    status = models.CharField(
        max_length=10,
        choices=[('pending', 'Pending'), ('approved', 'Approved'), ('denied', 'Denied')],
        default='pending'
    )

    def __str__(self):
        return f"{self.employee.username} - {self.date} ({self.status})"


class LunchBreakOverride(models.Model):
    schedule = models.OneToOneField(WeeklySchedule, on_delete=models.CASCADE)
    extended = models.BooleanField(default=False)  # True = 1.5h, False = 1h

    def adjusted_paid_hours(self):
        return self.schedule.shift.default_paid_hours - (0.5 if self.extended else 0)

    def __str__(self):
        return f"{self.schedule} - Extended: {self.extended}"


class ShiftPreference(models.Model):
    employee = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    date = models.DateField()
    preferred_shift = models.ForeignKey(Shift, on_delete=models.CASCADE)

    class Meta:
        unique_together = ('employee', 'date')

    def __str__(self):
        return f"{self.employee.username} prefers {self.preferred_shift.name} on {self.date}"
