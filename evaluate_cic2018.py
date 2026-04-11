import os
import glob
import time
import numpy as np
import pandas as pd
import joblib

from sklearn.metrics import accuracy_score, precision_score, recall_score, classification_report

# Configuration
DATA_DIR = r"C:\Users\sanja\OneDrive\Documents\CSE-CIC-IDS2018 Dataset"
MODEL_FILE = "knn_model_cic2018.pkl"
SCALER_FILE = "scaler_cic2018.pkl"
SAMPLE_FRACTION = 0.05 # Evaluate on a random subset (e.g., 5%) to save memory/time. Change to 1.0 for full dataset.

def map_labels(label_str):
    label_str = str(label_str).lower().strip()
    if label_str == 'benign':
        return 'Benign'
    elif 'ddos' in label_str:
        return 'DDoS'
    elif 'dos' in label_str:
        return 'DoS'
    elif 'brute' in label_str or 'ftp' in label_str or 'ssh' in label_str:
        return 'Brute-force'
    elif 'web' in label_str or 'xss' in label_str or 'sql' in label_str:
        return 'Web Attack'
    elif 'infil' in label_str:
        return 'Infiltration'
    elif 'bot' in label_str:
        return 'Botnet'
    else:
        return 'Benign' # Default fallback

def main():
    print("[1] Loading Models...")
    try:
        model_data = joblib.load(MODEL_FILE)
        knn = model_data['model']
        top_20_cols = model_data['features']
        scaler = joblib.load(SCALER_FILE)
        print("  -> Model and Scaler loaded successfully.\n")
    except Exception as e:
        print(f"  -> Error loading models: {e}")
        print("  -> Please make sure 'knn_model_cic2018.pkl' and 'scaler_cic2018.pkl' exist in the directory.")
        return

    print("[2] Loading Evaluation Data...")
    all_files = glob.glob(os.path.join(DATA_DIR, "*.csv"))
    if not all_files:
        print(f"Error: No CSV files found in {DATA_DIR}")
        return

    dfs = []
    for idx, f in enumerate(all_files):
        print(f"  -> Reading sample from {os.path.basename(f)} ({idx+1}/{len(all_files)})")
        try:
            # Read only a fraction 
            df_chunk = pd.read_csv(f, low_memory=False, on_bad_lines='skip')
            df_chunk = df_chunk.sample(frac=SAMPLE_FRACTION, random_state=42)
            df_chunk.columns = df_chunk.columns.str.strip()
            
            if 'Label' in df_chunk.columns:
                df_chunk['Mapped_Label'] = df_chunk['Label'].apply(map_labels)
                dfs.append(df_chunk)
            else:
                print(f"     Skipping {os.path.basename(f)}, no Label column found.")
        except Exception as e:
            print(f"  -> Error reading {f}: {e}")

    if not dfs:
        print("Error: No valid dataframes loaded.")
        return

    df = pd.concat(dfs, ignore_index=True)
    print(f"\n[3] Pre-processing Data (Total evaluation records: {len(df)})")
    
    df.replace([np.inf, -np.inf], np.nan, inplace=True)
    df.dropna(inplace=True)
    
    y_true = df['Mapped_Label']
    
    missing_cols = [c for c in top_20_cols if c not in df.columns]
    if missing_cols:
        for c in missing_cols:
            df[c] = 0
            
    X = df[top_20_cols]
    
    # Force numeric type
    X = X.apply(pd.to_numeric, errors='coerce')
    X.fillna(0, inplace=True)

    print("\n[4] Scaling Features...")
    X_scaled = scaler.transform(X)

    print("\n[5] Making Predictions (this might take a moment depending on dataset size)...")
    start_time = time.time()
    y_pred = knn.predict(X_scaled)
    print(f"Predicted in {time.time() - start_time:.2f} seconds.")

    print("\n[6] Calculating Metrics...")
    acc = accuracy_score(y_true, y_pred)
    prec_macro = precision_score(y_true, y_pred, average='macro', zero_division=0)
    prec_weighted = precision_score(y_true, y_pred, average='weighted', zero_division=0)
    rec_macro = recall_score(y_true, y_pred, average='macro', zero_division=0)
    rec_weighted = recall_score(y_true, y_pred, average='weighted', zero_division=0)

    print("\n=============================================")
    print("           EVALUATION RESULTS                ")
    print("=============================================")
    print(f"Overall Accuracy:       {acc:.4f} ({acc*100:.2f}%)")
    print("-" * 45)
    print(f"Precision (Macro):      {prec_macro:.4f}")
    print(f"Precision (Weighted):   {prec_weighted:.4f}")
    print(f"Recall (Macro):         {rec_macro:.4f}")
    print(f"Recall (Weighted):      {rec_weighted:.4f}")
    print("=============================================")
    
    print("\nDetailed Classification Report:")
    print(classification_report(y_true, y_pred, zero_division=0))
    
    print("\nConfusion Matrix:")
    cm = pd.crosstab(y_true.values, y_pred, rownames=['Actual / True'], colnames=['Predicted'])
    print(cm)

if __name__ == "__main__":
    main()
