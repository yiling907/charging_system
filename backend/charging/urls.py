from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r"stations", views.StationViewSet, basename="stations")
router.register(r"chargers", views.ChargerViewSet, basename="chargers")
router.register(r"records", views.ChargingRecordViewSet, basename="records")
router.register(r"user", views.UserViewSet, basename="users")


urlpatterns = [
    path("", include(router.urls)),
    path("login/", views.UserLoginView.as_view(), name="login"),
    path("api-auth/", include("rest_framework.urls", namespace="rest_framework")),
]
