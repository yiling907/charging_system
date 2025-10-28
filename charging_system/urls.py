from django.contrib import admin
from django.urls import path, include

from charging.views import UserLoginView

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/charging/', include('charging.urls')),
    path('api/dashboard/', include('dashboard.urls')),
    path('api/login/', UserLoginView.as_view(), name='user_login'),

]