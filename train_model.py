import numpy as np
import pandas as pd
from xgboost import XGBClassifier
from sklearn.model_selection import GroupShuffleSplit
from sklearn.metrics import average_precision_score, roc_auc_score, accuracy_score, precision_recall_curve, roc_curve, confusion_matrix
import joblib
import os

# Create folders
os.makedirs('/Users/hp/Desktop/L&T_Dashboard/BatteryDashboard/data', exist_ok=True)
os.makedirs('/Users/hp/Desktop/L&T_Dashboard/BatteryDashboard/assets/images', exist_ok=True)

# Load data
print("Loading dataset...")
raw = pd.read_csv('/Users/hp/Downloads/unified_bess_dataset_2.csv')
print("Loaded raw data shape:", raw.shape)

HORIZON = 300
TR_TEMP = 120
LARGE_T = 40

# Feature engineering
print("Building features...")
def build_features(df):
    df=df.copy()
    if 'run_id' not in df: df['run_id']=0
    df=df.sort_values(['run_id','cell_id','ts_timestamp'])
    g=df.groupby(['run_id','cell_id'],sort=False)
    dt=(g['ts_timestamp'].diff()/1000.0).replace(0,np.nan)      # seconds between rows
    df['d_t_surf']=(g['cell_t_surf'].diff()/dt).fillna(0)       # per-second rates (spacing-robust)
    df['d_v']=(g['cell_v_meas'].diff()/dt).fillna(0)
    df['d_h2']=(g['enclosure_h2_ppm'].diff()/dt).fillna(0)
    g=df.groupby(['run_id','cell_id'],sort=False)               # windowed trend
    df['roll_max_dt']=g['d_t_surf'].transform(lambda s:s.rolling(4,min_periods=1).max())
    df['t_accel']=g['d_t_surf'].diff().fillna(0)
    # spatial: hottest neighbour temp & neighbour heating-rate (drives propagation)
    df=df.reset_index(drop=True)
    co=df['cell_id'].str.extract(r'_(\d+)-(\d+)-(\d+)$').astype(int)
    df['_r'],df['_c'],df['_l']=co[0],co[1],co[2]
    R,C,L=df['_r'].max()+1,df['_c'].max()+1,df['_l'].max()+1
    def nbrmax(A):
        o=np.full_like(A,-1e9)
        for ax in range(3):
            for sh in (1,-1): o=np.maximum(o,np.roll(A,sh,axis=ax))
        return o
    nmax=np.zeros(len(df)); ndmax=np.zeros(len(df))
    for _,gi in df.groupby(['run_id','ts_timestamp']):
        T=np.full((R,C,L),25.0); D=np.zeros((R,C,L))
        r,cc,l=gi['_r'].values,gi['_c'].values,gi['_l'].values
        T[r,cc,l]=gi['cell_t_surf'].values; D[r,cc,l]=gi['d_t_surf'].values
        NM=nbrmax(T); ND=nbrmax(D); nmax[gi.index]=NM[r,cc,l]; ndmax[gi.index]=ND[r,cc,l]
    df['nbr_max_tsurf']=nmax; df['nbr_max_dt']=ndmax
    return df.drop(columns=['_r','_c','_l'])

data = build_features(raw)
data['y'] = ((data.lbl_tt_runaway>=0) & (data.lbl_tt_runaway<=HORIZON)).astype(int)

DROP = ['cell_id','run_id','run_outcome','ts_timestamp','lbl_t_core','lbl_alpha_sei','lbl_alpha_an',
        'lbl_alpha_ca','lbl_q_chem','lbl_p_internal','lbl_tt_runaway','cls_is_anomaly','cls_fail_mode',
        'meta_cell_chemistry','meta_cell_form_factor','y']
FEATURES = [c for c in data.columns if c not in DROP and data[c].nunique()>1]

X, y, groups = data[FEATURES], data.y.values, data.run_id.values
tr, te = next(GroupShuffleSplit(1, test_size=0.30, random_state=0).split(X, y, groups))

spw = (y[tr]==0).sum()/max((y[tr]==1).sum(),1)

print("Starting grid search on training set splits...")
# Fit model (since we know grid search in notebook took Config cfg, let's run grid search or just use a good parameter)
itr, ival = next(GroupShuffleSplit(1, test_size=0.30, random_state=1).split(X.iloc[tr], y[tr], groups[tr]))
Xi, yi = X.iloc[tr].iloc[itr], y[tr][itr]
Xv, yv = X.iloc[tr].iloc[ival], y[tr][ival]
grid = [dict(max_depth=md, learning_rate=lr, min_child_weight=mcw, n_estimators=500, subsample=0.9, colsample_bytree=0.8)
        for md in [6, 9] for lr in [0.05, 0.1] for mcw in [1, 5]]
best = None
for cfg in grid:
    mm = XGBClassifier(scale_pos_weight=spw, tree_method='hist', n_jobs=4, eval_metric='aucpr', **cfg).fit(Xi, yi)
    s = average_precision_score(yv, mm.predict_proba(Xv)[:,1])
    if best is None or s > best[0]:
        best = (s, cfg)
    print(f"val PR-AUC {s:.3f} with depth={cfg['max_depth']} lr={cfg['learning_rate']} mcw={cfg['min_child_weight']}")

best_params = best[1]
print("BEST PARAMS:", best_params)

# Train final model
print("Training final model of XGBClassifier...")
model = XGBClassifier(scale_pos_weight=spw, tree_method='hist', n_jobs=4, eval_metric='aucpr', **best_params).fit(X.iloc[tr], y[tr])

# Save model and artifacts
joblib.dump(model, '/Users/hp/Desktop/L&T_Dashboard/BatteryDashboard/model.pkl')
print("Model saved to BatteryDashboard/model.pkl")

# Save test metrics and lists
test_data = data.iloc[te].copy()
test_data['p'] = model.predict_proba(X.iloc[te])[:,1]
# Save test predictions for the performance charts
test_data.to_parquet('/Users/hp/Desktop/L&T_Dashboard/BatteryDashboard/data/test_predictions.parquet', index=False)
print("Saved performance evaluation data")

# Let's save a mapping of run_id to outcome and some extra info for quick loading in the dashboard
# Precomputed feature importance
feat_imp = pd.DataFrame({'feature': FEATURES, 'importance': model.feature_importances_})
feat_imp.to_csv('/Users/hp/Desktop/L&T_Dashboard/BatteryDashboard/data/feature_importances.csv', index=False)
print("Saved feature importances")

# Precompute training dataset dimensions
model_info = {
    'hyperparameters': str(best_params),
    'model_type': 'XGBClassifier',
    'train_samples': len(tr),
    'test_samples': len(te),
    'num_features': len(FEATURES),
    'features': FEATURES
}
joblib.dump(model_info, '/Users/hp/Desktop/L&T_Dashboard/BatteryDashboard/data/model_info.pkl')
print("Saved model info")
