import pandas as pd
import numpy as np
from sklearn.metrics import precision_recall_curve, roc_curve, confusion_matrix, average_precision_score, roc_auc_score, accuracy_score, precision_score, recall_score, f1_score
import joblib

print("Loading test predictions parquet...")
df = pd.read_parquet('/Users/hp/Desktop/L&T_Dashboard/BatteryDashboard/data/test_predictions.parquet')

y_true = df['y'].values
y_prob = df['p'].values

print("Computing curves...")
# ROC
fpr, tpr, roc_thresh = roc_curve(y_true, y_prob)
# PR
precision, recall, pr_thresh = precision_recall_curve(y_true, y_prob)

# Downsample to speed up loading and charting in Plotly (e.g. 500 points max)
def downsample(x, y, n=500):
    if len(x) <= n:
        return x, y
    indices = np.linspace(0, len(x) - 1, n, dtype=int)
    return x[indices], y[indices]

fpr_d, tpr_d = downsample(fpr, tpr)
prec_d, rec_d = downsample(precision, recall)

# Metrics at common thresholds and specific 0.5 threshold
y_pred = (y_prob > 0.5).astype(int)
tn, fp, fn, tp = confusion_matrix(y_true, y_pred).ravel()

pr_auc = average_precision_score(y_true, y_prob)
roc_auc = roc_auc_score(y_true, y_prob)
acc = accuracy_score(y_true, y_pred)
prec = precision_score(y_true, y_pred)
rec = recall_score(y_true, y_pred)
f1 = f1_score(y_true, y_pred)

print(f"Metrics: PR-AUC={pr_auc:.3f}, ROC-AUC={roc_auc:.3f}, Acc={acc:.3f}")

metrics_dict = {
    'fpr': fpr_d.tolist(),
    'tpr': tpr_d.tolist(),
    'precision': prec_d.tolist(),
    'recall': rec_d.tolist(),
    'confusion_matrix': {
        'tn': int(tn),
        'fp': int(fp),
        'fn': int(fn),
        'tp': int(tp)
    },
    'metrics': {
        'pr_auc': float(pr_auc),
        'roc_auc': float(roc_auc),
        'accuracy': float(acc),
        'precision': float(prec),
        'recall': float(rec),
        'f1': float(f1)
    }
}

joblib.dump(metrics_dict, '/Users/hp/Desktop/L&T_Dashboard/BatteryDashboard/data/performance_metrics.pkl')
print("Saved performance metrics to BatteryDashboard/data/performance_metrics.pkl")
