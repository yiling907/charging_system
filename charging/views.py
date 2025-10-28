from rest_framework import viewsets, permissions, status, filters
from rest_framework.decorators import action
from rest_framework.generics import RetrieveAPIView, UpdateAPIView
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from .models import Station, Charger, ChargingRecord, Reservation
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

class UpdateUserView(UpdateAPIView):
    permission_classes = (IsOperator,)
    @action(detail=True, methods=['patch'],permission_classes=[IsOperator])
    def update_user(self, request, pk=None):
        user = self.get_object()
        charger.status = 'maintenance'
        charger.save()
        return Response({'status': 'maintenance mode activated'})



class StationViewSet(viewsets.ModelViewSet):
    queryset = Station.objects.all()
    serializer_class = StationSerializer
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['name', 'address']
    ordering_fields = ['name', 'created_at']

    def get_permissions(self):
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            return [IsOperator()]
        return [permissions.IsAuthenticated()]


class ChargerViewSet(viewsets.ModelViewSet):
    queryset = Charger.objects.all()
    serializer_class = ChargerSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    filterset_fields = ['station', 'status', 'charger_type']
    search_fields = ['code', 'station__name']

    def get_permissions(self):
        if self.action in ['create', 'update', 'partial_update']:
            return [IsOperator()]
        return [permissions.IsAuthenticated()]

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