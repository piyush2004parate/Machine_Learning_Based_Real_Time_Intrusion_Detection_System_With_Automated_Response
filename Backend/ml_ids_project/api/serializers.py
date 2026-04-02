# api/serializers.py
from rest_framework import serializers
from .models import NetworkTraffic, ThreatIncident, ResponseRule, LogEntry

class NetworkTrafficSerializer(serializers.ModelSerializer):
    class Meta:
        model = NetworkTraffic
        fields = '__all__'

class ThreatIncidentSerializer(serializers.ModelSerializer):
    class Meta:
        model = ThreatIncident
        fields = '__all__'

class ResponseRuleSerializer(serializers.ModelSerializer):
    class Meta:
        model = ResponseRule
        fields = '__all__'

class LogEntrySerializer(serializers.ModelSerializer):
    class Meta:
        model = LogEntry
        fields = '__all__'