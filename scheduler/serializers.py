from rest_framework import serializers
from django.core.exceptions import ValidationError as DjangoValidationError
from django.contrib.auth.password_validation import validate_password
from .models import User, Shift, WeeklySchedule, PTORequest, LunchBreakOverride, ShiftPreference

class UserSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, required=False, allow_blank=True, validators=[validate_password])
    password_confirm = serializers.CharField(write_only=True, required=False, allow_blank=True)

    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'role', 'password', 'password_confirm']

    def validate(self, attrs):
        password = attrs.get('password')
        password_confirm = attrs.get('password_confirm')

        # If password is set, password_confirm must match
        if password or password_confirm:
            if password != password_confirm:
                raise serializers.ValidationError({"password_confirm": "Password fields didn't match."})

        return attrs

    def create(self, validated_data):
        password = validated_data.pop('password', None)
        validated_data.pop('password_confirm', None)
        user = User(**validated_data)
        if password:
            user.set_password(password)
        else:
            user.set_unusable_password()
        user.save()
        return user

    def update(self, instance, validated_data):
        password = validated_data.pop('password', None)
        validated_data.pop('password_confirm', None)
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        if password:
            instance.set_password(password)
        instance.save()
        return instance

class ShiftSerializer(serializers.ModelSerializer):
    class Meta:
        model = Shift
        fields = '__all__'

class WeeklyScheduleSerializer(serializers.ModelSerializer):
    shift = ShiftSerializer(read_only=True)
    shift_id = serializers.PrimaryKeyRelatedField(
        queryset=Shift.objects.all(), source='shift', write_only=True
    )
    employee = UserSerializer(read_only=True)
    employee_id = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.all(), source='employee', write_only=True
    )
    effective_start_time = serializers.SerializerMethodField()
    effective_paid_hours = serializers.SerializerMethodField()

    class Meta:
        model = WeeklySchedule
        fields = [
            'id', 'employee', 'employee_id', 'date', 'shift', 'shift_id', 'locked',
            'effective_start_time', 'effective_paid_hours'
        ]

    def get_effective_start_time(self, obj):
        return obj.get_effective_start_time().strftime("%H:%M:%S")

    def get_effective_paid_hours(self, obj):
        return "{:.2f}".format(obj.get_effective_paid_hours())

    def validate(self, data):
        employee = data.get('employee') or getattr(self.instance, 'employee', None)
        date = data.get('date') or getattr(self.instance, 'date', None)

        from .models import PTORequest
        if PTORequest.objects.filter(employee=employee, date=date, status='approved').exists():
            raise serializers.ValidationError("Cannot assign a shift when PTO is approved on this date.")

        instance = self.instance or WeeklySchedule(**data)
        try:
            instance.clean()
        except DjangoValidationError as e:
            raise serializers.ValidationError(e.message_dict)

        return data

class PTORequestSerializer(serializers.ModelSerializer):
    employee = UserSerializer(read_only=True)
    employee_id = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.all(), source='employee', write_only=True
    )
    class Meta:
        model = PTORequest
        fields = ['id', 'employee', 'employee_id', 'date', 'reason', 'status']

class LunchBreakOverrideSerializer(serializers.ModelSerializer):
    schedule = WeeklyScheduleSerializer(read_only=True)
    schedule_id = serializers.PrimaryKeyRelatedField(
        queryset=WeeklySchedule.objects.all(), source='schedule', write_only=True
    )
    class Meta:
        model = LunchBreakOverride
        fields = ['id', 'schedule', 'schedule_id', 'extended']

class ShiftPreferenceSerializer(serializers.ModelSerializer):
    employee = UserSerializer(read_only=True)
    employee_id = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.all(), source='employee', write_only=True
    )
    preferred_shift = ShiftSerializer(read_only=True)
    preferred_shift_id = serializers.PrimaryKeyRelatedField(
        queryset=Shift.objects.all(), source='preferred_shift', write_only=True
    )
    class Meta:
        model = ShiftPreference
        fields = ['id', 'employee', 'employee_id', 'date', 'preferred_shift', 'preferred_shift_id']
