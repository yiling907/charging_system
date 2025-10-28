from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views
from .views import UserLoginView

router = DefaultRouter()
router.register(r'stations', views.StationViewSet, basename='stations')
router.register(r'chargers', views.ChargerViewSet, basename='chargers')
router.register(r'records', views.ChargingRecordViewSet,basename='records')
router.register(r'reservations', views.ReservationViewSet,basename='reservations')

urlpatterns = [
    path('', include(router.urls)),

]