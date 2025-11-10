from django.contrib import admin
from django.urls import path, include

from charging import views
from django.urls import re_path
from rest_framework import permissions
from drf_yasg.views import get_schema_view
from drf_yasg import openapi

schema_view = get_schema_view(
    openapi.Info(
        title="Snippets API",
        default_version='v1',
        description="Test description",
        terms_of_service="https://www.google.com/policies/terms/",
        contact=openapi.Contact(email="contact@snippets.local"),
        license=openapi.License(name="BSD License"),
    ),
    public=True,
    permission_classes=(permissions.AllowAny,),
)

urlpatterns = [
    path('swagger.<format>/', schema_view.without_ui(cache_timeout=0), name='schema-json'),
    path('swagger/', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),
    path('redoc/', schema_view.with_ui('redoc', cache_timeout=0), name='schema-redoc'),
    path('admin/', admin.site.urls),
    path('api/charging/', include('charging.urls')),
    path('api/dashboard/', include('dashboard.urls')),
    path('api/v1/', include('proxy_api.urls')),
    path('user/login/', views.index, name='login'),
    path('register/', views.register, name='register'),
    path('home/', views.index, name='home'),
    path('user_inform/', views.user_inform, name='user_inform'),
    path('order_create/<charger_id>', views.order_create, name='order_create'),
    path('available_station/', views.available_station, name='available_station'),
    path('stations/<id>', views.stations_detail, name='stations'),
    path('chargers/<id>', views.chargers_detail, name='chargers'),
    path('records/', views.records, name='records'),
    path('temp/', views.temp, name='temp'),
]
