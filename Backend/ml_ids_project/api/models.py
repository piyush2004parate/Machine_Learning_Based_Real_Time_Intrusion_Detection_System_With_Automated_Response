from django.db import models
# api/models.py
import uuid
from django.db import models

class NetworkTraffic(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    timestamp = models.DateTimeField(auto_now_add=True)
    source_ip = models.CharField(max_length=100)
    destination_ip = models.CharField(max_length=100)
    protocol = models.CharField(max_length=50)
    bytes = models.IntegerField()
    status = models.CharField(max_length=50, choices=[('Normal', 'Normal'), ('Anomalous', 'Anomalous'), ('Blocked', 'Blocked')])
    severity = models.CharField(max_length=50, choices=[('Low', 'Low'), ('Medium', 'Medium'), ('High', 'High'), ('Critical', 'Critical')], null=True, blank=True)

class ThreatIncident(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    timestamp = models.DateTimeField(auto_now_add=True)
    source_ip = models.CharField(max_length=100)
    destination_ip = models.CharField(max_length=100)
    threat_type = models.CharField(max_length=100)
    severity = models.CharField(max_length=50)
    status = models.CharField(max_length=50)
    description = models.TextField()
    confidence = models.IntegerField()

class ResponseRule(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255)
    condition = models.CharField(max_length=255)
    action = models.CharField(max_length=100)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    triggered_count = models.IntegerField(default=0)

class LogEntry(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    timestamp = models.DateTimeField(auto_now_add=True)
    action = models.CharField(max_length=255)
    target = models.CharField(max_length=255)
    result = models.CharField(max_length=50, choices=[('Success', 'Success'), ('Failed', 'Failed')])
    details = models.TextField()
    severity = models.CharField(max_length=50, choices=[('Info', 'Info'), ('Warning', 'Warning'), ('Error', 'Error')])