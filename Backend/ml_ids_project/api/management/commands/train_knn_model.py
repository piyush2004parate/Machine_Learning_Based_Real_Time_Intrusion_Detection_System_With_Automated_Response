"""
Django Management Command to Train KNN Anomaly Detection Model
Usage: python manage.py train_knn_model [--data-path PATH] [--output-dir DIR]
"""

import os
import json
from pathlib import Path
from django.core.management.base import BaseCommand, CommandError
from django.conf import settings
import pandas as pd
from api.utils.knn_classifier import KNNAnomalyDetector


class Command(BaseCommand):
    help = 'Train KNN anomaly detection model using UNSW dataset'

    def add_arguments(self, parser):
        parser.add_argument(
            '--data-path',
            type=str,
            default='UNSW_Train_Test Datasets/UNSW_NB15_training-set.csv',
            help='Path to UNSW training dataset'
        )
        parser.add_argument(
            '--output-dir',
            type=str,
            default=None,
            help='Output directory for model artifacts'
        )
        parser.add_argument(
            '--n-neighbors',
            type=int,
            default=7,
            help='Number of neighbors for KNN'
        )

    def handle(self, *args, **options):
        data_path = options['data_path']
        output_dir = options['output_dir'] or os.path.join(
            settings.BASE_DIR, '..', '..', 'model', 'unsw_tabular'
        )
        n_neighbors = options['n_neighbors']

        # Resolve paths
        data_path = Path(settings.BASE_DIR) / data_path if not os.path.isabs(data_path) else data_path
        output_dir = Path(output_dir)

        self.stdout.write(self.style.SUCCESS('='*60))
        self.stdout.write(self.style.SUCCESS('KNN ANOMALY DETECTION MODEL TRAINING'))
        self.stdout.write(self.style.SUCCESS('='*60))

        # Check if data exists
        if not os.path.exists(data_path):
            raise CommandError(f'Data file not found: {data_path}')

        self.stdout.write(f'Loading data from: {data_path}')

        try:
            # Load data
            df = pd.read_csv(data_path)
            self.stdout.write(f'Data loaded successfully. Shape: {df.shape}')

            # Initialize detector
            detector = KNNAnomalyDetector()

            # Train model
            self.stdout.write(f'Training KNN model with n_neighbors={n_neighbors}...')
            metrics = detector.train(df, n_neighbors=n_neighbors)

            # Save model
            output_dir.mkdir(parents=True, exist_ok=True)

            model_path = output_dir / 'model_knn.pkl'
            features_path = output_dir / 'features_knn.json'
            scaler_path = output_dir / 'scaler_knn.pkl'
            metrics_path = output_dir / 'metrics_knn.json'

            detector.save_model(str(model_path), str(features_path), str(scaler_path))

            # Save metrics
            with open(metrics_path, 'w') as f:
                json.dump(metrics, f, indent=2)

            self.stdout.write(self.style.SUCCESS('\n' + '='*60))
            self.stdout.write(self.style.SUCCESS('MODEL TRAINING COMPLETE'))
            self.stdout.write(self.style.SUCCESS('='*60))

            self.stdout.write(f'\nModel saved to: {output_dir}')
            self.stdout.write(f'\nPerformance Metrics:')
            self.stdout.write(f'  Accuracy:  {metrics["accuracy"]:.4f}')
            self.stdout.write(f'  Precision: {metrics["precision"]:.4f}')
            self.stdout.write(f'  Recall:    {metrics["recall"]:.4f}')
            self.stdout.write(f'  F1-Score:  {metrics["f1"]:.4f}')

            self.stdout.write(self.style.SUCCESS('\nModel ready for deployment!'))

        except Exception as e:
            raise CommandError(f'Error during training: {str(e)}')
