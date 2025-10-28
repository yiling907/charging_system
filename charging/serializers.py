from rest_framework import serializers
from .models import Station, Charger, ChargingRecord, Reservation, User


class StationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Station
        fields = '__all__'


class ChargerSerializer(serializers.ModelSerializer):
    station_name = serializers.ReadOnlyField(source='station.name')

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