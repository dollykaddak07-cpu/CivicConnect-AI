"""Retrain the CivicConnect complaint classifier.

Run from the project root:
    python ml/train_model.py
"""
from pathlib import Path
import json
import joblib
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.pipeline import FeatureUnion
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, precision_recall_fscore_support, confusion_matrix, classification_report

BASE = Path(__file__).resolve().parent
DATA = BASE / 'complaint_dataset.csv'
MODEL = BASE / 'complaint_classifier.joblib'
METRICS = BASE / 'metrics.json'

df = pd.read_csv(DATA)
X_train, X_test, y_train, y_test = train_test_split(
    df['text'], df['category'], test_size=0.20, random_state=42, stratify=df['category']
)
model = Pipeline([
    ('features', FeatureUnion([
        ('word_tfidf', TfidfVectorizer(lowercase=True, strip_accents='unicode', ngram_range=(1,2), sublinear_tf=True, max_features=8000)),
        ('char_tfidf', TfidfVectorizer(analyzer='char', ngram_range=(2,5), min_df=1, sublinear_tf=True, max_features=12000))
    ])),
    ('classifier', LogisticRegression(max_iter=2500, class_weight='balanced', random_state=42))
])
model.fit(X_train, y_train)
pred = model.predict(X_test)
precision, recall, f1, _ = precision_recall_fscore_support(y_test, pred, average='weighted', zero_division=0)
labels = list(model.classes_)
metrics = {
    'model': 'Word + Character TF-IDF + Logistic Regression',
    'task': 'Civic complaint category classification',
    'dataset': 'complaint_dataset.csv',
    'dataset_rows': len(df),
    'train_rows': len(X_train),
    'test_rows': len(X_test),
    'classes': labels,
    'test_accuracy': round(float(accuracy_score(y_test, pred)), 4),
    'weighted_precision': round(float(precision), 4),
    'weighted_recall': round(float(recall), 4),
    'weighted_f1': round(float(f1), 4),
    'confusion_matrix': confusion_matrix(y_test, pred, labels=labels).tolist(),
    'class_report': classification_report(y_test, pred, output_dict=True, zero_division=0),
}
joblib.dump(model, MODEL)
METRICS.write_text(json.dumps(metrics, indent=2), encoding='utf-8')
print(f"Model trained on {len(X_train)} rows; tested on {len(X_test)} rows.")
print(f"Test accuracy: {metrics['test_accuracy']*100:.2f}%")
print(f"Weighted F1: {metrics['weighted_f1']*100:.2f}%")
