from django.urls import path
from .views import GoogleApiKey


urlpatterns = [
    path('google_api_key/', GoogleApiKey.as_view(), name='google_api_key'),
]