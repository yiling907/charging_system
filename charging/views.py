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
from .models import Station, Charger, ChargingRecord, Reservation, User
from .serializers import (
    StationSerializer, ChargerSerializer,
    ChargingRecordSerializer, ReservationSerializer
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


def order_create(request):
    return render(request, 'orderCreate.html')


def available_station(request):
    return render(request, 'availableStation.html')


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


@authentication_classes([TokenAuthentication])
class StationViewSet(viewsets.ModelViewSet):
    serializer_class = StationSerializer
    filter_backends = [filters.SearchFilter, filters.OrderingFilter, ChargerStatusFilter]
    search_fields = ['name', 'address']
    ordering_fields = ['name', 'created_at']

    def get_queryset(self):
        # 基础查询集
        queryset = Station.objects.all()

        # 获取过滤条件中的充电桩状态（假设你的过滤器用'charger_status'作为参数名）
        charger_status = self.request.query_params.get('charger_status')

        # 如果有状态过滤条件，对预加载的chargers也应用过滤
        if charger_status:
            queryset = queryset.prefetch_related(
                Prefetch(
                    'chargers',
                    queryset=Charger.objects.filter(status=charger_status),  # 按状态过滤充电桩
                    to_attr='filtered_chargers'  # 自定义属性名，避免覆盖原related_name
                )
            )
        else:
            # 无过滤时加载所有充电桩
            queryset = queryset.exclude(chargers__isnull=True).prefetch_related(
            Prefetch(
                'chargers',
                queryset=Charger.objects.all(),  # 全部充电桩
                to_attr='filtered_chargers'  # 同样用 filtered_chargers
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

    @action(detail=True, methods=['post'], permission_classes=[IsMaintenanceStaff])
    def set_maintenance(self, request, pk=None):
        """Set charger to maintenance mode"""
        charger = self.get_object()
        charger.status = 'maintenance'
        charger.save()
        return Response({'status': 'maintenance mode activated'})

    @action(detail=True, methods=['post'], permission_classes=[IsMaintenanceStaff])
    def set_active(self, request, pk=None):
        """Set charger back to active mode"""
        charger = self.get_object()
        charger.status = 'idle'
        charger.save()
        return Response({'status': 'charger activated'})


class ChargingRecordViewSet(viewsets.ModelViewSet):
    serializer_class = ChargingRecordSerializer
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['charger', 'user', 'pay_status']
    ordering_fields = ['start_time', 'fee']

    def get_queryset(self):
        """Users can only see their own records, operators see all"""
        user = self.request.user
        if user.is_operator or user.is_staff:
            return ChargingRecord.objects.all()
        return ChargingRecord.objects.filter(user=user)

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


class ReservationViewSet(viewsets.ModelViewSet):
    serializer_class = ReservationSerializer
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['charger', 'status']
    ordering_fields = ['start_time']

    def get_queryset(self):
        """Users see their own reservations, operators see all"""
        user = self.request.user
        if user.is_operator or user.is_staff:
            return Reservation.objects.all()
        return Reservation.objects.filter(user=user)

    @action(detail=True, methods=['post'])
    def confirm(self, request, pk=None):
        """Confirm a reservation"""
        reservation = self.get_object()
        if reservation.user != request.user and not request.user.is_operator:
            return Response(
                {'error': 'Not authorized'},
                status=status.HTTP_403_FORBIDDEN
            )

        reservation.status = 'confirmed'
        reservation.save()
        return Response({'status': 'reservation confirmed'})

    @action(detail=True, methods=['post'])
    def cancel(self, request, pk=None):
        """Cancel a reservation"""
        reservation = self.get_object()
        if reservation.user != request.user and not request.user.is_operator:
            return Response(
                {'error': 'Not authorized'},
                status=status.HTTP_403_FORBIDDEN
            )

        reservation.status = 'cancelled'
        reservation.save()
        return Response({'status': 'reservation cancelled'})
