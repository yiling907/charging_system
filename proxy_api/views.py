import requests
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .utils import get_google_maps_api_key

class GoogleApiKey(APIView):
    def get(self, request):
        try:
            api_key = get_google_maps_api_key()

            return Response({"google_maps_api_key": api_key}, status=status.HTTP_200_OK)

        except Exception as e:
            return Response(
                {"error": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
