import os
import glob
import time
import numpy as np
import pandas as pd
import joblib

from sklearn.ensemble import RandomForestClassifier
from sklearn.neighbors import KNeighborsClassifier
from sklearn.preprocessing import RobustScaler
from sklearn.model_selection import train_test_split
from imblearn.over_sampling import SMOTE
from imblearn.under_sampling import EditedNearestNeighbours
from imblearn.combine import SMOTEENN
from sklearn.metrics import accuracy_score, precision_score, recall_score, classification_report

# Configuration
DATA_DIR = r"C:\Users\sanja\OneDrive\Documents\CSE-CIC-IDS2018 Dataset"
OUTPUT_MODEL = "knn_model_cic2018.pkl"
OUTPUT_SCALER = "scaler_cic2018.pkl"

MAX_BENIGN_SAMPLES = 250000
MAX_ATTACK_SAMPLES = 75000
MIN_ATTACK_SAMPLES = 10000  # Cap extreme minority generation (e.g. Web Attack)

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
    print("[1] Loading Data...")
    all_files = glob.glob(os.path.join(DATA_DIR, "*.csv"))
    if not all_files:
        print(f"Error: No CSV files found in {DATA_DIR}")
        return

    dfs = []
    for idx, f in enumerate(all_files):
        print(f"  -> Reading {os.path.basename(f)} ({idx+1}/{len(all_files)})")
        try:
            df_chunk = pd.read_csv(f, low_memory=False, on_bad_lines='skip')
            df_chunk.columns = df_chunk.columns.str.strip()
            
            if 'Label' in df_chunk.columns:
                df_chunk['Mapped_Label'] = df_chunk['Label'].apply(map_labels)
                sampled_mini = []
                # Stratify per file early to prevent OOM
                for label in df_chunk['Mapped_Label'].unique():
                    subset = df_chunk[df_chunk['Mapped_Label'] == label]
                    limit = MAX_BENIGN_SAMPLES if label == 'Benign' else MAX_ATTACK_SAMPLES
                    if len(subset) > limit:
                        subset = subset.sample(n=limit, random_state=42)
                    sampled_mini.append(subset)
                df_mini = pd.concat(sampled_mini, ignore_index=True)
                dfs.append(df_mini)
                del df_chunk
                del sampled_mini
            else:
                print(f"     Skipping {os.path.basename(f)}, no Label column found.")
        except Exception as e:
            print(f"  -> Error reading {f}: {e}")

    if not dfs:
        print("Error: No valid dataframes loaded.")
        return

    df = pd.concat(dfs, ignore_index=True)
    print(f"\n[2] Pre-processing Data (Total records loaded: {len(df)})")
    
    df.replace([np.inf, -np.inf], np.nan, inplace=True)
    df.dropna(inplace=True)
    
    # Global Undersampling Check
    sampled_dfs = []
    print("Class distribution before final downsampling:")
    print(df['Mapped_Label'].value_counts())
    
    for label in df['Mapped_Label'].unique():
        subset = df[df['Mapped_Label'] == label]
        limit = MAX_BENIGN_SAMPLES if label == 'Benign' else MAX_ATTACK_SAMPLES
        if len(subset) > limit:
            subset = subset.sample(n=limit, random_state=42)
        sampled_dfs.append(subset)
    
    df_sampled = pd.concat(sampled_dfs, ignore_index=True)
    counts_after_down = df_sampled['Mapped_Label'].value_counts()
    print("\nClass distribution after downsampling:")
    print(counts_after_down)
    
    # Define smart SMOTE strategy
    smote_dict = {}
    for label, count in counts_after_down.items():
        if count < MIN_ATTACK_SAMPLES:
            smote_dict[label] = MIN_ATTACK_SAMPLES # Boost sparse attacks
        else:
            smote_dict[label] = count # Keep current density

    X_full = df_sampled.drop(columns=['Label', 'Mapped_Label'])
    y = df_sampled['Mapped_Label']
    
    X_full = X_full.apply(pd.to_numeric, errors='coerce')
    X_full.fillna(0, inplace=True)

    print("\n[3] Training Random Forest for Feature Selection...")
    rf_fs = RandomForestClassifier(n_estimators=50, random_state=42, n_jobs=-1)
    rf_fs.fit(X_full, y)
    
    feature_importances = pd.Series(rf_fs.feature_importances_, index=X_full.columns)
    top_20_features = feature_importances.nlargest(20)
    top_20_cols = list(top_20_features.index)
    
    print("\n*** TOP 20 FEATURES SELECTED ***")
    for idx, (feat, imp) in enumerate(top_20_features.items(), 1):
        print(f"{idx}. {feat}: {imp:.4f}")
    
    X = X_full[top_20_cols]

    print("\n[4] Creating Train/Test Splits for Champion Model Evaluation...")
    # Split 80/20. Testing must be strictly organic data!
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42, stratify=y)
    
    print("\n[5] Applying SMOTE-ENN (Smarter Balancing) to Train Split ONLY...")
    smote = SMOTE(sampling_strategy=smote_dict, random_state=42)
    enn = EditedNearestNeighbours(sampling_strategy='all')
    smote_enn = SMOTEENN(smote=smote, enn=enn, random_state=42)
    
    X_train_res, y_train_res = smote_enn.fit_resample(X_train, y_train)
    print(f"Resampled training data shape:\n{y_train_res.value_counts()}")
    
    print("\n[6] Scaling Data (RobustScaler)...")
    scaler = RobustScaler()
    X_train_scaled = scaler.fit_transform(X_train_res)
    X_test_scaled = scaler.transform(X_test)
    
    print("\n[7] Training Champion Contenders...")
    
    # Contender 1: Distance-weighted KNN
    print("  -> Training KNeighborsClassifier (n_neighbors=5, weights='distance')...")
    start_time = time.time()
    knn = KNeighborsClassifier(n_neighbors=5, weights='distance', n_jobs=-1)
    knn.fit(X_train_scaled, y_train_res)
    print(f"     Finished in {time.time()-start_time:.2f}s")
    
    # Contender 2: Balanced Random Forest
    print("  -> Training RandomForestClassifier (class_weight='balanced')...")
    start_time = time.time()
    rf = RandomForestClassifier(n_estimators=100, class_weight='balanced', random_state=42, n_jobs=-1)
    rf.fit(X_train_scaled, y_train_res)
    print(f"     Finished in {time.time()-start_time:.2f}s")
    
    print("\n[8] Champion Model Evaluation on Organic Test Split...")
    models = {'KNN (Distance Weighted)': knn, 'Random Forest (Balanced)': rf}
    champion_name = None
    champion_model = None
    best_score = 0
    
    for name, model in models.items():
        print(f"\nEvaluating {name}...")
        y_pred = model.predict(X_test_scaled)
        
        acc = accuracy_score(y_test, y_pred)
        prec_macro = precision_score(y_test, y_pred, average='macro', zero_division=0)
        rec_macro = recall_score(y_test, y_pred, average='macro', zero_division=0)
        
        print(f"  Accuracy: {acc:.4f} | Precision (Macro): {prec_macro:.4f} | Recall (Macro): {rec_macro:.4f}")
        print("  Detailed Classification Report:")
        print(classification_report(y_test, y_pred, zero_division=0))
        
        # Determine the champion
        combined_score = (acc + prec_macro + rec_macro) / 3
        if combined_score > best_score:
            best_score = combined_score
            champion_name = name
            champion_model = model
            
    print(f"\n*** CHAMPION DECLARED: {champion_name} (Combined Score: {best_score:.4f}) ***")
    
    print("\n[9] Exporting Champion Model...")
    model_data = {
        'model': champion_model,
        'features': top_20_cols
    }
    joblib.dump(model_data, OUTPUT_MODEL)
    joblib.dump(scaler, OUTPUT_SCALER)
    
    print(f"Successfully saved {champion_name} as '{OUTPUT_MODEL}'")
    print(f"Successfully saved RobustScaler as '{OUTPUT_SCALER}'")
    print("Champion Pipeline fully complete!")

if __name__ == "__main__":
    main()
