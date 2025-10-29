from rest_framework import serializers
from .models import Station, Charger, ChargingRecord, Reservation, User


class StationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Station
        fields = '__all__'


class ChargerSerializer(serializers.ModelSerializer):
    station_name = serializers.ReadOnlyField(source='station.name')
    address = serializers.ReadOnlyField(source='station.address')
    latitude = serializers.ReadOnlyField(source='station.latitude')
    longitude = serializers.ReadOnlyField(source='station.longitude')

    class Meta:
        model = Charger
        fields = '__all__'


class ChargingRecordSerializer(serializers.ModelSerializer):
    charger_code = serializers.ReadOnlyField(source='charger.code')
    user_username = serializers.ReadOnlyField(source='user.username')

    class Meta:
        model = ChargingRecord
        fields = '__all__'
        read_only_fields = ('duration', 'fee', 'transaction_id', 'pay_status')


class ReservationSerializer(serializers.ModelSerializer):
    charger_code = serializers.ReadOnlyField(source='charger.code')
    user_username = serializers.ReadOnlyField(source='user.username')

    class Meta:
        model = Reservation
        fields = '__all__'
        read_only_fields = ('status',)

    def validate(self, data):
        """Check reservation time conflicts"""
        charger = data['charger']
        start = data['start_time']
        end = data['end_time']

        # Check if charger is available during requested time
        conflicts = Reservation.objects.filter(
            charger=charger,
            status__in=['pending', 'confirmed'],
            start_time__lt=end,
            end_time__gt=start
        ).exists()

        if conflicts:
            raise serializers.ValidationError("Charger is already reserved during this time")
        return data


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = '__all__'
    def validate(self, data):
        email = data['email']


        # Check if charger is available during requested time
        conflicts = User.objects.filter(
            email=email,
        ).exists()

        if conflicts:
            raise serializers.ValidationError("email have already been registered")
        return data

    def create(self, validated_data):
        # 从验证后的数据中提取密码
        password = validated_data.pop('password')
        # 创建用户对象（不含密码）
        user = User(**validated_data)
        # 加密密码并设置
        user.set_password(password)
        # 保存用户（加密后的密码会被存储）
        user.save()
        return user