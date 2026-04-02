# KNN Integration Quick Setup

## What's Been Done

Your KNN anomaly detection model is now fully integrated with your ML-IDS project! Here's what was created:

### 1. **Backend Integration**
- ✓ `api/utils/knn_classifier.py` - KNN classifier utility module
- ✓ `api/views.py` - Updated with `/api/traffic/detect-anomaly/` endpoint
- ✓ `api/management/commands/train_knn_model.py` - Django training command
- ✓ `knn_anomaly_detection.ipynb` - Complete notebook with model saving

### 2. **Model Artifacts** (after training)
Will be saved to `model/unsw_tabular/`:
- `model_knn.pkl` - Trained KNN classifier
- `scaler_knn.pkl` - Feature scaler
- `features_knn.json` - Selected features list
- `metrics_knn.json` - Model performance metrics

### 3. **Documentation**
- `KNN_INTEGRATION_GUIDE.md` - Complete integration guide with examples

## Quick Start (5 Steps)

### Step 1: Train the Model
Choose one method:

**Option A - Using Jupyter Notebook (Recommended)**
```bash
cd Backend/ml_ids_project
# Open knn_anomaly_detection.ipynb and run all cells
# Model will be automatically saved
```

**Option B - Using Django Command**
```bash
cd Backend/ml_ids_project
python manage.py train_knn_model
```

### Step 2: Verify Model Artifacts
Check that these files exist in `model/unsw_tabular/`:
```bash
ls model/unsw_tabular/
# Should show:
# - model_knn.pkl
# - scaler_knn.pkl
# - features_knn.json
# - metrics_knn.json
```

### Step 3: Start Django Server
```bash
cd Backend/ml_ids_project
python manage.py runserver
```

### Step 4: Test the API
```bash
curl -X POST http://localhost:8000/api/traffic/detect-anomaly/ \
  -H "Content-Type: application/json" \
  -d '{
    "features": {
      "dur": 0.5,
      "spkts": 10,
      "dpkts": 8,
      "sbytes": 1024,
      "dbytes": 512,
      "rate": 5.0,
      "sttl": 64,
      "dttl": 64,
      "sload": 0.01,
      "dload": 0.01,
      "sloss": 0,
      "dloss": 0,
      "sinpkt": 0.1,
      "dinpkt": 0.1,
      "sjit": 0.001,
      "djit": 0.001,
      "swin": 65535,
      "stcpb": 100000,
      "dtcpb": 100000,
      "dwin": 65535,
      "tcprtt": 0.001
    }
  }'
```

### Step 5: Use in Frontend
```javascript
// Frontend code to call the API
const response = await fetch('/api/traffic/detect-anomaly/', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
    'Authorization': 'Bearer YOUR_TOKEN' // if needed
  },
  body: JSON.stringify({
    features: {
      dur: 0.5,
      spkts: 10,
      dpkts: 8,
      // ... all required features
    }
  })
});

const data = await response.json();
console.log(data.prediction.label); // 'Normal' or 'Anomalous'
console.log(data.prediction.confidence); // confidence score
```

## API Endpoint Details

### Endpoint
```
POST /api/traffic/detect-anomaly/
```

### Request Format
```json
{
  "features": {
    "feature_name_1": value1,
    "feature_name_2": value2,
    ...
  }
}
```

### Response Format
```json
{
  "status": "success",
  "prediction": {
    "prediction": 0,              // 0 = Normal, 1 = Anomalous
    "label": "Normal",            // Human readable label
    "confidence": 0.95,           // Confidence score (0-1)
    "probabilities": {
      "normal": 0.95,
      "anomalous": 0.05
    }
  },
  "severity": "Low"               // Low or Critical based on prediction
}
```

## Required Features

The model expects these 21 features (all must be provided):
```
dur, spkts, dpkts, sbytes, dbytes, rate, sttl, dttl, sload, dload,
sloss, dloss, sinpkt, dinpkt, sjit, djit, swin, stcpb, dtcpb, dwin,
tcprtt, synack, ackdat, smean, dmean, trans_depth, response_body_len,
ct_srv_src, ct_state_ttl, ct_dst_ltm, ct_src_dport_ltm, ct_dst_sport_ltm,
ct_dst_src_ltm, is_ftp_login, ct_ftp_cmd, ct_flw_http_mthd, ct_src_ltm,
ct_srv_dst, is_sm_ips_ports
```

## Troubleshooting

### Issue: "Model not found"
**Solution:** Run the training command or notebook to generate model artifacts

### Issue: "Feature 'X' not found"
**Solution:** Ensure all required features are provided in the request

### Issue: "scaler not fitted"
**Solution:** Ensure scaler_knn.pkl exists and is being loaded

## File Structure
```
Project Root/
├── Backend/
│   └── ml_ids_project/
│       ├── api/
│       │   ├── utils/
│       │   │   └── knn_classifier.py ✓ NEW
│       │   ├── management/
│       │   │   └── commands/
│       │   │       └── train_knn_model.py ✓ NEW
│       │   └── views.py ✓ UPDATED
│       ├── knn_anomaly_detection.ipynb ✓ NEW
│       └── manage.py
├── model/
│   └── unsw_tabular/
│       ├── model_knn.pkl ✓ (after training)
│       ├── scaler_knn.pkl ✓ (after training)
│       ├── features_knn.json ✓ (after training)
│       └── metrics_knn.json ✓ (after training)
├── KNN_INTEGRATION_GUIDE.md ✓ NEW
└── KNN_QUICKSTART.md ✓ THIS FILE
```

## Next Steps

1. **Train the Model** - Run notebook or Django command
2. **Test the API** - Use curl or Postman to test endpoints
3. **Frontend Integration** - Call API from React components
4. **Real-time Monitoring** - Process incoming traffic data
5. **Create Alerts** - Trigger alerts when anomalies detected

## Support

For detailed information, see `KNN_INTEGRATION_GUIDE.md`

For issues with the model or integration, check:
- Model training output logs
- API response errors
- Backend console for exceptions

Good luck with your ML-IDS system!
