from django.contrib import admin
from django.urls import path, include

from charging import views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/charging/', include('charging.urls')),
    path('api/dashboard/', include('dashboard.urls')),
    path('user/login/', views.index, name='login'),
    path('register/', views.register, name='register'),
    path('home/', views.index, name='home'),
    path('user_inform/', views.user_inform, name='user_inform'),
    path('order_create/', views.order_create, name='order_create'),
    path('available_charger/', views.available_charger, name='available_charger'),

]
