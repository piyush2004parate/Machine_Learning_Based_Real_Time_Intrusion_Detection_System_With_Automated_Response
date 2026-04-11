# api/views.py
import os
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.db.models import Q
from django.conf import settings
from .models import NetworkTraffic, ThreatIncident, ResponseRule, LogEntry
from .serializers import (
    NetworkTrafficSerializer,
    ThreatIncidentSerializer,
    ResponseRuleSerializer,
    LogEntrySerializer,
)
from .actions import unblock_ip
from .utils.knn_classifier import KNNAnomalyDetector

class NetworkTrafficViewSet(viewsets.ModelViewSet):
    queryset = NetworkTraffic.objects.all()
    serializer_class = NetworkTrafficSerializer

    @action(detail=False, methods=["get"], url_path="search")
    def search(self, request):
        q = request.query_params.get("q", "").strip()
        qs = self.get_queryset()
        if q:
            qs = qs.filter(
                Q(source_ip__icontains=q)
                | Q(destination_ip__icontains=q)
                | Q(protocol__icontains=q)
                | Q(status__icontains=q)
                | Q(severity__icontains=q)
            )
        qs = qs.order_by("-timestamp")[:500]
        serializer = self.get_serializer(qs, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=["delete"], url_path="clear", authentication_classes=[], permission_classes=[])
    def clear(self, request):
        deleted_count, _ = NetworkTraffic.objects.all().delete()
        return Response({"deleted": deleted_count})
    
    @action(detail=False, methods=["post"], url_path="detect-anomaly")
    def detect_anomaly(self, request):
        """Detect if a packet/traffic is anomalous using KNN model."""
        try:
            # Initialize KNN detector with saved model
            model_dir = os.path.join(settings.BASE_DIR, '..', '..')
            model_path = os.path.join(model_dir, 'knn_model_cic2018.pkl')
            scaler_path = os.path.join(model_dir, 'scaler_cic2018.pkl')
            
            # Check if model exists
            if not os.path.exists(model_path):
                return Response(
                    {'error': 'Model not found. Please train the model first.'},
                    status=status.HTTP_404_NOT_FOUND
                )
            
            detector = KNNAnomalyDetector(model_path, scaler_path=scaler_path)
            
            # Get features from request
            features = request.data.get('features', {})
            
            # Predict
            result = detector.predict(features)
            
            return Response({
                'status': 'success',
                'prediction': result,
                'severity': 'Critical' if result['label'] == 'Anomalous' else 'Low'
            })
        
        except FileNotFoundError as e:
            return Response(
                {'error': f'Model file not found: {str(e)}'},
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            return Response(
                {'error': f'Error during prediction: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

class ThreatIncidentViewSet(viewsets.ModelViewSet):
    queryset = ThreatIncident.objects.all()
    serializer_class = ThreatIncidentSerializer

    @action(detail=True, methods=["post"], url_path="unblock")
    def unblock(self, request, pk=None):
        incident = self.get_object()
        ip = incident.source_ip
        if not ip:
            return Response({"error": "No source IP found for this incident"}, status=status.HTTP_400_BAD_REQUEST)
        
        result = unblock_ip(ip)
        if result.get("result") == "ok":
            incident.status = "Resolved"
            incident.save()
            return Response({"status": "success", "message": f"IP {ip} unblocked", "details": result})
        else:
            return Response({"status": "error", "message": f"Failed to unblock {ip}", "details": result}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class ResponseRuleViewSet(viewsets.ModelViewSet):
    queryset = ResponseRule.objects.all()
    serializer_class = ResponseRuleSerializer

class LogEntryViewSet(viewsets.ModelViewSet):
    queryset = LogEntry.objects.all()
    serializer_class = LogEntrySerializer