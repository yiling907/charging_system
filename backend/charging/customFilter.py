# myapp/filters.py
from rest_framework.filters import BaseFilterBackend


class ChargerStatusFilter(BaseFilterBackend):
    def filter_queryset(self, request, queryset, view):
        charger_status = request.query_params.get("charger_status")

        if charger_status is not None:
            try:
                queryset = queryset.filter(chargers__status=charger_status)
            except ValueError:
                pass
        return queryset
