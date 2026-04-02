import os
import pytest
import pandas as pd
from pathlib import Path

# Ensure package import works when running tests from Backend/
import sys
sys.path.insert(0, str(Path(__file__).parent / 'ml_ids_project'))

from api.utils.knn_classifier import KNNAnomalyDetector


def load_dataset(sample_size=10000, random_state=42):
    dataset_path = Path(__file__).parent / 'ml_ids_project' / 'UNSW_Train_Test Datasets' / 'UNSW_NB15_training-set.csv'
    df = pd.read_csv(dataset_path)
    n = min(sample_size, len(df))
    return df.sample(n=n, random_state=random_state)


def test_model_accuracy_threshold():
    """Train a KNN model on a sample of the UNSW training set and assert minimum accuracy.

    The acceptance threshold can be overridden with the env var `MODEL_ACC_THRESHOLD`.
    """
    sample = load_dataset(sample_size=5000)

    detector = KNNAnomalyDetector()

    metrics = detector.train(sample, n_neighbors=7)

    acc = float(metrics.get('accuracy', 0.0))
    thresh = float(os.getenv('MODEL_ACC_THRESHOLD', '0.70'))

    print(f"Trained model metrics: accuracy={acc:.4f}, precision={metrics.get('precision')}, recall={metrics.get('recall')}")

    assert acc >= thresh, f"Model accuracy {acc:.4f} below threshold {thresh:.2f}"


if __name__ == '__main__':
    # Allow running the test file directly for quick checks
    try:
        test_model_accuracy_threshold()
        print('Model accuracy test passed')
    except AssertionError as e:
        print('Model accuracy test failed:', e)
        raise
