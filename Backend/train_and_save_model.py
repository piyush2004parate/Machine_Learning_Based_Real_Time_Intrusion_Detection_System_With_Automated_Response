"""Train a KNN model on the UNSW training set and save artifacts.

Produces:
 - models/knn_model.joblib
 - models/knn_scaler.joblib
 - models/knn_features.json

Run from `Backend`:
    python train_and_save_model.py
"""
from pathlib import Path
import sys
import json
import pandas as pd

# Ensure imports from ml_ids_project work when executed from Backend/
sys.path.insert(0, str(Path(__file__).parent / 'ml_ids_project'))

from api.utils.knn_classifier import KNNAnomalyDetector


def load_full_training_set():
    dataset_path = Path(__file__).parent / 'ml_ids_project' / 'UNSW_Train_Test Datasets' / 'UNSW_NB15_training-set.csv'
    if not dataset_path.exists():
        raise FileNotFoundError(f"Training dataset not found at {dataset_path}")
    return pd.read_csv(dataset_path)


def main():
    print('Loading dataset...')
    df = load_full_training_set()

    # Optionally limit rows to speed up local runs; comment out to use full dataset
    max_rows = int(__import__('os').environ.get('TRAIN_MAX_ROWS', '0'))
    if max_rows > 0:
        df = df.sample(n=min(max_rows, len(df)), random_state=42)
        print(f'Using {len(df)} rows for training (TRAIN_MAX_ROWS={max_rows})')
    else:
        print(f'Using full dataset ({len(df)} rows) for training')

    detector = KNNAnomalyDetector()

    print('Training model...')
    metrics = detector.train(df, n_neighbors=7)

    models_dir = Path(__file__).parent / 'models'
    models_dir.mkdir(parents=True, exist_ok=True)

    model_path = models_dir / 'knn_model.joblib'
    scaler_path = models_dir / 'knn_scaler.joblib'
    features_path = models_dir / 'knn_features.json'

    print('Saving model artifacts...')
    detector.save_model(str(model_path), str(features_path), str(scaler_path))

    print('\nTraining complete. Metrics:')
    print(json.dumps({k: (v if k != 'confusion_matrix' else v) for k, v in metrics.items()}, indent=2))
    print(f'Artifacts saved to: {models_dir}\n')


if __name__ == '__main__':
    main()
