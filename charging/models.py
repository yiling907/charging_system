from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils import timezone
import uuid

class User(AbstractUser):
    """Extended user model with role-based access"""
    phone = models.CharField(max_length=15, blank=True)
    is_maintenance = models.BooleanField(default=False)
    is_operator = models.BooleanField(default=False)

    class Meta:
        verbose_name = "User"
        verbose_name_plural = "Users"

    def __str__(self):
        return self.username


class Station(models.Model):
    """Charging station location"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField("Station Name", max_length=100)
    address = models.TextField("Address")
    latitude = models.DecimalField("Latitude", max_digits=9, decimal_places=6, null=True, blank=True)
    longitude = models.DecimalField("Longitude", max_digits=9, decimal_places=6, null=True, blank=True)
    is_active = models.BooleanField("Operational", default=True)
    contact_phone = models.CharField("Contact Phone", max_length=15, blank=True)
    created_at = models.DateTimeField("Created At", auto_now_add=True)
    updated_at = models.DateTimeField("Updated At", auto_now=True)

    def __str__(self):
        return self.name

    @property
    def available_chargers(self):
        """Return count of available chargers"""
        return self.chargers.filter(status='idle').count()

    class Meta:
        verbose_name = "Charging Station"
        verbose_name_plural = "Charging Stations"
        ordering = ['name']


class Charger(models.Model):
    """Electric vehicle charger device"""
    CHARGER_TYPES = (
        ('DC', 'Direct Current (Fast)'),
        ('AC', 'Alternating Current (Slow)'),
    )
    STATUS_CHOICES = (
        ('idle', 'Idle'),
        ('charging', 'Charging'),
        ('fault', 'Faulty'),
        ('maintenance', 'Maintenance'),
    )

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    station = models.ForeignKey(Station, on_delete=models.CASCADE, related_name="chargers")
    code = models.CharField("Device Code", max_length=50, unique=True)
    charger_type = models.CharField("Charger Type", max_length=2, choices=CHARGER_TYPES)
    power = models.IntegerField("Power (kW)", help_text="e.g. 60kW")
    status = models.CharField("Status", max_length=20, choices=STATUS_CHOICES, default='idle')
    last_maintenance = models.DateField("Last Maintenance", null=True, blank=True)
    firmware_version = models.CharField("Firmware Version", max_length=50, blank=True)
    created_at = models.DateTimeField("Installation Date", auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.station.name} - {self.code}"

    class Meta:
        verbose_name = "Charger"
        verbose_name_plural = "Chargers"
        ordering = ['station__name', 'code']


class ChargingRecord(models.Model):
    """Record of a completed or ongoing charging session"""
    PAY_STATUS = (
        ('unpaid', 'Unpaid'),
        ('paid', 'Paid'),
        ('refunded', 'Refunded'),
    )
    STATUS = (
        ('completed', 'Unpaid'),
        ('charging', 'Paid'),
        ('failed', 'Refunded'),
    )

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    charger = models.ForeignKey(Charger, on_delete=models.CASCADE, related_name="records")
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name="charging_sessions")
    start_time = models.DateTimeField("Start Time")
    end_time = models.DateTimeField("End Time", null=True, blank=True)
    duration = models.IntegerField("Duration (minutes)", null=True, blank=True)
    electricity = models.DecimalField("Energy (kWh)", max_digits=5, decimal_places=2, null=True, blank=True)
    fee = models.DecimalField("Total Fee (¥)", max_digits=6, decimal_places=2, null=True, blank=True)
    pay_status = models.CharField("Payment Status", max_length=10, choices=PAY_STATUS, default='unpaid')
    status = models.CharField("Status", max_length=10, choices=STATUS, default='charging')
    transaction_id = models.CharField("Transaction ID", max_length=100, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        # Calculate duration if both times are present
        if self.start_time and self.end_time:
            self.duration = int((self.end_time - self.start_time).total_seconds() / 60)
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.user.email} - {self.start_time.strftime('%Y-%m-%d')}"

    class Meta:
        verbose_name = "Charging Record"
        verbose_name_plural = "Charging Records"
        ordering = ['-start_time']


class MaintenanceRecord(models.Model):
    """Record of maintenance activities on chargers"""
    MAINTENANCE_TYPES = (
        ('routine', 'Routine Check'),
        ('repair', 'Repair'),
        ('upgrade', 'Firmware Upgrade'),
        ('replacement', 'Part Replacement'),
    )

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    charger = models.ForeignKey(Charger, on_delete=models.CASCADE, related_name="maintenances")
    worker = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, limit_choices_to={'is_maintenance': True})
    maintenance_type = models.CharField("Type", max_length=20, choices=MAINTENANCE_TYPES)
    content = models.TextField("Details")
    maintenance_time = models.DateTimeField("Maintenance Time")
    duration = models.IntegerField("Duration (minutes)", help_text="Time spent on maintenance")
    parts_used = models.TextField("Parts Used", blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.charger.code} - {self.maintenance_time.strftime('%Y-%m-%d')}"

    class Meta:
        verbose_name = "Maintenance Record"
        verbose_name_plural = "Maintenance Records"
        ordering = ['-maintenance_time']


