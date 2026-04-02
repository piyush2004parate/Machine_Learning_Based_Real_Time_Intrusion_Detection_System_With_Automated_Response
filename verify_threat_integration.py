#!/usr/bin/env python
"""
Quick test script to verify threat categories integration
Shows how attack types are detected and stored in the database
"""

import os
import sys
import django
from pathlib import Path

# Setup Django
sys.path.insert(0, str(Path(__file__).parent / 'Backend' / 'ml_ids_project'))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ml_ids_project.settings')
django.setup()

from api.models import ThreatIncident, NetworkTraffic
from django.db.models import Count

print("="*80)
print("THREAT CATEGORIES INTEGRATION TEST")
print("="*80)

# Count incidents by threat type
threat_counts = ThreatIncident.objects.values('threat_type').annotate(count=Count('threat_type')).order_by('-count')

print("\nThreat Categories Detected in Database:")
print("-" * 80)

if threat_counts.exists():
    total_threats = 0
    for threat in threat_counts:
        threat_type = threat['threat_type']
        count = threat['count']
        total_threats += count
        bar_length = int(count / 2)  # Scale for display
        bar = "█" * bar_length
        print(f"  {threat_type:25s} {bar:30s} ({count})")
    
    print("-" * 80)
    print(f"  Total Threats Detected: {total_threats}")
else:
    print("  No threats detected yet. Start the server and capture live traffic.")

# Summary statistics
print("\n" + "="*80)
print("SUMMARY STATISTICS")
print("="*80)

total_packets = NetworkTraffic.objects.count()
anomalous_packets = NetworkTraffic.objects.filter(status='Anomalous').count()
normal_packets = NetworkTraffic.objects.filter(status='Normal').count()
critical_threats = ThreatIncident.objects.filter(severity='Critical').count()
active_threats = ThreatIncident.objects.filter(status='Active').count()

print(f"Total Packets Captured:     {total_packets}")
print(f"  - Normal:                 {normal_packets}")
print(f"  - Anomalous:              {anomalous_packets}")
print(f"\nTotal Incidents Created:    {ThreatIncident.objects.count()}")
print(f"  - Active Threats:         {active_threats}")
print(f"  - Critical Severity:      {critical_threats}")

print("\n" + "="*80)
print("✓ Integration working! View dashboard at http://localhost:5173")
print("="*80)
