from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework import status
from datetime import date
from .models import User, Shift, WeeklySchedule, PTORequest
from django.core.exceptions import ValidationError

class ModelTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='testuser', password='testpass', role='employee')
        self.shift = Shift.objects.create(
            name='first',
            start_time='09:00',
            end_time='16:00',
            duration_hours=7.00,
            default_paid_hours=6.5,
        )

    def test_pto_blocks_shift(self):
        # Create approved PTO for today
        PTORequest.objects.create(employee=self.user, date=date.today(), status='approved')
        ws = WeeklySchedule(employee=self.user, date=date.today(), shift=self.shift)
        with self.assertRaises(ValidationError) as context:
            ws.clean()
        self.assertIn("Cannot assign a shift when PTO is approved", str(context.exception))

    def test_shift_str(self):
        self.assertEqual(str(self.shift), 'First Shift (09:00–16:00)')

class APITests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(username='apiuser', password='testpass', role='employee')
        self.admin = User.objects.create_user(username='admin', password='adminpass', role='admin')
        self.shift = Shift.objects.create(
            name='first',
            start_time='09:00',
            end_time='16:00',
            duration_hours=7.00,
            default_paid_hours=6.5,
        )
        # Obtain token for user
        response = self.client.post('/api/token/', {'username': 'apiuser', 'password': 'testpass'})
        self.token = response.data['access']

    def test_auth_required_for_schedules(self):
        url = reverse('weeklyschedule-list')
        # No auth header
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

        # With auth
        self.client.credentials(HTTP_AUTHORIZATION='Bearer ' + self.token)
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_create_schedule(self):
        self.client.credentials(HTTP_AUTHORIZATION='Bearer ' + self.token)
        url = reverse('weeklyschedule-list')
        data = {
            'employee_id': self.user.id,
            'date': str(date.today()),
            'shift_id': self.shift.id,
        }
        response = self.client.post(url, data)
        # Since no PTO on this date, it should succeed
        self.assertIn(response.status_code, [status.HTTP_201_CREATED, status.HTTP_200_OK])
