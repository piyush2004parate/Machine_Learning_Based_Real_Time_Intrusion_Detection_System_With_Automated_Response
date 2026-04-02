import sys
import os
import warnings

# Suppress sklearn warnings
warnings.filterwarnings('ignore')

# Adjust path to the project
sys.path.append(r'c:\Users\sanja\OneDrive\Desktop\Machine_Learning_Based_RealTime_Intrusion_Detection_System-main\Backend\ml_ids_project')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ml_ids_project.settings')

import django
django.setup()

from api.utils.knn_classifier import KNNAnomalyDetector

model_dir = r'c:\Users\sanja\OneDrive\Desktop\Machine_Learning_Based_RealTime_Intrusion_Detection_System-main\model\unsw_tabular'
model_path = os.path.join(model_dir, 'model_knn.pkl')
features_path = os.path.join(model_dir, 'features_knn.json')
scaler_path = os.path.join(model_dir, 'scaler_knn.pkl')

detector = KNNAnomalyDetector(model_path, features_path, scaler_path)

print("Selected Model Features:", detector.selected_features)

# Live SYN packet values (attack from 192.168.0.108 to 192.168.0.111)
features_dict = {
  "dur": 0,
  "dpkts": 0,
  "sbytes": 168,
  "dbytes": 0,
  "rate": 0,
  "sttl": 64,
  "dttl": 0,
  "sload": 0,
  "dload": 0,
  "sinpkt": 0,
  "dinpkt": 0,
  "sjit": 0,
  "tcprtt": 0,
  "synack": 0,
  "ackdat": 0,
  "smean": 168,
  "dmean": 0,
  "ct_state_ttl": 44
}

res = detector.predict(features_dict)
print("Prediction Result:", res)

# Let's inspect what happens to the feature vector
feature_vector = detector._preprocess_features(features_dict)
print("Raw feature vector length:", len(feature_vector[0]))

scaled_feature_vector = detector.scaler.transform(feature_vector)
print("Scaled feature vector:", scaled_feature_vector[0][:5], "...") # Just a sample
