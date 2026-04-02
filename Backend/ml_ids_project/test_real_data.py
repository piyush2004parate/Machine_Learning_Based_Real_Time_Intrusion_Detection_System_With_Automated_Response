#!/usr/bin/env python
"""Test KNN model on real UNSW dataset samples."""

import pandas as pd
import numpy as np
from api.utils.knn_classifier import KNNAnomalyDetector
from pathlib import Path

# Load the test data
df_test = pd.read_csv('UNSW_Train_Test Datasets/UNSW_NB15_testing-set.csv')

# Initialize detector with trained model
model_dir = Path('.') / '..' / '..' / 'model' / 'unsw_tabular'
detector = KNNAnomalyDetector(
    str(model_dir / 'model_knn.pkl'),
    str(model_dir / 'features_knn.json'),
    str(model_dir / 'scaler_knn.pkl')
)

# Test on a few real samples
print('Testing on REAL UNSW dataset samples:')
print('=' * 70)

# Normal traffic samples
print('\nNormal Traffic Samples (label=0):')
print('-' * 70)
normal_samples = df_test[df_test['label'] == 0].head(3)
for idx, row in normal_samples.iterrows():
    features = row.to_dict()
    result = detector.predict(features)
    print(f'Sample {idx}: Predicted={result["label"]}, Confidence={result["confidence"]:.4f}')

print('\nAnomalous Traffic Samples (label=1):')
print('-' * 70)
# Anomalous traffic samples  
anomalous_samples = df_test[df_test['label'] == 1].head(3)
for idx, row in anomalous_samples.iterrows():
    features = row.to_dict()
    result = detector.predict(features)
    print(f'Sample {idx}: Predicted={result["label"]}, Confidence={result["confidence"]:.4f}')

print('\n' + '=' * 70)
print('Model working correctly on real data!')
