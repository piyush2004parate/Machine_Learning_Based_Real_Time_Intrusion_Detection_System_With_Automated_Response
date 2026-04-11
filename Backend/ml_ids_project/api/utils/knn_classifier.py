"""
KNN-based Anomaly Detection Classifier for Network Intrusion Detection System
This module provides functionality to train and use a KNN model for detecting anomalous network packets.
"""

import os
import json
import numpy as np
import pandas as pd
import joblib
from pathlib import Path
from sklearn.preprocessing import StandardScaler
from sklearn.neighbors import KNeighborsClassifier as KNN
from sklearn.feature_selection import mutual_info_classif
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score, confusion_matrix


class KNNAnomalyDetector:
    """KNN-based anomaly detection classifier for network intrusion detection."""
    
    def __init__(self, model_path=None, features_path=None, scaler_path=None):
        self.model = None
        self.scaler = None
        self.selected_features = None
        
        # Load directly
        if model_path and scaler_path:
            self.load_model(model_path, scaler_path)
            
    def load_model(self, model_path, scaler_path):
        import joblib
        model_data = joblib.load(model_path)
        # We handle both dict format (CIC-2018) or direct format
        if isinstance(model_data, dict) and 'model' in model_data:
            self.model = model_data['model']
            self.selected_features = model_data['features']
        else:
            self.model = model_data
            self.selected_features = [] # Fallback
            
        self.scaler = joblib.load(scaler_path)

    def predict(self, features_dict):
        """
        Predict whether a packet is normal or anomalous.
        """
        import numpy as np
        
        if self.model is None or self.scaler is None:
            raise ValueError("Model not trained.")
            
        # Build feature vector according to selected features exactly
        feature_vector = []
        for feat in self.selected_features:
            val = float(features_dict.get(feat, 0.0))
            if np.isnan(val) or np.isinf(val):
                val = 0.0
            feature_vector.append(val)
            
        feature_matrix = np.array([feature_vector])
        scaled = self.scaler.transform(feature_matrix)
        
        prediction = self.model.predict(scaled)[0]
        probabilities = self.model.predict_proba(scaled)[0]
        
        # Determine labels - handling both categorical (DoS, etc) or binary
        if isinstance(prediction, (int, np.integer)) or prediction in [0, 1]:
            # Old binary format
            pred_idx = prediction
            pred_label = 'Anomalous' if prediction == 1 else 'Normal'
        else:
            # New Categorical format (e.g. 'Benign', 'DoS')
            pred_label = str(prediction)
            pred_idx = 0 if pred_label == 'Benign' else 1
            
            # The model predict_proba returns probabilities for classes
            # So if it's Benign, max is normal. If it's DoS, probabilty of normal is low.
            # We map it to binary [normal_prob, anomalous_prob] for backward compatibility with frontend
            idx_benign = list(self.model.classes_).index('Benign') if 'Benign' in self.model.classes_ else 0
            normal_prob = float(probabilities[idx_benign])
            anomalous_prob = 1.0 - normal_prob
            probabilities = [normal_prob, anomalous_prob]
            
        return {
            'prediction': int(pred_idx),
            'label': pred_label, # This passes the exact classification 'DoS', 'Benign', etc.
            'confidence': float(max(probabilities)),
            'probabilities': {
                'normal': float(probabilities[0]),
                'anomalous': float(probabilities[1])
            }
        }
