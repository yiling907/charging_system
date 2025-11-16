from rest_framework import serializers
from .models import Station, Charger, ChargingRecord, User


class ChargerSerializer(serializers.ModelSerializer):
    station_info = serializers.SerializerMethodField()

    class Meta:
        model = Charger
        fields = '__all__'

    def get_station_info(self, obj):
        station=obj.station
        if not station:
            return None
        return {
            "station_name": station.name,
            "active_charger_count": station.chargers.filter(status='idle').count(),
            "charger_count": station.chargers.count(),
        }


class StationSerializer(serializers.ModelSerializer):
    chargers = ChargerSerializer(source='filtered_chargers', many=True, read_only=True)
    avaliable_count = serializers.SerializerMethodField()
    count = serializers.SerializerMethodField()
    chargers_type = serializers.SerializerMethodField()

    class Meta:
        model = Station
        fields = '__all__'

    def get_avaliable_count(self, obj):
        return len(obj.filtered_chargers)


    def get_count(self, obj):
        return obj.chargers.count()

    def get_chargers_type(self, obj):
        types = {charger.charger_type for charger in obj.filtered_chargers}
        return list(types)


class ChargingRecordSerializer(serializers.ModelSerializer):
    charger_code = serializers.ReadOnlyField(source='charger.code')
    status = serializers.ReadOnlyField(source='charger.status')
    user_username = serializers.ReadOnlyField(source='user.username')

    class Meta:
        model = ChargingRecord
        fields = '__all__'
        read_only_fields = ('duration', 'transaction_id', 'pay_status')

    def validate_charger(self, charger):
        """验证充电器状态是否为idle"""
        if charger.status != 'idle':
            raise serializers.ValidationError("charger status must be idle")
        return charger  # 验证通过，返回充电器对象



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
