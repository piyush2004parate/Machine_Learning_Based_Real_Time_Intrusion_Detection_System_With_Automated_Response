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
        """
        Initialize the KNN Anomaly Detector.
        
        Args:
            model_path: Path to saved KNN model
            features_path: Path to saved features JSON
            scaler_path: Path to saved StandardScaler
        """
        self.model = None
        self.scaler = None
        self.selected_features = None
        self.model_path = model_path
        self.features_path = features_path
        self.scaler_path = scaler_path
        
        # Try to load existing model
        if model_path and features_path and scaler_path:
            self.load_model(model_path, features_path, scaler_path)
    
    @staticmethod
    def build_feature_sets(df):
        """Build feature sets for preprocessing."""
        features = ['dur', 'spkts', 'dpkts', 'sbytes', 'dbytes', 'rate', 'sttl', 'dttl', 'sload',
                    'dload', 'sloss', 'dloss', 'sinpkt', 'dinpkt', 'sjit', 'djit', 'swin', 'stcpb', 'dtcpb',
                    'dwin', 'tcprtt', 'synack', 'ackdat', 'smean', 'dmean', 'trans_depth', 'response_body_len',
                    'ct_srv_src', 'ct_state_ttl', 'ct_dst_ltm', 'ct_src_dport_ltm', 'ct_dst_sport_ltm', 'ct_dst_src_ltm',
                    'is_ftp_login', 'ct_ftp_cmd', 'ct_flw_http_mthd', 'ct_src_ltm', 'ct_srv_dst', 'is_sm_ips_ports']
        
        non_numeric = ['is_sm_ips_ports', 'is_ftp_login']
        numeric_features = list(set(features) - set(non_numeric))
        non_log = ['sttl', 'dttl', 'swin', 'dwin', 'trans_depth', 'ct_state_ttl', 'ct_flw_http_mthd']
        
        return features, numeric_features, non_log, non_numeric
    
    @staticmethod
    def preprocess_data(df):
        """
        Preprocess data with log transformation and feature selection.
        
        Args:
            df: Input dataframe
            
        Returns:
            Tuple of (preprocessed_df, selected_features)
        """
        features, numeric_features, non_log, non_numeric = KNNAnomalyDetector.build_feature_sets(df)
        
        # Log transform
        df_logs = np.log10(df[list(set(numeric_features) - set(non_log))] + 1)
        df_numeric = pd.concat([df_logs, df[non_log]], axis=1)
        df_transformed = pd.concat([df_numeric, df[non_numeric]], axis=1)[features]
        
        # Feature selection using mutual information
        mi_arr = mutual_info_classif(X=df_transformed, y=df['label'], random_state=42)
        df_mi = pd.DataFrame(np.array([df_transformed.columns, mi_arr]).T, columns=['feature', 'mi'])
        df_mi['mi'] = df_mi['mi'].astype(float)
        
        # Select features with MI > 0.2
        mi_cutoff = 0.2
        selected_features = df_mi[df_mi['mi'] > mi_cutoff]['feature'].tolist()
        
        preprocessed = pd.concat([df_transformed[selected_features], df['label']], axis=1)
        return preprocessed, selected_features
    
    def train(self, df, n_neighbors=7):
        """
        Train the KNN model.
        
        Args:
            df: Preprocessed dataframe with 'label' column
            n_neighbors: Number of neighbors for KNN
            
        Returns:
            Dictionary with training metrics
        """
        # Preprocess data
        df_processed, self.selected_features = self.preprocess_data(df)
        
        # Split data
        X = df_processed[self.selected_features]
        y = df_processed['label']
        
        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
        
        # Scale features
        self.scaler = StandardScaler()
        X_train_scaled = self.scaler.fit_transform(X_train)
        X_test_scaled = self.scaler.transform(X_test)
        
        # Train model
        self.model = KNN(n_neighbors=n_neighbors, metric='euclidean', n_jobs=-1)
        self.model.fit(X_train_scaled, y_train)
        
        # Evaluate
        y_pred = self.model.predict(X_test_scaled)
        
        metrics = {
            'accuracy': float(accuracy_score(y_test, y_pred)),
            'precision': float(precision_score(y_test, y_pred)),
            'recall': float(recall_score(y_test, y_pred)),
            'f1': float(f1_score(y_test, y_pred)),
            'confusion_matrix': confusion_matrix(y_test, y_pred).tolist(),
            'selected_features': self.selected_features
        }
        
        return metrics
    
    def predict(self, features_dict):
        """
        Predict whether a packet is normal or anomalous.
        
        Args:
            features_dict: Dictionary with feature names as keys and values
            
        Returns:
            Dictionary with prediction, confidence, and class label
        """
        if self.model is None or self.scaler is None or self.selected_features is None:
            raise ValueError("Model not trained. Train or load a model first.")
        
        # Apply the same preprocessing as training
        feature_vector = self._preprocess_features(features_dict)
        
        # Scale
        feature_vector_scaled = self.scaler.transform(feature_vector)
        
        # Predict
        prediction = self.model.predict(feature_vector_scaled)[0]
        probabilities = self.model.predict_proba(feature_vector_scaled)[0]
        
        return {
            'prediction': int(prediction),
            'label': 'Anomalous' if prediction == 1 else 'Normal',
            'confidence': float(max(probabilities)),
            'probabilities': {
                'normal': float(probabilities[0]),
                'anomalous': float(probabilities[1])
            }
        }
    
    def _preprocess_features(self, features_dict):
        """
        Preprocess individual feature dictionary applying log transformation.
        
        Args:
            features_dict: Raw feature dictionary
            
        Returns:
            Numpy array with log-transformed and selected features
        """
        features, numeric_features, non_log, non_numeric = self.build_feature_sets(pd.DataFrame())
        
        # Create a dataframe with raw values
        raw_df = pd.DataFrame([features_dict])
        
        # Apply log transform to numeric features (same as training)
        log_features = []
        for feat in self.selected_features:
            if feat in numeric_features and feat not in non_log:
                # Apply log transform
                value = features_dict.get(feat, 0)
                transformed = np.log10(value + 1)
                log_features.append(transformed)
            else:
                # Keep as-is
                log_features.append(features_dict.get(feat, 0))
        
        feature_vector = np.array([log_features])
        return feature_vector
    
    def predict_batch(self, df):
        """
        Predict on a batch of records.
        
        Args:
            df: Dataframe with feature columns
            
        Returns:
            Dictionary with predictions and metrics
        """
        if self.model is None or self.scaler is None or self.selected_features is None:
            raise ValueError("Model not trained. Train or load a model first.")
        
        # Extract features
        X = df[self.selected_features]
        X_scaled = self.scaler.transform(X)
        
        # Predict
        predictions = self.model.predict(X_scaled)
        probabilities = self.model.predict_proba(X_scaled)
        
        return {
            'predictions': predictions.tolist(),
            'labels': ['Anomalous' if p == 1 else 'Normal' for p in predictions],
            'confidences': np.max(probabilities, axis=1).tolist()
        }
    
    def save_model(self, model_path, features_path, scaler_path):
        """Save trained model and artifacts."""
        if self.model is None or self.scaler is None:
            raise ValueError("No model to save. Train a model first.")
        
        # Create directories if they don't exist
        Path(model_path).parent.mkdir(parents=True, exist_ok=True)
        Path(features_path).parent.mkdir(parents=True, exist_ok=True)
        Path(scaler_path).parent.mkdir(parents=True, exist_ok=True)
        
        # Save artifacts
        joblib.dump(self.model, model_path)
        joblib.dump(self.scaler, scaler_path)
        
        with open(features_path, 'w') as f:
            json.dump({'selected_features': self.selected_features}, f, indent=2)
    
    def load_model(self, model_path, features_path, scaler_path):
        """Load trained model and artifacts."""
        self.model = joblib.load(model_path)
        self.scaler = joblib.load(scaler_path)
        
        with open(features_path, 'r') as f:
            data = json.load(f)
            self.selected_features = data['selected_features']
