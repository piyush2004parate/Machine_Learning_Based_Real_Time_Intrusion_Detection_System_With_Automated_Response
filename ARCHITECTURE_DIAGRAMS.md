# KNN Model Integration Architecture

## System Flow Diagram

```
┌──────────────────────────────────────────────────────────────────┐
│                         Frontend (React/TS)                      │
│  ┌────────────────────────────────────────────────────────────┐  │
│  │  Dashboard │ Incidents │ Live Traffic │ Logs │ Settings    │  │
│  └────────────────────────────────────────────────────────────┘  │
│                              │                                    │
│                              ↓ HTTP POST                          │
└──────────────────────────────────────────────────────────────────┘
                               │
                               ↓
┌──────────────────────────────────────────────────────────────────┐
│                  Django REST Framework API                       │
│  ┌────────────────────────────────────────────────────────────┐  │
│  │  POST /api/traffic/detect-anomaly/                         │  │
│  │  {                                                          │  │
│  │    "features": {                                           │  │
│  │      "dur": 0.5,                                          │  │
│  │      "spkts": 10,                                         │  │
│  │      "dpkts": 8,                                          │  │
│  │      ... (38 total features)                              │  │
│  │    }                                                       │  │
│  │  }                                                         │  │
│  └────────────────────────────────────────────────────────────┘  │
│                              │                                    │
│                              ↓                                    │
│  ┌────────────────────────────────────────────────────────────┐  │
│  │  NetworkTrafficViewSet.detect_anomaly()                    │  │
│  │  ├─ Load KNN model artifacts                             │  │
│  │  ├─ Initialize KNNAnomalyDetector                        │  │
│  │  └─ Call detector.predict(features)                      │  │
│  └────────────────────────────────────────────────────────────┘  │
│                              │                                    │
│                              ↓                                    │
└──────────────────────────────────────────────────────────────────┘
                               │
┌──────────────────────────────────────────────────────────────────┐
│           ML Models Layer (api/utils/knn_classifier.py)          │
│                                                                  │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  KNNAnomalyDetector                                      │  │
│  │                                                          │  │
│  │  1. Load Model Artifacts                               │  │
│  │     ├─ model_knn.pkl (KNN classifier)                  │  │
│  │     ├─ scaler_knn.pkl (StandardScaler)                 │  │
│  │     └─ features_knn.json (selected features)           │  │
│  │                                                          │  │
│  │  2. Preprocess Input Features                          │  │
│  │     ├─ Extract selected features only                  │  │
│  │     ├─ Apply log transformation                        │  │
│  │     └─ Scale using StandardScaler                      │  │
│  │                                                          │  │
│  │  3. Generate Prediction                                │  │
│  │     ├─ KNN.predict() → class label (0/1)              │  │
│  │     ├─ KNN.predict_proba() → confidence scores        │  │
│  │     └─ Package result with metadata                    │  │
│  │                                                          │  │
│  │  4. Return Prediction                                  │  │
│  │     {                                                   │  │
│  │       "prediction": 0,                                 │  │
│  │       "label": "Normal",                               │  │
│  │       "confidence": 0.95,                              │  │
│  │       "probabilities": {...}                           │  │
│  │     }                                                   │  │
│  └──────────────────────────────────────────────────────────┘  │
│                              │                                    │
│                              ↓                                    │
└──────────────────────────────────────────────────────────────────┘
                               │
                               ↓
┌──────────────────────────────────────────────────────────────────┐
│                    Response to Frontend                          │
│  ┌────────────────────────────────────────────────────────────┐  │
│  │  {                                                         │  │
│  │    "status": "success",                                   │  │
│  │    "prediction": {                                        │  │
│  │      "prediction": 0,                                    │  │
│  │      "label": "Normal",                                  │  │
│  │      "confidence": 0.95,                                 │  │
│  │      "probabilities": {                                  │  │
│  │        "normal": 0.95,                                   │  │
│  │        "anomalous": 0.05                                 │  │
│  │      }                                                    │  │
│  │    },                                                     │  │
│  │    "severity": "Low"                                     │  │
│  │  }                                                         │  │
│  └────────────────────────────────────────────────────────────┘  │
│                              │                                    │
│                              ↓                                    │
└──────────────────────────────────────────────────────────────────┘
                               │
                               ↓
                      Store in Database?
                               │
                    ┌──────────┴──────────┐
                    ↓                     ↓
            Normal Traffic           Anomalous Traffic
                    │                     │
                    ↓                     ↓
         NetworkTraffic Record    ThreatIncident Record
         status="Normal"          status="Anomalous"
         severity="Low"           severity="Critical"
```

## Data Flow for Model Training

```
┌──────────────────────────────────────────────────────────────────┐
│                    UNSW NB15 Dataset                             │
│  (UNSW_Train_Test Datasets/UNSW_NB15_training-set.csv)          │
│                                                                  │
│  - 175,341 records                                               │
│  - 38 network features                                           │
│  - Binary labels (Normal/Anomalous)                              │
└──────────────────────────────────────────┬───────────────────────┘
                                           │
                                           ↓
                    ┌─────────────────────────────────────┐
                    │  Data Preprocessing                 │
                    │  (preprocessing.ipynb)              │
                    │                                     │
                    │  1. Load raw UNSW data              │
                    │  2. Log-transform numeric features  │
                    │  3. Calculate mutual information    │
                    │  4. Select features (MI > 0.2)      │
                    │  5. Output: 21 selected features    │
                    └──────────┬──────────────────────────┘
                               │
                               ↓
                    ┌─────────────────────────────────────┐
                    │  Model Training                     │
                    │  (knn_anomaly_detection.ipynb)      │
                    │                                     │
                    │  1. Load preprocessed data          │
                    │  2. Split: 80% train, 20% test     │
                    │  3. Standardize features            │
                    │  4. Train KNN (k=7)                 │
                    │  5. Evaluate metrics                │
                    │  6. Generate visualizations         │
                    └──────────┬──────────────────────────┘
                               │
                               ↓
                    ┌─────────────────────────────────────┐
                    │  Model Serialization                │
                    │  Save Artifacts                     │
                    │                                     │
                    │  → model_knn.pkl                    │
                    │  → scaler_knn.pkl                   │
                    │  → features_knn.json                │
                    │  → metrics_knn.json                 │
                    └──────────┬──────────────────────────┘
                               │
                               ↓
                    ┌─────────────────────────────────────┐
                    │  model/unsw_tabular/                │
                    │                                     │
                    │  Ready for production use           │
                    └─────────────────────────────────────┘
```

## Component Interaction Diagram

```
┌─────────────────────────────────────────────────────────┐
│                                                         │
│  Frontend React Components                             │
│  ┌───────────────────────────────────────────────────┐ │
│  │ Dashboard.tsx                                     │ │
│  │   ├─ DetectAnomalyComponent                      │ │
│  │   │   ├─ Input feature data                      │ │
│  │   │   └─ Call API endpoint                       │ │
│  │   └─ DisplayPredictionComponent                  │ │
│  │       └─ Show anomaly result                     │ │
│  │                                                   │ │
│  │ Incidents.tsx                                     │ │
│  │   ├─ Fetch anomalous incidents                  │ │
│  │   └─ Display threat details                      │ │
│  │                                                   │ │
│  │ LiveTraffic.tsx                                   │ │
│  │   ├─ Real-time packet monitoring                │ │
│  │   └─ Run KNN detection on live data             │ │
│  └───────────────────────────────────────────────────┘ │
│                           │                            │
│                           ↓ useToast, API calls        │
└─────────────────────────────────────────────────────────┘
                           │
            ┌──────────────┴──────────────┐
            ↓                             ↓
    API Service Layer            Django Views Layer
    (Frontend)                    (Backend)
    
    ┌────────────────┐           ┌────────────────────┐
    │ api.ts         │           │ api/views.py       │
    │                │ ────POST→ │                    │
    │ detectAnomaly()│           │ detect_anomaly()   │
    └────────────────┘           └──────┬─────────────┘
                                        │
                                        ↓
                            ┌───────────────────────┐
                            │ KNNAnomalyDetector    │
                            │                       │
                            │ - Load artifacts      │
                            │ - Preprocess input    │
                            │ - Make prediction     │
                            │ - Return result       │
                            └──────┬────────────────┘
                                   │
                    ┌──────────────┴──────────────┐
                    ↓                             ↓
            ┌─────────────────┐          ┌──────────────┐
            │ Model Files     │          │ Database     │
            │                 │          │              │
            │ - model_knn.pkl │          │ NetworkTraff │
            │ - scaler_knn.pkl│  ←────→  │ ThreatIncide │
            │ - features_knn  │          │ ResponseRule │
            │ - metrics_knn   │          │ LogEntry     │
            └─────────────────┘          └──────────────┘
```

## Training Pipeline (Django Command)

```
Command: python manage.py train_knn_model

    ↓
    
┌─────────────────────────────────────────────────┐
│ Django Management Command Handler               │
│                                                 │
│ train_knn_model.py                              │
│ ├─ Parse arguments                             │
│ ├─ Load UNSW dataset                           │
│ ├─ Create KNNAnomalyDetector                   │
│ └─ Call detector.train()                       │
└────────────────┬────────────────────────────────┘
                 │
                 ↓
┌─────────────────────────────────────────────────┐
│ KNNAnomalyDetector.train()                      │
│                                                 │
│ 1. preprocess_data()                           │
│    ├─ Log transform numeric features           │
│    ├─ Calculate MI scores                      │
│    └─ Select features (MI > 0.2)               │
│                                                 │
│ 2. Split data (80/20)                          │
│                                                 │
│ 3. StandardScaler.fit_transform()              │
│                                                 │
│ 4. KNN.fit()                                   │
│                                                 │
│ 5. KNN.predict() on test set                   │
│                                                 │
│ 6. Calculate metrics                           │
│    ├─ Accuracy                                 │
│    ├─ Precision                                │
│    ├─ Recall                                   │
│    └─ F1-Score                                 │
│                                                 │
│ 7. Return metrics dict                         │
└────────────────┬────────────────────────────────┘
                 │
                 ↓
┌─────────────────────────────────────────────────┐
│ save_model()                                    │
│                                                 │
│ joblib.dump(model, 'model_knn.pkl')            │
│ joblib.dump(scaler, 'scaler_knn.pkl')          │
│ json.dump(features, 'features_knn.json')       │
│ json.dump(metrics, 'metrics_knn.json')         │
└────────────────┬────────────────────────────────┘
                 │
                 ↓
┌─────────────────────────────────────────────────┐
│ Model Artifacts Ready                           │
│                                                 │
│ model/unsw_tabular/                            │
│ ├─ model_knn.pkl                               │
│ ├─ scaler_knn.pkl                              │
│ ├─ features_knn.json                           │
│ └─ metrics_knn.json                            │
└─────────────────────────────────────────────────┘
```

## Error Handling Flow

```
Prediction Request
        │
        ↓
┌───────────────────┐
│ Check Model Files │
└────────┬──────────┘
         │
    ┌────┴────┐
    │ Missing │  Yes → Return 404 Error
    │ Error?  │        "Model not found"
    └────┬────┘
    No   │
         ↓
┌───────────────────┐
│ Load Artifacts    │
└────────┬──────────┘
         │
    ┌────┴────────────┐
    │ Load Error?     │  Yes → Return 500 Error
    └────┬────────────┘
    No   │
         ↓
┌───────────────────┐
│ Extract Features  │
└────────┬──────────┘
         │
    ┌────┴──────────┐
    │ Missing       │  Yes → Return 400 Error
    │ Feature?      │        "Feature not found"
    └────┬──────────┘
    No   │
         ↓
┌───────────────────┐
│ Scale Features    │
└────────┬──────────┘
         │
    ┌────┴──────────┐
    │ Scaling       │  Yes → Return 500 Error
    │ Error?        │        "Error during prediction"
    └────┬──────────┘
    No   │
         ↓
┌───────────────────┐
│ Make Prediction   │
└────────┬──────────┘
         │
         ↓
┌───────────────────┐
│ Return Result     │  Success 200
│ with Confidence   │  {prediction, confidence, ...}
└───────────────────┘
```

---

This architecture ensures:
- **Modularity:** Each component has clear responsibility
- **Scalability:** Can handle batch predictions
- **Robustness:** Comprehensive error handling
- **Integration:** Seamless Django-ML integration
