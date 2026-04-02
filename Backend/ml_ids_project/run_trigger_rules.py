#!/usr/bin/env python
"""
Trigger the DB rule engine and action dispatcher using sample rows from the UNSW test set.
This script runs inside the Django project context and calls `save_traffic_and_incidents` directly.
"""
import os
import django
import asyncio
import pandas as pd
from pathlib import Path

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ml_ids_project.settings')
django.setup()

from api.utils.knn_classifier import KNNAnomalyDetector
from api.db_utils import save_traffic_and_incidents

BASE = Path(__file__).parent
DATASET = BASE / 'UNSW_Train_Test Datasets' / 'UNSW_NB15_testing-set.csv'
MODEL_DIR = BASE.parent.parent / 'model' / 'unsw_tabular'
MODEL_PATH = str(MODEL_DIR / 'model_knn.pkl')
FEATURES_PATH = str(MODEL_DIR / 'features_knn.json')
SCALER_PATH = str(MODEL_DIR / 'scaler_knn.pkl')

print("Loading detector and dataset...")
detector = KNNAnomalyDetector(MODEL_PATH, FEATURES_PATH, SCALER_PATH)
df = pd.read_csv(str(DATASET))

# Choose representative attack samples that match configured rules
targets = {
    'DoS': 1,
    'Backdoor': 1,
    'Reconnaissance': 1,
    'Fuzzers': 1,
    'Generic': 1,
}

samples = []
for attack, n in targets.items():
    rows = df[df['attack_cat'].str.contains(attack, na=False)]
    if len(rows) == 0:
        continue
    samples.append(rows.sample(n=min(n, len(rows)), random_state=42).iloc[0])

async def run():
    for idx, row in enumerate(samples):
        features = row.to_dict()
        res = detector.predict(features)
        label = res['label']
        # Map attack_cat -> threat_type used by rules (simple mapping)
        attack_cat = row.get('attack_cat')
        threat_type = None
        if isinstance(attack_cat, str):
            if 'DoS' in attack_cat:
                threat_type = 'DoS/SYN_Flood'
            elif 'Backdoor' in attack_cat:
                threat_type = 'Backdoor/C2'
            elif 'Recon' in attack_cat or 'Scan' in attack_cat:
                threat_type = 'Port_Scanning'
            elif 'Fuzzer' in attack_cat or 'Fuzz' in attack_cat:
                threat_type = 'Fuzzing'
            elif 'Generic' in attack_cat:
                threat_type = 'Generic'
        packet = {
            'timestamp': None,
            'source_ip': f'10.0.0.{100+idx}',
            'destination_ip': '8.8.8.8',
            'protocol': 'TCP',
            'bytes': int(row.get('sbytes', 0) or 0),
            'status': 'Anomalous' if label == 'Anomalous' else 'Normal',
            'severity': 'Critical' if 'DoS' in (attack_cat or '') else 'High',
            'label': '1' if label == 'Anomalous' else '0',
            'rate': float(row.get('rate', 0) or 0),
            'service': row.get('service', ''),
            'state': row.get('state', ''),
            'is_sm_ips_ports': int(row.get('is_sm_ips_ports', 0) or 0),
            'attack_type': threat_type,
        }
        print(f"Submitting packet idx-{idx} (threat_type={threat_type}, status={packet['status']})")
        try:
            payload = await save_traffic_and_incidents(packet)
            print('  -> Incident created:' , payload)
        except Exception as e:
            print('  -> Error creating incident:', e)

if __name__ == '__main__':
    asyncio.run(run())
