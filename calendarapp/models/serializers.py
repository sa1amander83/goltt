from django.conf import settings
from django.contrib.auth import get_user_model
from rest_framework import serializers

from . import EventMember
from .event import Event, UserEventStats
from .event import Tables


# Use get_user_model() to get the actual User model
User = get_user_model()

class EventSerializer(serializers.ModelSerializer):
    user = serializers.PrimaryKeyRelatedField(queryset=User.objects.all())

    class Meta:
        model = Event
        fields = '__all__'

class EventDetailSerializer(serializers.ModelSerializer):
    user = serializers.StringRelatedField()
    table = serializers.StringRelatedField()

    class Meta:
        model = Event
        fields = ['id', 'user', 'title', 'description', 'start_time', 'end_time', 'total_cost', 'payment_status', 'is_canceled', 'cancel_reason', 'payment_id', 'table', 'total_time', 'is_paid', 'created_at', 'updated_at']

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User  # Now using the actual User model
        fields = ['id', 'email', 'is_active', 'date_joined', 'last_updated']

class TablesSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tables
        fields = ['id', 'number', 'price_per_hour', 'price_per_half_hour', 'table_description']

class UserEventStatsSerializer(serializers.ModelSerializer):
    user = UserSerializer()
    table = TablesSerializer()

    class Meta:
        model = UserEventStats
        fields = ['id', 'user', 'table', 'total_time', 'total_cost', 'total_events']

class EventMemberSerializer(serializers.ModelSerializer):
    event = EventSerializer()
    user = UserSerializer()

    class Meta:
        model = EventMember
        fields = ['id', 'event', 'user']