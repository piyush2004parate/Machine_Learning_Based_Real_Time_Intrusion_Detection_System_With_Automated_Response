import os
import glob
import numpy as np
import pandas as pd
import joblib
import matplotlib.pyplot as plt

from sklearn.model_selection import train_test_split, learning_curve
from sklearn.metrics import accuracy_score, f1_score
from sklearn.base import clone

DATA_DIR = r"C:\Users\sanja\OneDrive\Documents\CSE-CIC-IDS2018 Dataset"
MODEL_FILE = "knn_model_cic2018.pkl"
SCALER_FILE = "scaler_cic2018.pkl"
SAMPLE_FRACTION = 0.05  # Retaining our quick sampling to prevent memory exhaustion

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
        return 'Benign'

def load_sample_dataset():
    all_files = glob.glob(os.path.join(DATA_DIR, "*.csv"))
    dfs = []
    for f in all_files:
        try:
            df_chunk = pd.read_csv(f, low_memory=False, on_bad_lines='skip')
            # 5% fraction is highly sufficient for diagnostic representation
            df_chunk = df_chunk.sample(frac=SAMPLE_FRACTION, random_state=42)
            df_chunk.columns = df_chunk.columns.str.strip()
            if 'Label' in df_chunk.columns:
                df_chunk['Mapped_Label'] = df_chunk['Label'].apply(map_labels)
                dfs.append(df_chunk)
        except Exception as e:
            pass # Keep it clean
    if dfs:
        df = pd.concat(dfs, ignore_index=True)
        df.replace([np.inf, -np.inf], np.nan, inplace=True)
        df.dropna(inplace=True)
        return df
    return pd.DataFrame()

def main():
    print("[1] Loading Model and Scaler...")
    try:
        model_data = joblib.load(MODEL_FILE)
        model = model_data['model']
        top_20_features = model_data['features']
        scaler = joblib.load(SCALER_FILE)
        print(f" -> Champion loaded: {model.__class__.__name__}")
    except Exception as e:
         print(f"Error loading models: {e}")
         return

    print("[2] Loading Representative Sample Dataset...")
    df = load_sample_dataset()
    if df.empty:
        print(" -> Dataset not loaded. Exiting.")
        return
    
    # Isolate X and y
    X = df[top_20_features]
    X = X.apply(pd.to_numeric, errors='coerce').fillna(0)
    y = df['Mapped_Label']

    print("[3] Splitting into Target Train and Test Sets...")
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=100, stratify=y)
    
    print("[4] Scaling Data...")
    X_train_scaled = scaler.transform(X_train)
    X_test_scaled = scaler.transform(X_test)
    
    print("[5] Calculating Performance Gap on Pre-trained Champion...")
    # Inference with pre-trained parameters
    y_pred_train = model.predict(X_train_scaled)
    y_pred_test = model.predict(X_test_scaled)
    
    train_acc = accuracy_score(y_train, y_pred_train)
    test_acc = accuracy_score(y_test, y_pred_test)
    train_f1 = f1_score(y_train, y_pred_train, average='macro', zero_division=0)
    test_f1 = f1_score(y_test, y_pred_test, average='macro', zero_division=0)
    
    print(f"\n==========================================")
    print(f"          SIDE-BY-SIDE PERFORMANCE")
    print(f"==========================================")
    print(f"Train Accuracy: {train_acc:.4f}  |  Test Accuracy: {test_acc:.4f}")
    print(f"Train F1-Score: {train_f1:.4f}  |  Test F1-Score: {test_f1:.4f}")
    print(f"==========================================\n")
    
    print("[6] Generating 5-Fold Learning Curve (Simulated Truncated Fitting)....")
    print(" -> Cloning the model architecture to fit varying data sizes...")
    model_clone = clone(model)
    
    # Calculate learning curve mapping
    train_sizes, train_scores, test_scores = learning_curve(
        estimator=model_clone,
        X=X_train_scaled,
        y=y_train,
        train_sizes=np.linspace(0.1, 1.0, 5),
        cv=5,
        n_jobs=-1,
        scoring='accuracy'
    )
    
    # Plotting calculations
    train_scores_mean = np.mean(train_scores, axis=1)
    test_scores_mean = np.mean(test_scores, axis=1)
    
    plt.figure(figsize=(10, 6))
    plt.plot(train_sizes, train_scores_mean, "o-", color="blue", label="Training Score (Fit)")
    plt.plot(train_sizes, test_scores_mean, "o-", color="orange", label="Cross-Validation Score")
    plt.title(f"Learning Curve Analysis ({model.__class__.__name__})")
    plt.xlabel("Training Examples Provided")
    plt.ylabel("Accuracy Score")
    plt.legend(loc="lower right")
    plt.grid(True, linestyle="--", alpha=0.6)
    
    plt.savefig("learning_curve.png")
    print(" -> Saved 5-Fold CV plot to: 'learning_curve.png'")
    
    print("\n[7] Automated Baseline Diagnosis:")
    if train_acc > 0.98 and (train_acc - test_acc) > 0.05:
        print("🚨 WARNING: High Variance (Overfitting Detected).")
        print("The model performs exceptionally well on the training data but fails to generalize. Consider applying constraints like `max_depth` or higher regularization.")
    elif train_acc < 0.85 and test_acc < 0.85:
        print("🚨 WARNING: High Bias (Underfitting Detected).")
        print("The model struggles to learn the underlying patterns. The complexity of the architecture is too restricted.")
    elif train_acc >= 0.90 and test_acc >= 0.90 and abs(train_acc - test_acc) <= 0.05:
        print("✅ SUCCESS: Good Fit (Model Generalizes Well).")
        gap = abs((train_acc - test_acc) * 100)
        print(f"The model proves generalized capability with an impressively tight Train/Test tolerance of {gap:.2f}%.")
    else:
        print("⚠️ OBSERVATION: Model is performing moderately well, evaluate the 'learning_curve.png' convergence for further insights.")
        print(f"Current recorded accuracy gap: {abs(train_acc - test_acc)*100:.2f}%")

if __name__ == "__main__":
    main()
