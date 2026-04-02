#!/usr/bin/env python
"""
Test script for KNN anomaly detection API endpoint
Generates test data from real UNSW NB15 dataset samples
Usage: python test_knn_api.py [--url http://localhost:8000] [--samples N]
"""

import requests
import json
import argparse
import numpy as np
import pandas as pd
from pathlib import Path


def get_sample_features():
    """Generate sample network traffic features from real UNSW dataset."""
    try:
        # Load real UNSW test data
        df = pd.read_csv('UNSW_Train_Test Datasets/UNSW_NB15_testing-set.csv')
        
        # Select diverse samples
        normal_samples = df[df['label'] == 0].sample(n=2, random_state=42)
        anomalous_samples = df[df['label'] == 1].sample(n=2, random_state=42)
        
        samples = []
        
        # Add normal traffic samples
        for idx, row in normal_samples.iterrows():
            samples.append({
                'name': f'Normal Traffic {len([s for s in samples if "Normal" in s["name"]]) + 1}',
                'expected': 'Normal',
                'features': row.to_dict()
            })
        
        # Add anomalous traffic samples
        for idx, row in anomalous_samples.iterrows():
            attack_type = row.get('attack_cat', 'Intrusion')
            samples.append({
                'name': f'Anomalous Pattern ({attack_type})',
                'expected': 'Anomalous',
                'features': row.to_dict()
            })
        
        return samples
    
    except FileNotFoundError:
        print("Warning: UNSW dataset not found. Using synthetic test data.")
        return get_synthetic_samples()


def get_synthetic_samples():
    """Fallback: Generate sample network traffic features for testing.
    
    Based on actual UNSW NB15 training data statistics to ensure realistic test cases.
    """
    samples = [
        {
            'name': 'Normal Traffic 1 (HTTP Request)',
            'expected': 'Normal',
            'features': {
                # Real normal traffic sample from UNSW dataset
                'dur': 0.121, 'dpkts': 4, 'sbytes': 258, 'dbytes': 172, 'rate': 74.0,
                'sttl': 252, 'dttl': 254, 'sload': 0.001, 'dload': 0.001,
                'sinpkt': 0.1, 'dinpkt': 0.15, 'sjit': 30.2, 'tcprtt': 0.0,
                'synack': 0.0, 'ackdat': 0.0, 'smean': 43, 'dmean': 43,
                'ct_state_ttl': 0
            }
        },
        {
            'name': 'Normal Traffic 2 (HTTP Response)',
            'expected': 'Normal',
            'features': {
                # Real normal traffic sample - moderate session
                'dur': 0.650, 'dpkts': 38, 'sbytes': 734, 'dbytes': 42014, 'rate': 78.5,
                'sttl': 62, 'dttl': 252, 'sload': 0.01, 'dload': 0.08,
                'sinpkt': 0.05, 'dinpkt': 0.06, 'sjit': 61.4, 'tcprtt': 0.0,
                'synack': 0.0, 'ackdat': 0.0, 'smean': 52, 'dmean': 1106,
                'ct_state_ttl': 1
            }
        },
        {
            'name': 'Suspicious Traffic (Unusual Jitter)',
            'expected': 'Normal/Anomalous',
            'features': {
                # Normal rate but high jitter indicating packet loss or latency issues
                'dur': 1.623, 'dpkts': 16, 'sbytes': 364, 'dbytes': 13186, 'rate': 14.2,
                'sttl': 62, 'dttl': 252, 'sload': 0.002, 'dload': 0.015,
                'sinpkt': 0.1, 'dinpkt': 0.12, 'sjit': 17179.6, 'tcprtt': 0.111,
                'synack': 0.061, 'ackdat': 0.050, 'smean': 46, 'dmean': 824,
                'ct_state_ttl': 1
            }
        },
        {
            'name': 'Anomalous Pattern (DoS - High Rate)',
            'expected': 'Anomalous',
            'features': {
                # Very short duration with extreme packet count - classic DoS pattern
                'dur': 0.001, 'dpkts': 1000, 'sbytes': 500000, 'dbytes': 450000, 'rate': 500000.0,
                'sttl': 32, 'dttl': 32, 'sload': 5000.0, 'dload': 4500.0,
                'sinpkt': 0.0001, 'dinpkt': 0.00011, 'sjit': 1000.0, 'tcprtt': 0.5,
                'synack': 1.0, 'ackdat': 2.0, 'smean': 500, 'dmean': 450,
                'ct_state_ttl': 50
            }
        }
    ]
    return samples


def test_api(base_url, test_samples):
    """Test the anomaly detection API."""
    endpoint = f"{base_url}/api/traffic/detect-anomaly/"
    
    print("="*70)
    print("KNN ANOMALY DETECTION API TEST")
    print("="*70)
    print(f"\nEndpoint: {endpoint}\n")
    
    results = []
    
    for sample in test_samples:
        print(f"\nTesting: {sample['name']}")
        print(f"Expected: {sample.get('expected', 'Unknown')}")
        print("-" * 70)
        
        try:
            # Make request
            response = requests.post(
                endpoint,
                json={'features': sample['features']},
                timeout=10
            )
            
            # Check status
            if response.status_code == 200:
                data = response.json()
                prediction = data.get('prediction', {})
                
                print(f"Status: [OK] Success")
                print(f"Label: {prediction.get('label', 'Unknown')}")
                print(f"Confidence: {prediction.get('confidence', 0):.4f}")
                print(f"Probability (Normal): {prediction.get('probabilities', {}).get('normal', 0):.4f}")
                print(f"Probability (Anomalous): {prediction.get('probabilities', {}).get('anomalous', 0):.4f}")
                print(f"Severity: {data.get('severity', 'Unknown')}")
                
                results.append({
                    'name': sample['name'],
                    'status': 'success',
                    'expected': sample.get('expected'),
                    'prediction': prediction.get('label'),
                    'confidence': prediction.get('confidence')
                })
            
            elif response.status_code == 404:
                print(f"Status: [FAIL] Model Not Found")
                print(f"Message: {response.json().get('error', 'Unknown error')}")
                results.append({
                    'name': sample['name'],
                    'status': 'error',
                    'error': 'Model not found'
                })
            
            else:
                print(f"Status: [FAIL] Error ({response.status_code})")
                print(f"Response: {response.text}")
                results.append({
                    'name': sample['name'],
                    'status': 'error',
                    'error': f'HTTP {response.status_code}'
                })
        
        except requests.exceptions.ConnectionError:
            print(f"Status: [FAIL] Connection Error")
            print(f"Cannot connect to {base_url}")
            results.append({
                'name': sample['name'],
                'status': 'error',
                'error': 'Connection error'
            })
        
        except Exception as e:
            print(f"Status: [FAIL] Exception")
            print(f"Error: {str(e)}")
            results.append({
                'name': sample['name'],
                'status': 'error',
                'error': str(e)
            })
    
    # Summary
    print("\n" + "="*70)
    print("TEST SUMMARY")
    print("="*70)
    
    successful = sum(1 for r in results if r['status'] == 'success')
    total = len(results)
    
    print(f"\nTotal Tests: {total}")
    print(f"Successful: {successful}")
    print(f"Failed: {total - successful}")
    
    print("\nDetailed Results:")
    for result in results:
        status_icon = "[OK]" if result['status'] == 'success' else "[FAIL]"
        print(f"{status_icon} {result['name']}: {result['status']}")
        if result['status'] == 'success':
            expected = result.get('expected', 'Unknown')
            actual = result['prediction']
            match = "[OK]" if expected.lower() == actual.lower() or ("normal/anomalous" in expected.lower()) else "[FAIL]"
            print(f"   Expected: {expected} | Actual: {actual} {match}")
            print(f"   Confidence: {result['confidence']:.4f}")
        else:
            print(f"   Error: {result.get('error', 'Unknown')}")
    
    print("\n" + "="*70)
    
    return successful == total


def main():
    parser = argparse.ArgumentParser(
        description='Test KNN anomaly detection API endpoint'
    )
    parser.add_argument(
        '--url',
        type=str,
        default='http://localhost:8000',
        help='Base URL of the Django server (default: http://localhost:8000)'
    )
    parser.add_argument(
        '--samples',
        type=int,
        default=4,
        help='Number of test samples to use (1-4, default: 4)'
    )
    
    args = parser.parse_args()
    
    # Get test samples
    all_samples = get_sample_features()
    test_samples = all_samples[:min(args.samples, len(all_samples))]
    
    # Run tests
    success = test_api(args.url, test_samples)
    
    exit(0 if success else 1)


if __name__ == '__main__':
    main()
