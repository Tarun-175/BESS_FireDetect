import numpy as np
import pandas as pd
import joblib
import os
import streamlit as st

# Constants
HORIZON = 300
TR_TEMP = 120
LARGE_T = 40

# Feature Names list from training
FEATURES = [
    'cell_v_meas', 'cell_i_meas', 'cell_t_surf', 'cell_soc', 'cell_soh', 
    'rack_coolant_t_out', 'enclosure_h2_ppm', 'enclosure_co_ppm', 
    'meta_node_pos_x', 'meta_node_pos_y', 'meta_node_pos_z', 'meta_nominal_cap', 
    'd_t_surf', 'd_v', 'd_h2', 'roll_max_dt', 't_accel', 'nbr_max_tsurf', 'nbr_max_dt'
]

FEATURE_DESCRIPTIONS = {
    'cell_v_meas': 'Measured cell terminal voltage (V)',
    'cell_i_meas': 'Measured cell current (A)',
    'cell_t_surf': 'Measured cell surface temperature (°C)',
    'cell_soc': 'State of charge (%)',
    'cell_soh': 'State of health (%)',
    'rack_coolant_t_out': 'Coolant outlet temperature of the rack (°C)',
    'enclosure_h2_ppm': 'Hydrogen concentration in the enclosure (ppm)',
    'enclosure_co_ppm': 'Carbon monoxide concentration in the enclosure (ppm)',
    'meta_node_pos_x': 'Cell spatial X-coordinate inside layout',
    'meta_node_pos_y': 'Cell spatial Y-coordinate inside layout',
    'meta_node_pos_z': 'Cell spatial Z-coordinate inside layout',
    'meta_nominal_cap': 'Nominal capacity of the cell (Ah)',
    'd_t_surf': 'Rate of change of surface temperature (°C/s)',
    'd_v': 'Rate of change of terminal voltage (V/s)',
    'd_h2': 'Rate of change of hydrogen gas concentration (ppm/s)',
    'roll_max_dt': '4-step rolling maximum heating rate (°C/s)',
    't_accel': 'Cell temperature acceleration rate (°C/s²)',
    'nbr_max_tsurf': 'Maximum surface temperature of adjacent neighbor cells (°C)',
    'nbr_max_dt': 'Maximum heating rate of adjacent neighbor cells (°C/s)'
}

@st.cache_resource
def load_xgb_model():
    model_path = os.path.join(os.path.dirname(__file__), 'model.pkl')
    return joblib.load(model_path)

@st.cache_data
def load_performance_metrics():
    metrics_path = os.path.join(os.path.dirname(__file__), 'data', 'performance_metrics.pkl')
    return joblib.load(metrics_path)

@st.cache_data
def load_model_info():
    info_path = os.path.join(os.path.dirname(__file__), 'data', 'model_info.pkl')
    return joblib.load(info_path)

@st.cache_data
def load_feature_importances():
    imp_path = os.path.join(os.path.dirname(__file__), 'data', 'feature_importances.csv')
    return pd.read_csv(imp_path)

def build_features(df):
    """
    Identical feature engineering logic as the training notebook.
    Applies windowed, temporal, and spatial neighbor features.
    """
    df = df.copy()
    if 'run_id' not in df:
        df['run_id'] = 0
    
    # Ensure correct sorting order
    df = df.sort_values(['run_id', 'cell_id', 'ts_timestamp'])
    
    # Simple groupings
    g = df.groupby(['run_id', 'cell_id'], sort=False)
    
    # Seconds between rows
    dt = (g['ts_timestamp'].diff() / 1000.0).replace(0, np.nan)
    
    df['d_t_surf'] = (g['cell_t_surf'].diff() / dt).fillna(0)       # per-second rates
    df['d_v'] = (g['cell_v_meas'].diff() / dt).fillna(0)
    df['d_h2'] = (g['enclosure_h2_ppm'].diff() / dt).fillna(0)
    
    g = df.groupby(['run_id', 'cell_id'], sort=False)               # windowed trend
    df['roll_max_dt'] = g['d_t_surf'].transform(lambda s: s.rolling(4, min_periods=1).max())
    df['t_accel'] = g['d_t_surf'].diff().fillna(0)
    
    # Spatial feature extraction: hottest neighbor temp & neighbor heating rate
    df = df.reset_index(drop=True)
    co = df['cell_id'].str.extract(r'_(\d+)-(\d+)-(\d+)$').astype(int)
    df['_r'], df['_c'], df['_l'] = co[0], co[1], co[2]
    
    R, C, L = df['_r'].max() + 1, df['_c'].max() + 1, df['_l'].max() + 1
    
    def nbrmax(A):
        o = np.full_like(A, -1e9)
        for ax in range(3):
            for sh in (1, -1):
                o = np.maximum(o, np.roll(A, sh, axis=ax))
        return o
        
    nmax = np.zeros(len(df))
    ndmax = np.zeros(len(df))
    
    # Spatial calculation grouped per timestamp
    for _, gi in df.groupby(['run_id', 'ts_timestamp']):
        T = np.full((R, C, L), 25.0)
        D = np.zeros((R, C, L))
        r, cc, l = gi['_r'].values, gi['_c'].values, gi['_l'].values
        T[r, cc, l] = gi['cell_t_surf'].values
        D[r, cc, l] = gi['d_t_surf'].values
        NM = nbrmax(T)
        ND = nbrmax(D)
        nmax[gi.index] = NM[r, cc, l]
        ndmax[gi.index] = ND[r, cc, l]
        
    df['nbr_max_tsurf'] = nmax
    df['nbr_max_dt'] = ndmax
    
    return df.drop(columns=['_r', '_c', '_l'])

def get_true_severity(run_outcome):
    # Map raw field run_outcome to readable label
    if run_outcome in ('normal', 'fault_no_TR'):
        return 'Normal / No-TR'
    elif run_outcome == 'large':
        return 'TR - large cascade'
    else:
        return 'TR - contained'

def predict_class(df_run):
    """
    Determines run-level severity class using maximum measured temperatures of cell surface.
    Normal: no cell exceeds 120 C.
    Contained: > 0 and <= 40 cells exceed 120 C.
    Large: > 40 cells exceed 120 C.
    """
    max_temps = df_run.groupby('cell_id')['cell_t_surf'].max()
    runaway_count = int((max_temps > TR_TEMP).sum())
    
    if runaway_count == 0:
        pred_cls = 'Normal / No-TR'
    elif runaway_count <= LARGE_T:
        pred_cls = 'TR - contained'
    else:
        pred_cls = 'TR - large cascade'
        
    return pred_cls, runaway_count

def predict_run(df_run, model):
    """
    Builds features and predicts thermal runaway warning probability for each row.
    """
    df_feat = build_features(df_run)
    X = df_feat[FEATURES]
    probs = model.predict_proba(X)[:, 1]
    df_feat['p'] = probs
    return df_feat

def compute_warning_metrics(df_run_preds, threshold):
    """
    Computes summary prediction details for the given run:
    - Maximum probability
    - Warning time (earliest ts where any cell's probability > threshold)
    - Warning cell (cell that first triggered the warning)
    - Severity and true class
    - Runaway instant (earliest ts where any cell surface temp > 120)
    - Early warning lead time (difference in seconds)
    """
    # Max probability
    max_p = float(df_run_preds['p'].max())
    
    # Severity classification (using standard logic)
    severity_class, runaway_count = predict_class(df_run_preds)
    
    # Actual run outcome (if present)
    actual_outcome = 'Unknown'
    if 'run_outcome' in df_run_preds.columns:
        actual_outcome = get_true_severity(df_run_preds['run_outcome'].iloc[0])
        
    # Earliest runaway time (cell_t_surf > 120)
    runaway_events = df_run_preds[df_run_preds['cell_t_surf'] > TR_TEMP]
    if not runaway_events.empty:
        # timestamp is in ms, convert to seconds
        runaway_time_sec = float(runaway_events['ts_timestamp'].min() / 1000.0)
        runaway_cell = runaway_events.loc[runaway_events['ts_timestamp'].idxmin(), 'cell_id']
    else:
        runaway_time_sec = None
        runaway_cell = "None"
        
    # Earliest warning time (p > threshold)
    warning_events = df_run_preds[df_run_preds['p'] > threshold]
    if not warning_events.empty:
        warning_time_sec = float(warning_events['ts_timestamp'].min() / 1000.0)
        # Find which cell triggered it first
        warning_cell = warning_events.loc[warning_events['ts_timestamp'].idxmin(), 'cell_id']
    else:
        warning_time_sec = None
        warning_cell = "None"
        
    # Lead time calculation
    lead_time = None
    if runaway_time_sec is not None and warning_time_sec is not None:
        lead_time = runaway_time_sec - warning_time_sec
        
    return {
        'max_p': max_p,
        'warning_time': warning_time_sec,
        'warning_cell': warning_cell,
        'runaway_time': runaway_time_sec,
        'runaway_cell': runaway_cell,
        'severity_class': severity_class,
        'actual_outcome': actual_outcome,
        'runaway_count': runaway_count,
        'lead_time': lead_time
    }
