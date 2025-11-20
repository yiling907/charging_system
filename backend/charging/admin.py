from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.utils.html import format_html
from django.urls import reverse
import uuid
from .models import (
    Station, Charger, ChargingRecord,
    MaintenanceRecord, User
)


@admin.register(User)
class UserAdmin(UserAdmin):
    list_display = ('username', 'email', 'first_name', 'last_name', 'is_staff', 'is_maintenance', 'is_operator')
    list_filter = ('is_staff', 'is_maintenance', 'is_operator')
    search_fields = ('username', 'email', 'first_name', 'last_name')


@admin.register(Station)
class StationAdmin(admin.ModelAdmin):
    list_display = ('name', 'address', 'charger_count', 'available_chargers', 'is_active', 'contact_phone')
    search_fields = ('name', 'address')
    list_filter = ('is_active',)
    readonly_fields = ('created_at', 'updated_at')
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'address', 'latitude', 'longitude')
        }),
        ('Operational Status', {
            'fields': ('is_active', 'contact_phone', 'created_at', 'updated_at')
        }),
    )

    def charger_count(self, obj):
        """Return total number of chargers at this station"""
        return obj.chargers.count()

    charger_count.short_description = "Total Chargers"


@admin.register(Charger)
class ChargerAdmin(admin.ModelAdmin):
    list_display = ('code', 'station', 'charger_type', 'power', 'status_badge',
                    'last_maintenance', 'record_count', 'firmware_version')
    search_fields = ('code', 'station__name', 'firmware_version')
    list_filter = ('status', 'charger_type', 'station')
    readonly_fields = ('created_at', 'updated_at')
    fieldsets = (
        ('Device Information', {
            'fields': ('station', 'code', 'charger_type', 'power', 'firmware_version')
        }),
        ('Operational Status', {
            'fields': ('status', 'last_maintenance', 'created_at', 'updated_at')
        }),
    )

    def status_badge(self, obj):
        """Display status with colored badges"""
        color_map = {
            'idle': 'success',
            'charging': 'primary',
            'fault': 'danger',
            'maintenance': 'warning'
        }
        color = color_map.get(obj.status, 'secondary')
        return format_html(
            '<span class="badge bg-{}">{}</span>',
            color, dict(Charger.STATUS_CHOICES)[obj.status]
        )

    status_badge.short_description = "Status"
    status_badge.admin_order_field = 'status'

    def record_count(self, obj):
        """Total charging records for this charger"""
        return obj.records.count()

    record_count.short_description = "Total Sessions"


@admin.register(ChargingRecord)
class ChargingRecordAdmin(admin.ModelAdmin):
    list_display = ('id', 'charger', 'user', 'start_time',
                    'end_time', 'duration', 'electricity', 'fee', 'pay_status_badge')
    search_fields = ( 'user__username', 'charger__code', 'transaction_id')
    list_filter = ('pay_status', 'charger__station', 'start_time')
    date_hierarchy = 'start_time'
    readonly_fields = ('duration', 'created_at')
    actions = ['mark_as_paid', 'export_as_csv']

    def pay_status_badge(self, obj):
        """Display payment status with colored badges"""
        color_map = {
            'unpaid': 'danger',
            'paid': 'success',
            'refunded': 'secondary'
        }
        color = color_map.get(obj.pay_status, 'secondary')
        return format_html(
            '<span class="badge bg-{}">{}</span>',
            color, dict(ChargingRecord.PAY_STATUS)[obj.pay_status]
        )

    pay_status_badge.short_description = "Payment Status"

    def mark_as_paid(self, request, queryset):
        """Bulk update payment status to paid"""
        updated = queryset.filter(pay_status='unpaid').update(
            pay_status='paid',
            transaction_id=f"ADMIN-{uuid.uuid4().hex[:8]}"
        )
        self.message_user(request, f'Successfully updated {updated} records to paid status')

    mark_as_paid.short_description = "Mark selected as paid"

    def export_as_csv(self, request, queryset):
        """Export selected records as CSV"""
        import csv
        from django.http import HttpResponse
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="charging_records.csv"'

        writer = csv.writer(response)
        writer.writerow(
            ['ID', 'Charger', 'License Plate', 'Start Time', 'End Time', 'Energy (kWh)', 'Fee (¥)', 'Payment Status'])
        for obj in queryset:
            writer.writerow([
                obj.id,
                obj.charger.code,
                obj.start_time,
                obj.end_time,
                obj.electricity,
                obj.fee,
                obj.get_pay_status_display()
            ])
        return response

    export_as_csv.short_description = "Export selected to CSV"


@admin.register(MaintenanceRecord)
class MaintenanceRecordAdmin(admin.ModelAdmin):
    list_display = ('id', 'charger', 'worker', 'maintenance_type', 'maintenance_time', 'duration')
    search_fields = ('charger__code', 'worker__username', 'content', 'parts_used')
    list_filter = ('maintenance_type', 'maintenance_time')
    date_hierarchy = 'maintenance_time'

    def save_model(self, request, obj, form, change):
        """Update charger status after maintenance"""
        super().save_model(request, obj, form, change)
        # Update charger status if maintenance is completed
        if not change and obj.charger.status in ['fault', 'maintenance']:
            obj.charger.status = 'idle'
            obj.charger.last_maintenance = obj.maintenance_time.date()
            obj.charger.save()

