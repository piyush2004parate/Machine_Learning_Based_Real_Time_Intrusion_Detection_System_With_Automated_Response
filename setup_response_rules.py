#!/usr/bin/env python
"""
Auto Response Module - Example Rules Setup Script

This script demonstrates how to create and configure response rules
for different attack scenarios.

Usage:
    python setup_response_rules.py
"""

import os
import sys
import django
from pathlib import Path

# Setup Django
sys.path.insert(0, str(Path(__file__).parent / 'Backend' / 'ml_ids_project'))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ml_ids_project.settings')
django.setup()

from api.models import ResponseRule

def create_rules():
    """Create example response rules for different attack types."""
    
    rules = [
        {
            'name': 'Block Critical DoS Attacks',
            'condition': 'severity=Critical, threat_type=DoS/SYN_Flood',
            'action': 'Block IP',
            'is_active': True,
            'description': 'Automatically blocks source IP for critical DoS attacks'
        },
        {
            'name': 'Alert on Backdoor Detection',
            'condition': 'threat_type=Backdoor/C2',
            'action': 'Alert Admin',
            'is_active': True,
            'description': 'Sends alert when backdoor/C2 traffic detected'
        },
        {
            'name': 'Quarantine High Severity Threats',
            'condition': 'severity=High',
            'action': 'Quarantine',
            'is_active': True,
            'description': 'Quarantines any high severity threat traffic'
        },
        {
            'name': 'Block Reconnaissance Attempts',
            'condition': 'threat_type=Port_Scanning',
            'action': 'Block IP',
            'is_active': True,
            'description': 'Blocks port scanning/reconnaissance activities'
        },
        {
            'name': 'Alert on Exploits',
            'condition': 'threat_type=Exploit',
            'action': 'Alert Admin',
            'is_active': False,  # Start disabled
            'description': 'Alerts on any exploitation attempts'
        },
        {
            'name': 'Isolate Fuzzing Attacks',
            'condition': 'threat_type=Fuzzing',
            'action': 'Isolate Device',
            'is_active': True,
            'description': 'Isolates devices performing fuzzing attacks'
        },
        {
            'name': 'Block HTTP Anomalies',
            'condition': 'threat_type=HTTP_Anomaly',
            'action': 'Block IP',
            'is_active': True,
            'description': 'Blocks sources of HTTP anomalies'
        },
        {
            'name': 'Alert on IP Spoofing',
            'condition': 'threat_type=IP/Port Spoofing',
            'action': 'Alert Admin',
            'is_active': True,
            'description': 'Alerts on IP/port spoofing attempts'
        },
        {
            'name': 'Block DNS Anomalies',
            'condition': 'threat_type=DNS_Anomaly',
            'action': 'Block IP',
            'is_active': True,
            'description': 'Blocks DNS anomaly sources'
        },
        {
            'name': 'Critical Shellcode Execution',
            'condition': 'threat_type=Shellcode_Execution',
            'action': 'Isolate Device',
            'is_active': True,
            'description': 'Isolates devices attempting shellcode execution'
        },
    ]
    
    print("="*80)
    print("RESPONSE RULES SETUP")
    print("="*80)
    
    created_count = 0
    skipped_count = 0
    
    for rule_data in rules:
        rule_name = rule_data['name']
        
        # Check if rule already exists
        existing = ResponseRule.objects.filter(name=rule_name).first()
        if existing:
            print(f"\n⊘ SKIPPED: '{rule_name}' (already exists)")
            skipped_count += 1
            continue
        
        # Create rule
        rule = ResponseRule.objects.create(
            name=rule_data['name'],
            condition=rule_data['condition'],
            action=rule_data['action'],
            is_active=rule_data['is_active'],
        )
        
        status = "✓ ACTIVE" if rule_data['is_active'] else "⊘ INACTIVE"
        print(f"\n✓ CREATED: '{rule_name}'")
        print(f"  Condition: {rule_data['condition']}")
        print(f"  Action:    {rule_data['action']}")
        print(f"  Status:    {status}")
        print(f"  Info:      {rule_data['description']}")
        
        created_count += 1
    
    print("\n" + "="*80)
    print(f"SUMMARY: {created_count} rules created, {skipped_count} skipped")
    print("="*80)
    
    return created_count, skipped_count

def list_rules():
    """List all configured rules."""
    
    print("\n" + "="*80)
    print("CONFIGURED RESPONSE RULES")
    print("="*80)
    
    rules = ResponseRule.objects.all().order_by('-created_at')
    
    if not rules.exists():
        print("\nNo rules configured yet. Run setup to create example rules.")
        return
    
    for rule in rules:
        status = "🟢 ACTIVE" if rule.is_active else "🔴 INACTIVE"
        print(f"\n{status} {rule.name}")
        print(f"   Condition: {rule.condition}")
        print(f"   Action:    {rule.action}")
        print(f"   Triggered: {rule.triggered_count} times")
        print(f"   Created:   {rule.created_at.strftime('%Y-%m-%d %H:%M:%S')}")
    
    print("\n" + "="*80)

def example_usage():
    """Show example usage of the rules."""
    
    print("\n" + "="*80)
    print("EXAMPLE USAGE")
    print("="*80)
    
    print("""
When a threat is detected, the system:

1. Creates a ThreatIncident with:
   {
     "source_ip": "192.168.1.100",
     "destination_ip": "8.8.8.8",
     "threat_type": "DoS/SYN_Flood",
     "severity": "Critical",
     "status": "Active",
     "confidence": 95
   }

2. Evaluates all ACTIVE rules:
   
   Rule: "Block Critical DoS Attacks"
   Condition: severity=Critical, threat_type=DoS/SYN_Flood
   
   Matching process:
   - severity = "Critical"? ✓ YES
   - threat_type = "DoS/SYN_Flood"? ✓ YES
   → RULE MATCHES! 🎯

3. Executes the rule:
   - Action: "Block IP"
   - Target: source_ip = "192.168.1.100"
   - Creates LogEntry with action details
   - Increments triggered_count

4. Frontend/Admin notifications:
   - Incident appears in dashboard
   - Response rule trigger logged
   - Action count updated for the rule

Example Timeline:
┌──────────────────────────────────────────────────┐
│ 10:15:30 - Packet detected from 192.168.1.100    │
│ 10:15:31 - KNN model predicts Anomalous          │
│ 10:15:31 - Classified as DoS/SYN_Flood           │
│ 10:15:31 - ThreatIncident created (severity=Crit)│
│ 10:15:31 - Rule "Block Critical DoS" matches ✓   │
│ 10:15:31 - Action "Block IP" logged              │
│ 10:15:32 - Dashboard updated                     │
│ 10:15:32 - Admin notification sent               │
└──────────────────────────────────────────────────┘

Total latency: ~2 seconds end-to-end
    """)

if __name__ == '__main__':
    print("\n" + "="*80)
    print("ML-IDS AUTO RESPONSE MODULE - SETUP WIZARD")
    print("="*80)
    
    # Create rules
    created, skipped = create_rules()
    
    # List all rules
    list_rules()
    
    # Show example
    example_usage()
    
    print("\n" + "="*80)
    print("NEXT STEPS")
    print("="*80)
    print("""
1. View rules in admin panel:
   http://localhost:8000/admin/api/responserule/

2. View response rules UI:
   http://localhost:5173/auto-response

3. Manage rules via API:
   GET    /api/rules/              - List all rules
   POST   /api/rules/              - Create new rule
   PATCH  /api/rules/{id}/         - Update rule
   DELETE /api/rules/{id}/         - Delete rule

4. View action logs:
   http://localhost:8000/admin/api/logentry/

5. Monitor triggered rules:
   - Check dashboard for incidents
   - View rule statistics in admin
   - Review log entries for audit trail

6. Customize rules:
   - Edit conditions and actions in admin
   - Enable/disable rules as needed
   - Add IP whitelist for trusted sources
    """)
    print("="*80 + "\n")
