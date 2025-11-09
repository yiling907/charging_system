from django.db.models import Sum, Count
from django.utils import timezone
from datetime import timedelta
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAdminUser
from charging.models import ChargingRecord, Station, Charger


class DashboardStatsView(APIView):

    def get(self, request):
        """Get key performance indicators"""
        today = timezone.now().date()
        week_ago = today - timedelta(days=7)

        # Total statistics
        total_stations = Station.objects.count()
        total_chargers = Charger.objects.count()
        active_chargers = Charger.objects.filter(status__in=['idle', 'charging']).count()

        # Revenue statistics
        daily_revenue = ChargingRecord.objects.filter(
            start_time__date=today,
            pay_status='paid'
        ).aggregate(total=Sum('fee'))['total'] or 0

        weekly_revenue = ChargingRecord.objects.filter(
            start_time__date__gte=week_ago,
            pay_status='paid'
        ).aggregate(total=Sum('fee'))['total'] or 0

        # Session statistics
        daily_sessions = ChargingRecord.objects.filter(
            start_time__date=today
        ).count()

        # Energy statistics
        daily_energy = ChargingRecord.objects.filter(
            start_time__date=today
        ).aggregate(total=Sum('electricity'))['total'] or 0

        return Response({
            'stations': {
                'total': total_stations,
                'active': Station.objects.filter(is_active=True).count()
            },
            'chargers': {
                'total': total_chargers,
                'active': active_chargers,
                'faulty': Charger.objects.filter(status='fault').count()
            },
            'revenue': {
                'daily': daily_revenue,
                'weekly': weekly_revenue,
                'monthly': self.get_monthly_revenue()
            },
            'sessions': {
                'daily': daily_sessions,
                'weekly': ChargingRecord.objects.filter(
                    start_time__date__gte=week_ago
                ).count()
            },
            'energy': {
                'daily': daily_energy,
                'weekly': ChargingRecord.objects.filter(
                    start_time__date__gte=week_ago
                ).aggregate(total=Sum('electricity'))['total'] or 0
            }
        })

    def get_monthly_revenue(self):
        """Calculate revenue for current month"""
        now = timezone.now()
        start_of_month = now.replace(day=1, hour=0, minute=0, second=0)

        return ChargingRecord.objects.filter(
            start_time__gte=start_of_month,
            pay_status='paid'
        ).aggregate(total=Sum('fee'))['total'] or 0