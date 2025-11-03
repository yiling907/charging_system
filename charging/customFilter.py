# myapp/filters.py
from django.db.models import Prefetch
from rest_framework.filters import BaseFilterBackend

from .models import Charger


class ChargerStatusFilter(BaseFilterBackend):
    """
    自定义过滤器，根据 URL 参数 'status_code' 过滤产品。
    """
    def filter_queryset(self, request, queryset, view):
        charger_status = request.query_params.get('charger_status')

        if charger_status is not None:
            try:
                queryset = queryset.filter(chargers__status=charger_status).filter(chargers__is_active=True)
            except ValueError:
                pass
        return queryset

