import logging

from django.db.models import Prefetch
from django.forms import renderers
from django.shortcuts import render
from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema
from rest_framework import viewsets, permissions, status, filters
from rest_framework.authentication import TokenAuthentication
from rest_framework.decorators import action, authentication_classes, permission_classes
from rest_framework.generics import RetrieveAPIView, UpdateAPIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend

from .customFilter import ChargerStatusFilter
from .models import Station, Charger, ChargingRecord, User
from .serializers import (
    StationSerializer, ChargerSerializer,
    ChargingRecordSerializer
)
from .permissions import IsOperator, IsMaintenanceStaff
from payments.services import create_payment

# views.py
from rest_framework.authtoken.views import ObtainAuthToken
from rest_framework.authtoken.models import Token
from rest_framework.response import Response
from .serializers import UserSerializer  # 自定义用户序列化器


def index(request):
    return render(request, 'index.html')


def register(request):
    return render(request, 'register.html')


def user_inform(request):
    return render(request, 'userInfo.html')


def order_create(request, charger_id):
    charger = Charger.objects.filter(id=charger_id)
    return render(request, 'orderCreate.html', context={'charger': charger})


def available_station(request):
    return render(request, 'availableStation.html')


def stations_detail(request, id):
    return render(request, 'stationDetail.html')


def chargers_detail(request, id):
    return render(request, 'chargerDetail.html')

def records(request):
    return render(request, 'chargerRecord.html')

def temp(request):
    return render(request, 'temp.html')


class UserLoginView(ObtainAuthToken):
    def post(self, request, *args, **kwargs):
        # 验证用户名和密码
        serializer = self.serializer_class(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data['user']

        # 生成或获取令牌（用于后续接口认证）
        token, created = Token.objects.get_or_create(user=user)

        # 返回用户信息和令牌（仅包含普通用户可查看的字段）
        return Response({
            'token': token.key,
            'user': UserSerializer(user).data  # 序列化用户信息（如 username、phone 等）
        })


class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    lookup_field = 'username'

    @action(detail=True, methods=['post'])
    def register(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = self.get_object()

        token, created = Token.objects.get_or_create(user=user)

        # 返回用户信息和令牌（仅包含普通用户可查看的字段）
        return Response({
            'token': token.key,
            'user': UserSerializer(user).data  # 序列化用户信息（如 username、phone 等）
        })


charger_status = openapi.Parameter(
    'charger_status',  # 参数名称，必须与您的过滤器中使用的名称一致
    openapi.IN_QUERY,  # 参数位置：查询参数
    description="Filter products by charger status)",
    type=openapi.TYPE_STRING,  # 参数类型
    required=False  # 是否必须
)


class StationViewSet(viewsets.ModelViewSet):
    serializer_class = StationSerializer
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['name', 'address']
    ordering_fields = ['name', 'created_at']

    def get_queryset(self):
        queryset = Station.objects.all()

        charger_status = self.request.query_params.get('charger_status')

        if charger_status:
            queryset = queryset.prefetch_related(
                Prefetch(
                    'chargers',
                    queryset=Charger.objects.filter(status=charger_status),  # 按状态过滤充电桩
                    to_attr='filtered_chargers'  # 自定义属性名，避免覆盖原related_name
                )
            )
        else:
            queryset = queryset.exclude(chargers__isnull=True).prefetch_related(
                Prefetch(
                    'chargers',
                    queryset=Charger.objects.all(),
                    to_attr='filtered_chargers'
                ))

        return queryset

    @swagger_auto_schema(
        manual_parameters=[charger_status],
    )
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)


class ChargerViewSet(viewsets.ModelViewSet):
    queryset = Charger.objects.all()
    serializer_class = ChargerSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    filterset_fields = ['station', 'status', 'charger_type']
    search_fields = ['code', 'station__name']

    @action(detail=True, methods=['post'])
    def set_maintenance(self, request, pk=None):
        """Set charger to maintenance mode"""
        charger = self.get_object()
        charger.status = 'maintenance'
        charger.save()
        return Response({'status': 'maintenance mode activated'})

    @action(detail=True, methods=['post'])
    def set_active(self, request, pk=None):
        """Set charger back to active mode"""
        charger = self.get_object()
        charger.status = 'idle'
        charger.save()
        return Response({'status': 'charger activated'})

    @action(detail=True, methods=['post'])
    def set_inactive(self, request, pk=None):
        charger = self.get_object()
        charger.status = 'charging'
        charger.save()
        return Response({'status': 'charger inactivated'})


class ChargingRecordViewSet(viewsets.ModelViewSet):
    queryset = ChargingRecord.objects.all()
    serializer_class = ChargingRecordSerializer
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['charger', 'user', 'pay_status']
    ordering_fields = ['start_time', 'fee']


    def perform_create(self, serializer):
        # 从验证后的数据中获取充电器对象（已通过序列化器验证）
        charger = serializer.validated_data['charger']

        # 更新充电器状态
        charger.status = 'charging'
        charger.save(update_fields=['status'])  # 只更新status字段，效率更高

        # 保存充电记录（可在此处添加其他关联字段，如创建者）
        serializer.save()  # 无需返回值，DRF会自动处理后续响应

    @action(detail=True, methods=['post'])
    def initiate_payment(self, request, pk=None):
        """Initiate payment process"""
        record = self.get_object()
        if record.pay_status != 'unpaid':
            return Response(
                {'error': 'This record is already paid'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Call payment service
        payment_url = create_payment(record)
        return Response({'payment_url': payment_url})

    @action(detail=False, methods=['get'])
    def export_as_csv(self, request):
        """Export selected records as CSV"""
        import csv
        from django.http import HttpResponse
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="charging_records.csv"'
        queryset = ChargingRecord.objects.all()

        writer = csv.writer(response)
        writer.writerow(
            ['ID', 'Charger', 'License Plate', 'Start Time', 'End Time', 'Energy (kWh)', 'Fee (¥)', 'Payment Status'])
        for obj in queryset:
            writer.writerow([
                obj.id,
                obj.charger.code,
                obj.start_time,
                obj.end_time,
                obj.electricity,
                obj.fee,
                obj.get_pay_status_display()
            ])
        return response
