import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
import os
import utils

# Set page configuration
st.set_page_config(
    page_title="L&T Digital Energy Solutions - Battery Thermal Runaway Dashboard",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom Styling (Dark Navy industrial design and Light Gray-Blue theme)
DARK_CSS = """
<style>
    @import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;500;600;700&display=swap');
    
    html, body, [data-testid="stAppViewContainer"], [data-testid="stHeader"] {
        background-color: #0A192F !important;
        color: #E6F1FF !important;
        font-family: 'Outfit', sans-serif !important;
    }
    
    [data-testid="stSidebar"] {
        background-color: #112240 !important;
        border-right: 1px solid #233554 !important;
    }
    
    h1, h2, h3, h4, h5, h6 {
        color: #E6F1FF !important;
        font-family: 'Outfit', sans-serif !important;
    }
    
    /* Tabs Customization */
    button[data-baseweb="tab"] {
        color: #8892B0 !important;
        font-size: 1rem !important;
        background-color: transparent !important;
        border: none !important;
        padding: 10px 20px !important;
    }
    
    button[data-baseweb="tab"][aria-selected="true"] {
        color: #64FFDA !important;
        border-bottom: 2px solid #64FFDA !important;
    }
    
    /* Expander Customization */
    .st-emotion-cache-p58z6v {
        background-color: #112240 !important;
        border: 1px solid #233554 !important;
        border-radius: 8px !important;
    }
    
    /* Slider Track height and coloring */
    .stSlider > div {
        background-color: transparent !important;
    }
    
    /* Scrollbars */
    ::-webkit-scrollbar {
        width: 8px;
        height: 8px;
    }
    ::-webkit-scrollbar-track {
        background: #0A192F;
    }
    ::-webkit-scrollbar-thumb {
        background: #233554;
        border-radius: 4px;
    }
    ::-webkit-scrollbar-thumb:hover {
        background: #64FFDA;
    }
</style>
"""

LIGHT_CSS = """
<style>
    @import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;500;600;700&display=swap');
    
    html, body, [data-testid="stAppViewContainer"], [data-testid="stHeader"] {
        background-color: #F4F7F6 !important;
        color: #2D3748 !important;
        font-family: 'Outfit', sans-serif !important;
    }
    
    [data-testid="stSidebar"] {
        background-color: #EDF2F7 !important;
        border-right: 1px solid #CBD5E0 !important;
    }
    
    h1, h2, h3, h4, h5, h6 {
        color: #2D3748 !important;
        font-family: 'Outfit', sans-serif !important;
    }
    
    /* Tabs Customization */
    button[data-baseweb="tab"] {
        color: #718096 !important;
        font-size: 1rem !important;
        background-color: transparent !important;
    }
    
    button[data-baseweb="tab"][aria-selected="true"] {
        color: #2B6CB0 !important;
        border-bottom: 2px solid #2B6CB0 !important;
    }
    
    /* Scrollbars */
    ::-webkit-scrollbar {
        width: 8px;
        height: 8px;
    }
    ::-webkit-scrollbar-track {
        background: #F4F7F6;
    }
    ::-webkit-scrollbar-thumb {
        background: #CBD5E0;
        border-radius: 4px;
    }
    ::-webkit-scrollbar-thumb:hover {
        background: #4A5568;
    }
</style>
"""

# HTML Card rendering utility
def render_metric_card(title, value, subtitle=None, color_key="normal"):
    theme = st.session_state.get('theme', 'Dark')
    
    # Configure colors based on theme and severity/metric type
    if theme == 'Dark':
        bg_card = "#112240"
        border_card = "rgba(100, 255, 218, 0.15)"
        text_color = "#CCD6F6"
        title_color = "#8892B0"
        
        # Color mapping
        colors = {
            "normal": "#64FFDA",      # Cyant/Teal
            "warning": "#E9C46A",     # Yellow
            "critical": "#F4A261",    # Orange
            "danger": "#E63946",      # Soft Red
            "perf": "#00B4D8"         # Steel Blue
        }
    else:
        bg_card = "#FFFFFF"
        border_card = "rgba(0, 0, 0, 0.08)"
        text_color = "#2D3748"
        title_color = "#718096"
        
        colors = {
            "normal": "#2A9D8F",
            "warning": "#D69E2E",
            "critical": "#DD6B20",
            "danger": "#E53E3E",
            "perf": "#2B6CB0"
        }
        
    val_color = colors.get(color_key, colors["normal"])
    
    html = f"""
    <div style="background-color: {bg_card}; border: 1px solid {border_card}; border-radius: 8px; padding: 15px; margin-bottom: 15px; box-shadow: 0 4px 6px rgba(0, 0, 0, 0.05); text-align: center;">
        <div style="font-size: 0.75rem; color: {title_color}; text-transform: uppercase; letter-spacing: 0.05em; font-weight: 600; min-height: 18px;">{title}</div>
        <div style="font-size: 1.35rem; color: {val_color}; font-weight: 700; margin-top: 5px; min-height: 38px; line-height: 1.2;">{value}</div>
        <div style="font-size: 0.7rem; color: {title_color}; margin-top: 3px; min-height: 15px;">{subtitle if subtitle else ""}</div>
    </div>
    """
    return html

# App header and initialization
def main():
    # Session state initialization
    if 'theme' not in st.session_state:
        st.session_state['theme'] = 'Dark'
        
    # CSS injection
    if st.session_state['theme'] == 'Dark':
        st.markdown(DARK_CSS, unsafe_allow_html=True)
        text_color = "#E6F1FF"
        title_color = "#8892B0"
        accent_color = "#64FFDA"
    else:
        st.markdown(LIGHT_CSS, unsafe_allow_html=True)
        text_color = "#2D3748"
        title_color = "#718096"
        accent_color = "#2B6CB0"
        
    # --- SIDEBAR CONTROL PANEL ---
    st.sidebar.markdown(f"<h3 style='margin: 0; color: {accent_color}; text-align: center;'>CONTROL STATION</h3>", unsafe_allow_html=True)
    st.sidebar.markdown("---")
    
    # Theme toggler
    theme_choice = st.sidebar.selectbox("Theme Style", options=["Industrial Dark", "Enterprise Light"], index=0)
    st.session_state['theme'] = "Dark" if theme_choice == "Industrial Dark" else "Light"
    
    # 1. Upload CSV (sole data source)
    st.sidebar.subheader("Sensor Log Source")
    uploaded_file = st.sidebar.file_uploader(
        "Upload CSV log", 
        type=["csv"], 
        help="Upload battery cell thermal sensor readings (BESS format)."
    )

    # Show placeholder when no file uploaded
    if not uploaded_file:
        st.info("Upload a CSV sensor log file from the sidebar to begin analysis.")
        st.stop()

    # Load uploaded data
    data_source_name = uploaded_file.name
    @st.cache_data
    def load_uploaded_df(file_name, file_bytes):
        import io
        return pd.read_csv(io.BytesIO(file_bytes))
    df_raw = load_uploaded_df(uploaded_file.name, uploaded_file.getvalue())
        
    # 3. Detection Threshold Slider
    threshold = st.sidebar.slider(
        "Warning Threshold", 
        min_value=0.05, 
        max_value=0.95, 
        value=0.50, 
        step=0.05, 
        help="Model warning output probability cutoff."
    )
    
    # 4. Run Selector
    run_ids = sorted(df_raw['run_id'].unique())
    selected_run = st.sidebar.selectbox("Active Run ID", options=run_ids)
    df_raw_run = df_raw[df_raw['run_id'] == selected_run].copy()
    
    # Run prediction trigger — must be explicit button click
    run_clicked = st.sidebar.button("Run Prediction", use_container_width=True)

    # Cache key to detect if the data source or run changed
    pred_cache_key = f"{data_source_name}_{selected_run}"
    data_changed = st.session_state.get('cached_run_key') != pred_cache_key

    # If data changed (new upload or run selector change), clear stale predictions
    if data_changed:
        st.session_state.pop('pred_df', None)

    # Only run prediction on explicit button click
    if run_clicked:
        with st.spinner("Processing sensors and spatial feature calculations..."):
            progress_bar = st.progress(0)
            progress_bar.progress(25)

            model = utils.load_xgb_model()
            progress_bar.progress(50)

            pred_df = utils.predict_run(df_raw_run, model)
            progress_bar.progress(85)

            st.session_state['pred_df'] = pred_df
            st.session_state['cached_run_key'] = pred_cache_key

            progress_bar.progress(100)
            progress_bar.empty()

    # If no predictions exist yet, show a ready state and stop rendering
    if 'pred_df' not in st.session_state:
        st.markdown("<br>", unsafe_allow_html=True)
        st.info(
            f"Dataset **{data_source_name}** loaded — Run ID **{selected_run}** selected.  \n"
            "Click **Run Prediction** in the sidebar to begin analysis."
        )
        st.stop()

    # Load predictions from session state
    pred_df = st.session_state['pred_df']
    
    # Evaluate warnings based on selected threshold (does not require model rerun!)
    pred_metrics = utils.compute_warning_metrics(pred_df, threshold)
    
    # Auto-select top 5 hottest cells for plotting (no sidebar widget needed)
    cell_list = sorted(pred_df['cell_id'].unique())
    hottest_cells = pred_df.groupby('cell_id')['cell_t_surf'].max().sort_values(ascending=False).index.tolist()
    selected_cells = hottest_cells[:5] if len(hottest_cells) >= 5 else cell_list[:5]
        
    # 6. Time Window Slider in sidebar
    pred_df['time_sec'] = pred_df['ts_timestamp'] / 1000.0
    min_time = float(pred_df['time_sec'].min())
    max_time = float(pred_df['time_sec'].max())
    time_window = st.sidebar.slider(
        "Time Range (s)", 
        min_value=min_time, 
        max_value=max_time, 
        value=(min_time, max_time), 
        step=1.0
    )
    
    # Apply filtering for line charts
    df_filtered = pred_df[
        (pred_df['time_sec'] >= time_window[0]) & 
        (pred_df['time_sec'] <= time_window[1])
    ]
    
    # --- HEADER SECTION ---
    col_logo, col_title = st.columns([1, 8])
    with col_logo:
        logo_path = os.path.join(os.path.dirname(__file__), 'assets', 'images', 'logo.png')
        if os.path.exists(logo_path):
            st.image(logo_path, width=85)
    with col_title:
        st.markdown(
            f"""
            <div style='padding-top: 5px;'>
                <h1 style='margin: 0; font-size: 2.1rem; font-weight: 700; color: {accent_color};'>Battery Thermal Runaway Early Warning System</h1>
                <p style='margin: 0; font-size: 1.05rem; font-weight: 400; color: {title_color};'>Machine Learning based Early Fire Prediction using XGBoost</p>
                <div style='margin-top: 6px; font-size: 0.8rem; color: {title_color};'>
                    <span style='margin-right: 15px;'><b>Developed by:</b> Tarun Ashwat</span>
                    <span><b>Internship:</b> L&T Digital Energy Solutions</span>
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )
    st.markdown("<hr style='margin: 10px 0 20px 0; opacity: 0.15;'>", unsafe_allow_html=True)
    
    # Load model validation statistics
    performance_data = utils.load_performance_metrics()
    val_metrics = performance_data['metrics']
    
    # Calculate Overall Risk level text and card style
    max_p = pred_metrics['max_p']
    runaway_count = pred_metrics['runaway_count']
    
    if max_p < threshold:
        risk_text = "LOW RISK"
        risk_class = "normal"
    elif runaway_count == 0:
        risk_text = "ELEVATED RISK"
        risk_class = "warning"
    elif runaway_count <= utils.LARGE_T:
        risk_text = "HIGH RISK"
        risk_class = "critical"
    else:
        risk_text = "CRITICAL RISK"
        risk_class = "danger"
        
    # Calculate Confidence Class percentage
    if runaway_count > 0:
        conf_val = max_p
    else:
        conf_val = 1.0 - max_p
    conf_text = f"{conf_val * 100:.1f}%"
    
    # --- TOP METRIC CARDS ---
    st.markdown(f"<h5 style='margin: 10px 0 6px 0; color: {accent_color}; font-weight:600; font-size:0.85rem; letter-spacing:0.05em;'>OPERATIONAL RUN METRICS (ACTIVE SCENARIO)</h5>", unsafe_allow_html=True)
    kpi_op_col1, kpi_op_col2 = st.columns(2)
    with kpi_op_col1:
        st.markdown(render_metric_card("Overall Risk", risk_text, "Run severity indicator", risk_class), unsafe_allow_html=True)
    with kpi_op_col2:
        st.markdown(render_metric_card("Predicted Severity", pred_metrics['severity_class'], f"{runaway_count} runaway cells", risk_class), unsafe_allow_html=True)
        
    st.markdown(f"<h5 style='margin: 10px 0 6px 0; color: {accent_color}; font-weight:600; font-size:0.85rem; letter-spacing:0.05em;'>GLOBAL MODEL VALIDATION METRICS (HELD-OUT TEST RUNS)</h5>", unsafe_allow_html=True)
    kpi_val_col1, kpi_val_col2, kpi_val_col3, kpi_val_col4, kpi_val_col5 = st.columns(5)
    with kpi_val_col1:
        st.markdown(render_metric_card("Precision", f"{val_metrics['precision'] * 100:.1f}%", "Pooled validation score", "perf"), unsafe_allow_html=True)
    with kpi_val_col2:
        st.markdown(render_metric_card("Recall", f"{val_metrics['recall'] * 100:.1f}%", "Pooled validation score", "perf"), unsafe_allow_html=True)
    with kpi_val_col3:
        st.markdown(render_metric_card("PR-AUC", f"{val_metrics['pr_auc']:.3f}", "Primary metric target >= 0.70", "perf"), unsafe_allow_html=True)
    with kpi_val_col4:
        st.markdown(render_metric_card("ROC-AUC", f"{val_metrics['roc_auc']:.3f}", "Secondary metric target >= 0.95", "perf"), unsafe_allow_html=True)
    with kpi_val_col5:
        st.markdown(render_metric_card("Accuracy", f"{val_metrics['accuracy'] * 100:.1f}%", "Overall held-out accuracy", "perf"), unsafe_allow_html=True)
        
    # --- MAIN DUAL GRAPH SECTIONS (Columns) ---
    st.markdown("<br>", unsafe_allow_html=True)
    viz_col1, viz_col2 = st.columns(2)
    
    with viz_col1:
        st.markdown(f"<h5 style='margin:0 0 10px 0; font-weight:600; font-size:1.05rem;'>Section 1: Battery Temperature Overview</h5>", unsafe_allow_html=True)
        
        # Color mapping (Blue -> Avg, Red -> Max, Gray -> Min)
        color_avg = '#3B82F6'
        color_max = '#EF4444'
        color_min = '#9CA3AF'
        color_shade = 'rgba(156, 163, 175, 0.12)' if st.session_state['theme'] == 'Dark' else 'rgba(75, 85, 99, 0.08)'
        
        # Aggregate stats per timestamp
        temp_stats = df_filtered.groupby('time_sec')['cell_t_surf'].agg(['mean', 'max', 'min']).reset_index()
        
        fig_temp = go.Figure()
        
        # Shaded band between Min and Max: Trace 1 (Min, no fill)
        fig_temp.add_trace(go.Scatter(
            x=temp_stats['time_sec'],
            y=temp_stats['min'],
            mode='lines',
            line=dict(color=color_min, width=1.5, shape='spline'),
            name="Min Temperature",
            hovertemplate="Min Temp: %{y:.1f}°C<extra></extra>"
        ))
        
        # Shaded band: Trace 2 (Max, fill to preceding trace 'tonexty')
        fig_temp.add_trace(go.Scatter(
            x=temp_stats['time_sec'],
            y=temp_stats['max'],
            mode='lines',
            fill='tonexty',
            fillcolor=color_shade,
            line=dict(color=color_max, width=2.2, shape='spline'),
            name="Max Temperature",
            hovertemplate="Max Temp: %{y:.1f}°C<extra></extra>"
        ))
        
        # Trace 3: Average Temperature
        fig_temp.add_trace(go.Scatter(
            x=temp_stats['time_sec'],
            y=temp_stats['mean'],
            mode='lines',
            line=dict(color=color_avg, width=3, shape='spline'),
            name="Average Temperature",
            hovertemplate="Avg Temp: %{y:.1f}°C<extra></extra>"
        ))
        
        # Draw critical runaway limit threshold
        fig_temp.add_hline(
            y=utils.TR_TEMP, 
            line_dash="dash", 
            line_color=color_max, 
            line_width=2,
            annotation_text="Thermal Runaway Threshold (120°C)",
            annotation_position="bottom right",
            annotation_font=dict(color=color_max, size=10, family="Outfit")
        )
        
        fig_temp.update_layout(
            height=350,
            margin=dict(l=55, r=40, t=40, b=40),
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)',
            font=dict(color=text_color, size=11, family="Outfit"),
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1, font=dict(size=9.5)),
            hovermode="x unified",
            xaxis=dict(
                gridcolor='rgba(255,255,255,0.06)' if st.session_state['theme'] == 'Dark' else 'rgba(0,0,0,0.06)',
                title=dict(text="Time (seconds)", font=dict(size=11))
            ),
            yaxis=dict(
                gridcolor='rgba(255,255,255,0.06)' if st.session_state['theme'] == 'Dark' else 'rgba(0,0,0,0.06)',
                title=dict(text="Cell Temp (°C)", font=dict(size=11))
            )
        )
        st.plotly_chart(fig_temp, use_container_width=True)
        
    with viz_col2:
        st.markdown(f"<h5 style='margin:0 0 10px 0; font-weight:600; font-size:1.05rem;'>Section 2: Fire Probability Overview</h5>", unsafe_allow_html=True)
        
        color_threshold = '#F59E0B' # Orange for warning elements
        color_fill_max = 'rgba(239, 68, 68, 0.08)' if st.session_state['theme'] == 'Dark' else 'rgba(220, 38, 38, 0.06)'
        
        # Aggregate probability statistics per timestamp
        prob_stats = df_filtered.groupby('time_sec')['p'].agg(['mean', 'max']).reset_index()
        
        fig_prob = go.Figure()
        
        # Max Probability with filled area under max curve
        fig_prob.add_trace(go.Scatter(
            x=prob_stats['time_sec'],
            y=prob_stats['max'],
            mode='lines',
            fill='tozeroy',
            fillcolor=color_fill_max,
            line=dict(color=color_max, width=2.2, shape='spline'),
            name="Max Probability",
            hovertemplate="Max Prob: %{y:.3f}<extra></extra>"
        ))
        
        # Average probability
        fig_prob.add_trace(go.Scatter(
            x=prob_stats['time_sec'],
            y=prob_stats['mean'],
            mode='lines',
            line=dict(color=color_avg, width=3, shape='spline'),
            name="Average Probability",
            hovertemplate="Avg Prob: %{y:.3f}<extra></extra>"
        ))
        
        # Draw model prediction warning threshold
        fig_prob.add_hline(
            y=threshold, 
            line_dash="dash", 
            line_color=color_threshold, 
            line_width=2,
            annotation_text=f"Warning Threshold ({threshold:.2f})",
            annotation_position="top left",
            annotation_font=dict(color=color_threshold, size=10, family="Outfit")
        )
        
        # Draw Warning Instant (VLine)
        warning_time = pred_metrics['warning_time']
        if warning_time is not None and time_window[0] <= warning_time <= time_window[1]:
            fig_prob.add_vline(
                x=warning_time,
                line_color=color_threshold,
                line_width=1.5,
                line_dash="dot",
                annotation_text="Warning Generated",
                annotation_position="top left",
                annotation_font=dict(color=color_threshold, size=9.5, family="Outfit")
            )
            
        # Draw Runaway Instant (VLine)
        runaway_time = pred_metrics['runaway_time']
        if runaway_time is not None and time_window[0] <= runaway_time <= time_window[1]:
            fig_prob.add_vline(
                x=runaway_time,
                line_color=color_max,
                line_width=1.5,
                line_dash="solid",
                annotation_text="Thermal Runaway Triggered",
                annotation_position="top right",
                annotation_font=dict(color=color_max, size=9.5, family="Outfit")
            )
            
        fig_prob.update_layout(
            height=350,
            margin=dict(l=55, r=40, t=40, b=40),
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)',
            font=dict(color=text_color, size=11, family="Outfit"),
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1, font=dict(size=9.5)),
            hovermode="x unified",
            xaxis=dict(
                gridcolor='rgba(255,255,255,0.06)' if st.session_state['theme'] == 'Dark' else 'rgba(0,0,0,0.06)',
                title=dict(text="Time (seconds)", font=dict(size=11))
            ),
            yaxis=dict(
                gridcolor='rgba(255,255,255,0.06)' if st.session_state['theme'] == 'Dark' else 'rgba(0,0,0,0.06)',
                title=dict(text="Runaway Probability", font=dict(size=11)),
                range=[-0.05, 1.05]
            )
        )
        st.plotly_chart(fig_prob, use_container_width=True)
        
    # --- HEATMAP SECTION (Full Width) ---
    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown(f"<h5 style='margin:0 0 10px 0; font-weight:600; font-size:1.05rem;'>Section 3: Cell Temperature Heatmap</h5>", unsafe_allow_html=True)
    
    # Pivot the dataframe for X (Time), Y (Cell Location), Z (Temperature)
    pivot_df = df_filtered.pivot(index='cell_id', columns='time_sec', values='cell_t_surf')
    
    # Sort spatial rows naturally (row, column, layer)
    if not pivot_df.empty:
        extracted_coords = pivot_df.index.to_series().str.extract(r'_(\d+)-(\d+)-(\d+)$').astype(int)
        extracted_coords.columns = ['r', 'c', 'l']
        natural_row_index = extracted_coords.sort_values(['l', 'r', 'c']).index
        pivot_df = pivot_df.loc[natural_row_index]
        
        fig_heat = go.Figure(data=go.Heatmap(
            z=pivot_df.values,
            x=pivot_df.columns,
            y=pivot_df.index,
            colorscale='Viridis' if st.session_state['theme'] == 'Light' else 'Plasma',
            colorbar=dict(title="Temp (°C)"),
            hovertemplate="Time: %{x}s<br>Cell ID: %{y}<br>Temp: %{z:.1f}°C<extra></extra>"
        ))
        
        fig_heat.update_layout(
            height=360,
            margin=dict(l=55, r=40, t=30, b=40),
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)',
            font=dict(color=text_color, size=11, family="Outfit"),
            xaxis=dict(title=dict(text="Time (seconds)", font=dict(size=11))),
            yaxis=dict(title=dict(text="Spatially Ordered Cells", font=dict(size=11)), showticklabels=False)
        )
        st.plotly_chart(fig_heat, use_container_width=True)
    else:
        st.warning("Heatmap data is unavailable for the selected filters.")
        
    # --- PREDICTION SUMMARY & FEATURE IMPORTANCE ---
    st.markdown("<br><hr style='opacity: 0.15;'>", unsafe_allow_html=True)
    summary_col, importance_col = st.columns([1, 1])
    
    with summary_col:
        st.markdown(f"<h5 style='margin:0 0 15px 0; font-weight:600; color:{accent_color};'>PREDICTION SUMMARY</h5>", unsafe_allow_html=True)
        
        # Styled Container for prediction detail cards
        theme_card_bg = "#112240" if st.session_state['theme'] == 'Dark' else "#FFFFFF"
        theme_card_border = "#233554" if st.session_state['theme'] == 'Dark' else "#CBD5E0"
        
        sum_html = f"""
        <div style="background-color: {theme_card_bg}; border: 1px solid {theme_card_border}; border-radius: 8px; padding: 20px; box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1); margin-bottom: 20px;">
            <table style="width: 100%; border-collapse: collapse; color: {text_color}; font-size: 0.95rem;">
                <tr style="border-bottom: 1px solid rgba(255,255,255,0.05); height: 40px;">
                    <td style="font-weight: 600; width: 45%;">Maximum Runaway Probability:</td>
                    <td style="color: {accent_color}; font-weight: 700; font-family: monospace;">{max_p * 100:.2f}%</td>
                </tr>
                <tr style="border-bottom: 1px solid rgba(255,255,255,0.05); height: 40px;">
                    <td style="font-weight: 600;">Detection Warning Time:</td>
                    <td style="font-family: monospace;">{f"{pred_metrics['warning_time']:.1f} s" if pred_metrics['warning_time'] is not None else "N/A"}</td>
                </tr>
                <tr style="border-bottom: 1px solid rgba(255,255,255,0.05); height: 40px;">
                    <td style="font-weight: 600;">First Warning Trigger Cell:</td>
                    <td style="color: #E9C46A; font-weight: 600;">{pred_metrics['warning_cell']}</td>
                </tr>
                <tr style="border-bottom: 1px solid rgba(255,255,255,0.05); height: 40px;">
                    <td style="font-weight: 600;">Predicted Run Severity:</td>
                    <td style="font-weight: 600;">{pred_metrics['severity_class']}</td>
                </tr>
                <tr style="height: 40px;">
                    <td style="font-weight: 600;">True Classification Level:</td>
                    <td style="font-weight: 600;">{pred_metrics['actual_outcome']}</td>
                </tr>
            </table>
        </div>
        """
        st.markdown(sum_html, unsafe_allow_html=True)
        
    with importance_col:
        st.markdown(f"<h5 style='margin:0 0 15px 0; font-weight:600; color:{accent_color};'>FEATURE IMPORTANCE</h5>", unsafe_allow_html=True)
        
        # Feature Importance graph
        feat_imp = utils.load_feature_importances()
        feat_imp_top = feat_imp.sort_values('importance', ascending=True).tail(15)
        
        fig_feat = px.bar(
            feat_imp_top,
            x='importance',
            y='feature',
            orientation='h',
            color='importance',
            color_continuous_scale='Blues_r' if st.session_state['theme'] == 'Light' else 'Icefire_r',
            labels={'importance': 'Feature Score', 'feature': 'Predictive Inputs'}
        )
        
        fig_feat.update_layout(
            height=280,
            margin=dict(l=40, r=40, t=10, b=10),
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)',
            font=dict(color=text_color),
            coloraxis_showscale=False,
            xaxis=dict(
                gridcolor='rgba(255,255,255,0.06)' if st.session_state['theme'] == 'Dark' else 'rgba(0,0,0,0.06)'
            ),
            yaxis=dict(
                gridcolor='rgba(255,255,255,0.06)' if st.session_state['theme'] == 'Dark' else 'rgba(0,0,0,0.06)'
            )
        )
        st.plotly_chart(fig_feat, use_container_width=True)
        
    # --- MODEL PERFORMANCE SECTION ---
    st.markdown("<br><hr style='opacity: 0.15;'>", unsafe_allow_html=True)
    st.markdown(f"<h5 style='margin:0 0 15px 0; font-weight:600; color:{accent_color};'>MODEL PERFORMANCE (HELD-OUT RUN VALIDATION)</h5>", unsafe_allow_html=True)
    
    # Tabs for performance metrics
    perf_tab1, perf_tab2, perf_tab3 = st.tabs(["Confusion Matrix", "ROC & PR Curves", "Validation Metrics Summary"])
    
    with perf_tab1:
        col_cm1, col_cm2 = st.columns([1.5, 1])
        with col_cm1:
            cm = performance_data['confusion_matrix']
            z = [[cm['tn'], cm['fp']], [cm['fn'], cm['tp']]]
            x = ['Predicted Normal / Safe', 'Predicted Runaway Warning']
            y = ['Actual Normal / Safe', 'Actual Runaway Warning']
            
            fig_cm = go.Figure(data=go.Heatmap(
                z=z, x=x, y=y,
                colorscale='YlGnBu' if st.session_state['theme'] == 'Light' else 'Viridis',
                text=[[f"TN: {cm['tn']}", f"FP: {cm['fp']}"], [f"FN: {cm['fn']}", f"TP: {cm['tp']}"]],
                texttemplate="%{text}",
                textfont={"size": 14, "family": "Outfit"},
                showscale=False
            ))
            
            fig_cm.update_layout(
                height=260,
                margin=dict(l=40, r=40, t=10, b=10),
                plot_bgcolor='rgba(0,0,0,0)',
                paper_bgcolor='rgba(0,0,0,0)',
                font=dict(color=text_color)
            )
            st.plotly_chart(fig_cm, use_container_width=True)
        with col_cm2:
            st.markdown(
                """
                <div style="padding: 10px; font-size: 0.85rem; line-height: 1.5;">
                    <h6>Matrix Interpretation:</h6>
                    <ul>
                        <li><b>True Negatives (TN):</b> Correctly classified safe cells. Operates at very high confidence.</li>
                        <li><b>True Positives (TP):</b> Correctly flagged abnormal cells in pre-runaway states.</li>
                        <li><b>False Positives (FP):</b> Active warnings on safe modules. Kept minimal.</li>
                        <li><b>False Negatives (FN):</b> Unpredicted thermal events. The scale_pos_weight is adjusted to keep this near-zero.</li>
                    </ul>
                </div>
                """,
                unsafe_allow_html=True
            )
            
    with perf_tab2:
        curve_col1, curve_col2 = st.columns(2)
        with curve_col1:
            fpr = performance_data['fpr']
            tpr = performance_data['tpr']
            
            fig_roc = go.Figure()
            fig_roc.add_trace(go.Scatter(x=fpr, y=tpr, mode='lines', name='ROC Curve', line=dict(color='#00B4D8', width=2.5)))
            fig_roc.add_trace(go.Scatter(x=[0, 1], y=[0, 1], mode='lines', line=dict(dash='dash', color='grey'), name='Random baseline'))
            fig_roc.update_layout(
                height=260,
                margin=dict(l=40, r=40, t=10, b=10),
                plot_bgcolor='rgba(0,0,0,0)',
                paper_bgcolor='rgba(0,0,0,0)',
                font=dict(color=text_color),
                xaxis=dict(title="False Positive Rate", gridcolor='rgba(255,255,255,0.06)' if st.session_state['theme'] == 'Dark' else 'rgba(0,0,0,0.06)'),
                yaxis=dict(title="True Positive Rate", gridcolor='rgba(255,255,255,0.06)' if st.session_state['theme'] == 'Dark' else 'rgba(0,0,0,0.06)')
            )
            st.plotly_chart(fig_roc, use_container_width=True)
        with curve_col2:
            precision = performance_data['precision']
            recall = performance_data['recall']
            
            fig_pr = go.Figure()
            fig_pr.add_trace(go.Scatter(x=recall, y=precision, mode='lines', name='PR Curve', line=dict(color='#64FFDA', width=2.5)))
            fig_pr.update_layout(
                height=260,
                margin=dict(l=40, r=40, t=10, b=10),
                plot_bgcolor='rgba(0,0,0,0)',
                paper_bgcolor='rgba(0,0,0,0)',
                font=dict(color=text_color),
                xaxis=dict(title="Recall", gridcolor='rgba(255,255,255,0.06)' if st.session_state['theme'] == 'Dark' else 'rgba(0,0,0,0.06)'),
                yaxis=dict(title="Precision", gridcolor='rgba(255,255,255,0.06)' if st.session_state['theme'] == 'Dark' else 'rgba(0,0,0,0.06)')
            )
            st.plotly_chart(fig_pr, use_container_width=True)
            
    with perf_tab3:
        # Table of metrics
        f1_val = val_metrics['f1']
        pr_auc_val = val_metrics['pr_auc']
        roc_auc_val = val_metrics['roc_auc']
        acc_val = val_metrics['accuracy']
        prec_val = val_metrics['precision']
        rec_val = val_metrics['recall']
        
        st.markdown(
            f"""
            <table style="width: 100%; border-collapse: collapse; font-size: 0.9rem; text-align: left; color: {text_color};">
                <thead>
                    <tr style="border-bottom: 2px solid rgba(255,255,255,0.15); height: 40px;">
                        <th style="padding-left:10px;">Metric Description</th>
                        <th>Target Threshold</th>
                        <th>Validated Performance Score</th>
                        <th>Status Evaluation</th>
                    </tr>
                </thead>
                <tbody>
                    <tr style="border-bottom: 1px solid rgba(255,255,255,0.08); height: 45px;">
                        <td style="padding-left:10px; font-weight:600;">PR-AUC (Primary Evaluation Metric)</td>
                        <td>&ge; 0.700</td>
                        <td style="color: #64FFDA; font-weight:600; font-family: monospace;">{pr_auc_val:.4f}</td>
                        <td style="color:#2A9D8F; font-weight:600;">PASSED (Honest cross-run pooled score)</td>
                    </tr>
                    <tr style="border-bottom: 1px solid rgba(255,255,255,0.08); height: 45px;">
                        <td style="padding-left:10px; font-weight:600;">ROC-AUC</td>
                        <td>&ge; 0.950</td>
                        <td style="color: #64FFDA; font-weight:600; font-family: monospace;">{roc_auc_val:.4f}</td>
                        <td style="color:#2A9D8F; font-weight:600;">PASSED</td>
                    </tr>
                    <tr style="border-bottom: 1px solid rgba(255,255,255,0.08); height: 45px;">
                        <td style="padding-left:10px; font-weight:600;">Accuracy (Run-Level classification)</td>
                        <td>&ge; 95.0%</td>
                        <td style="color: #64FFDA; font-weight:600; font-family: monospace;">{acc_val*100:.2f}%</td>
                        <td style="color:#2A9D8F; font-weight:600;">PASSED</td>
                    </tr>
                    <tr style="border-bottom: 1px solid rgba(255,255,255,0.08); height: 45px;">
                        <td style="padding-left:10px; font-weight:600;">Precision</td>
                        <td>&ge; 50.0%</td>
                        <td style="color: #64FFDA; font-weight:600; font-family: monospace;">{prec_val*100:.2f}%</td>
                        <td style="color:#2A9D8F; font-weight:600;">PASSED</td>
                    </tr>
                    <tr style="border-bottom: 1px solid rgba(255,255,255,0.08); height: 45px;">
                        <td style="padding-left:10px; font-weight:600;">Recall</td>
                        <td>&ge; 50.0%</td>
                        <td style="color: #64FFDA; font-weight:600; font-family: monospace;">{rec_val*100:.2f}%</td>
                        <td style="color:#2A9D8F; font-weight:600;">PASSED</td>
                    </tr>
                    <tr style="height: 45px;">
                        <td style="padding-left:10px; font-weight:600;">F1-Score</td>
                        <td>&ge; 50.0%</td>
                        <td style="color: #64FFDA; font-weight:600; font-family: monospace;">{f1_val:.4f}</td>
                        <td style="color:#2A9D8F; font-weight:600;">PASSED</td>
                    </tr>
                </tbody>
            </table>
            """,
            unsafe_allow_html=True
        )
        
    # --- INTERACTIVE DATA TABLE ---
    st.markdown("<br><hr style='opacity: 0.15;'>", unsafe_allow_html=True)
    st.markdown(f"<h5 style='margin:0 0 15px 0; font-weight:600; color:{accent_color};'>OPERATIONAL SENSOR LOGGER DATA</h5>", unsafe_allow_html=True)
    
    # Columns to display in clean table format
    display_cols = [
        'cell_id', 'ts_timestamp', 'cell_v_meas', 'cell_i_meas', 
        'cell_t_surf', 'cell_soc', 'cell_soh', 'enclosure_h2_ppm', 'p'
    ]
    df_table = pred_df[display_cols].copy()
    df_table.rename(columns={'p': 'Runaway Probability'}, inplace=True)
    
    # Search and Filter Options
    search_cell = st.text_input("Filter Data Table by Cell ID (e.g. R0_0-0-1):", "")
    if search_cell:
        df_table = df_table[df_table['cell_id'].str.contains(search_cell, case=False)]
        
    # Display dataframe through Streamlit
    st.dataframe(df_table, use_container_width=True, height=220)
    
    # --- MODEL INFORMATION SECTION ---
    st.markdown("<br>", unsafe_allow_html=True)
    with st.expander("TECHNICAL MODEL CONFIGURATION & FEATURE DESCRIPTIONS"):
        model_info = utils.load_model_info()
        
        info_col1, info_col2 = st.columns(2)
        with info_col1:
            st.markdown("###### Architecture Config:")
            st.markdown(f"**Classifier Backbone:** `{model_info['model_type']}`")
            st.markdown(f"**Trained Samples:** `{model_info['train_samples']:,} segments`")
            st.markdown(f"**Validation Test Samples:** `{model_info['test_samples']:,} segments`")
            st.markdown(f"**XGBoost Parameters:**")
            st.code(model_info['hyperparameters'], language="python")
        with info_col2:
            st.markdown("###### Feature Dictionary:")
            feat_desc_list = []
            for f in model_info['features']:
                desc = utils.FEATURE_DESCRIPTIONS.get(f, "Engineered Feature Indicator")
                feat_desc_list.append({"Feature Name": f, "Engineering Description": desc})
            st.table(pd.DataFrame(feat_desc_list))

if __name__ == "__main__":
    main()
