"""Quick local harness to exercise the KNNAnomalyDetector and print audit info.

Run this from the Backend folder (where this file lives):

    python quick_model_check.py

It will instantiate the detector (which loads the saved KNN model) and run a few
sample feature inferences.
"""
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
# Ensure ml_ids_project is on sys.path
sys.path.insert(0, str(HERE / "ml_ids_project"))

try:
    from api.utils.knn_classifier import KNNAnomalyDetector
except Exception as e:
    print("Failed to import KNNAnomalyDetector:", e)
    raise


def main():
    # Load model from saved artifacts
    model_dir = HERE.parent / 'model' / 'unsw_tabular'
    model_path = str(model_dir / 'model_knn.pkl')
    features_path = str(model_dir / 'features_knn.json')
    scaler_path = str(model_dir / 'scaler_knn.pkl')
    
    det = KNNAnomalyDetector(model_path, features_path, scaler_path)

    # Create a few synthetic feature dicts (based on UNSW features)
    samples = [
        {
            "dur": 100, "sbytes": 1000, "dbytes": 500, "sttl": 64, "dttl": 64,
            "sloss": 0, "dloss": 0, "service": "http", "state": "CON",
            "spkts": 10, "dpkts": 8, "swin": 65535, "dwin": 65535,
            "stcpb": 0, "dtcpb": 0, "smeansz": 100, "dmeansz": 62,
            "trans_depth": 1, "res_bdy_len": 1024, "sjit": 0.1, "djit": 0.1,
            "stime": 123456, "ltime": 123500, "sintpkt": 5.0, "dintpkt": 6.0,
            "tcprtt": 0.05, "synack": 0.01, "ackdat": 0.02, "is_sm_ips_ports": 0,
            "ct_state_ttl": 1, "ct_flw_http_mthd": 1, "is_ftp_login": 0,
            "ct_ftp_cmd": 0, "ct_srv_src": 5, "ct_srv_dst": 3, "ct_dst_ltm": 10,
            "ct_src_dport_ltm": 2, "ct_dst_sport_ltm": 1, "ct_dst_src_ltm": 8,
            "attack_cat": "Normal"
        },
        {
            "dur": 10, "sbytes": 5000, "dbytes": 100, "sttl": 64, "dttl": 64,
            "sloss": 0, "dloss": 0, "service": "http", "state": "SYN",
            "spkts": 100, "dpkts": 2, "swin": 65535, "dwin": 65535,
            "stcpb": 0, "dtcpb": 0, "smeansz": 50, "dmeansz": 50,
            "trans_depth": 0, "res_bdy_len": 0, "sjit": 10.5, "djit": 1.0,
            "stime": 234567, "ltime": 234577, "sintpkt": 0.1, "dintpkt": 5.0,
            "tcprtt": 0.0, "synack": 0.0, "ackdat": 0.0, "is_sm_ips_ports": 0,
            "ct_state_ttl": 100, "ct_flw_http_mthd": 0, "is_ftp_login": 0,
            "ct_ftp_cmd": 0, "ct_srv_src": 100, "ct_srv_dst": 1, "ct_dst_ltm": 100,
            "ct_src_dport_ltm": 50, "ct_dst_sport_ltm": 1, "ct_dst_src_ltm": 100,
            "attack_cat": "DoS"
        },
    ]

    print("Running quick model checks...")
    for i, f in enumerate(samples, 1):
        try:
            res = det.predict(f)
            label = res.get('label', 'Unknown')
            confidence = res.get('confidence', 0.0)
            probs = res.get('probabilities', {})
            
            print(f"{i}: label={label}, confidence={confidence:.4f}")
            print(f"   probs={probs}, attack_cat={f.get('attack_cat')}")
        except Exception as e:
            print(f"Inference failed for sample {i}: {e}")


if __name__ == "__main__":
    main()

