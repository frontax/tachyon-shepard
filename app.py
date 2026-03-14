import streamlit as st
import pandas as pd
from src.lib.google_sheets import get_climbs
from src.components.map_view import render_map, render_trail_map
from src.components.climb_form import render_form

# Page configuration
st.set_page_config(
    page_title="Mountain Log App",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for premium YAMAP-like look
st.markdown("""
<style>
    /* Global Font */
    html, body, [class*="css"] {
        font-family: 'Noto Sans JP', 'Hiragino Kaku Gothic ProN', 'Meiryo', sans-serif !important;
        color: #2d3748;
    }
    
    /* Main Background & Padding with Dynamic Gradient */
    .stApp {
        background: linear-gradient(-45deg, #f0fdf4, #ffffff, #f8fafc, #e2e8f0);
        background-size: 400% 400%;
        animation: gradientBG 15s ease infinite;
    }
    @keyframes gradientBG {
        0% { background-position: 0% 50%; }
        50% { background-position: 100% 50%; }
        100% { background-position: 0% 50%; }
    }
    
    /* Premium Headers */
    h1, h2, h3, h4, h5, h6 {
        font-weight: 800 !important;
        letter-spacing: 0.05em;
        color: #1a202c;
    }
    
    /* Glassmorphism Card Style for Forms, DataFrames and Containers */
    [data-testid="stForm"], [data-testid="stMetric"], .ag-theme-streamlit, [data-testid="stExpander"] {
        background: rgba(255, 255, 255, 0.7) !important;
        backdrop-filter: blur(12px) !important;
        -webkit-backdrop-filter: blur(12px) !important;
        border-radius: 12px !important;
        border: 1px solid rgba(255, 255, 255, 0.5) !important;
        box-shadow: 0 8px 32px 0 rgba(31, 38, 135, 0.05) !important;
        padding: 1.5rem;
        margin-bottom: 1rem;
        transition: all 0.3s cubic-bezier(0.25, 0.8, 0.25, 1);
    }
    
    [data-testid="stForm"]:hover, [data-testid="stMetric"]:hover {
        transform: translateY(-4px);
        box-shadow: 0 12px 40px 0 rgba(31, 38, 135, 0.1) !important;
        background: rgba(255, 255, 255, 0.85) !important;
    }
    
    /* Styling Metrics (Summary Items) */
    [data-testid="stMetricValue"] {
        font-weight: 800;
        font-size: 1.8rem;
        background: -webkit-linear-gradient(45deg, #00A52B, #0284c7);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
    }
    [data-testid="stMetricLabel"] {
        font-size: 0.95rem;
        color: #4a5568;
        font-weight: 700;
    }
    
    /* Button Micro-animations */
    .stButton>button {
        border-radius: 8px;
        font-weight: bold;
        border: none;
        background: linear-gradient(135deg, #00A52B 0%, #059669 100%);
        color: white;
        padding: 0.6rem 2.5rem;
        box-shadow: 0 4px 6px -1px rgba(0, 165, 43, 0.2), 0 2px 4px -1px rgba(0, 165, 43, 0.1);
        transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
    }
    .stButton>button:hover {
        transform: translateY(-2px) scale(1.02);
        box-shadow: 0 10px 15px -3px rgba(0, 165, 43, 0.3), 0 4px 6px -2px rgba(0, 165, 43, 0.15);
        background: linear-gradient(135deg, #059669 0%, #047857 100%);
        color: white;
    }
    .stButton>button:active {
        transform: translateY(1px) scale(0.98);
        box-shadow: 0 2px 4px rgba(0,165,43,0.2);
    }
    
    /* Sidebar styling - Glassmorphism */
    [data-testid="stSidebar"] {
        background: rgba(255, 255, 255, 0.6) !important;
        backdrop-filter: blur(20px) !important;
        -webkit-backdrop-filter: blur(20px) !important;
        border-right: 1px solid rgba(255, 255, 255, 0.4);
    }
    
    /* Tabs styling enhancements */
    .stTabs [data-baseweb="tab-list"] {
        gap: 2rem;
        border-bottom: 2px solid rgba(0,0,0,0.05);
    }
    .stTabs [data-baseweb="tab"] {
        padding-top: 1rem;
        padding-bottom: 1rem;
        font-weight: bold;
        transition: color 0.2s;
    }
    .stTabs [data-baseweb="tab"]:hover {
        color: #00A52B;
    }
</style>
""", unsafe_allow_html=True)

def main():
    st.title("登山記録ログ")
    
    # Fetch data
    try:
        df = get_climbs()
    except Exception as e:
        st.error(f"データ取得エラー: {e}")
        df = pd.DataFrame()

    # Sidebar
    st.sidebar.title("メニュー")
    mode = st.sidebar.radio("表示モード", ["ダッシュボード", "新規登録"])
    
    st.sidebar.markdown("---")
    
    # Summary Metrics in Sidebar
    total_climbs = 0
    unique_mountains = 0
    
    if df is not None and not df.empty:
        total_climbs = len(df)
        if "山名" in df.columns:
            unique_mountains = df["山名"].nunique()

    st.sidebar.metric("総登山回数", f"{total_climbs} 回")
    st.sidebar.metric("登った山の数", f"{unique_mountains} 座")

    if mode == "ダッシュボード":
        # Tabs for different views
        tab1, tab2 = st.tabs(["リスト表示", "地図表示"])
        
        with tab1:
            st.subheader("登山記録一覧")
            if df is not None and not df.empty:
                # Custom dataframe display
                # Hide explicit lat/lon columns from the table view
                display_cols = [col for col in df.columns if col not in ['緯度', '経度', '緯度経度']]
                
                # Defensive type conversion for display to prevent ArrowInvalid errors
                # (In case cached data is old)
                display_df = df[display_cols].copy()
                if '標高' in display_df.columns:
                    display_df['標高'] = pd.to_numeric(display_df['標高'], errors='coerce').fillna(0).astype(int)

                from st_aggrid import AgGrid, GridOptionsBuilder, GridUpdateMode, JsCode, ColumnsAutoSizeMode
                display_df_with_idx = display_df.reset_index(names=['Original_Index'])
                
                # Add GPX indicator column
                import os
                def check_gpx(idx):
                    return "📍 あり" if os.path.exists(f"data/gpx/{idx}.gpx") else ""
                display_df_with_idx['GPX軌跡'] = display_df_with_idx['Original_Index'].apply(check_gpx)
                
                # Reorder columns to put GPX軌跡 near the front or back
                cols = display_df_with_idx.columns.tolist()
                cols.remove('GPX軌跡')
                cols.append('GPX軌跡') # Insert at the very end
                display_df_with_idx = display_df_with_idx[cols]
                
                gb = GridOptionsBuilder.from_dataframe(display_df_with_idx)
                # Use a default minimum width so columns don't crush on mobile
                gb.configure_default_column(resizable=True, wrapText=True, autoHeight=True, minWidth=120)
                gb.configure_column('Original_Index', hide=True)
                
                # Make text columns flex to fill any remaining empty space on wide screens,
                # but respect their minimum widths on narrow screens
                if '備考' in display_df_with_idx.columns:
                    gb.configure_column('備考', flex=2, minWidth=200)
                if 'URL' in display_df_with_idx.columns:
                    gb.configure_column('URL', flex=1, minWidth=120)
                if '山名' in display_df_with_idx.columns:
                    gb.configure_column('山名', flex=1, minWidth=150)
                if '日付' in display_df_with_idx.columns:
                    gb.configure_column('日付', minWidth=110)
                if 'GPX軌跡' in display_df_with_idx.columns:
                    gb.configure_column('GPX軌跡', minWidth=100)
                    
                gb.configure_selection('single', use_checkbox=False)
                # Removed suppressHorizontalScroll=True to allow mobile scrolling
                
                # Make URL clickable if it exists, avoiding HTML string rendering
                if 'URL' in display_df_with_idx.columns:
                    url_renderer = JsCode('''
                    class UrlCellRenderer {
                      init(params) {
                        this.eGui = document.createElement('span');
                        if (params.value && params.value.trim() !== "") {
                            let link = document.createElement('a');
                            link.href = params.value;
                            link.innerText = params.value;
                            link.target = '_blank';
                            link.style.color = '#00A52B';
                            link.style.textDecoration = 'none';
                            this.eGui.appendChild(link);
                        }
                      }
                      getGui() {
                        return this.eGui;
                      }
                    }
                    ''')
                    gb.configure_column("URL", cellRenderer=url_renderer)
                gridOptions = gb.build()

                grid_response = AgGrid(
                    display_df_with_idx,
                    gridOptions=gridOptions,
                    update_mode=GridUpdateMode.SELECTION_CHANGED,
                    fit_columns_on_grid_load=False, # Crucial: Let it scroll if too wide
                    theme='streamlit',
                    allow_unsafe_jscode=True, # crucial for JsCode to run
                    height=450,
                    custom_css={
                        ".ag-row-hover": {"background-color": "rgba(0,165,43,0.05) !important"},
                        ".ag-row-selected": {"background-color": "rgba(0,165,43,0.15) !important"},
                        ".ag-header-cell-label": {"justify-content": "center !important"},
                        ".ag-header-cell-text": {"text-align": "center"},
                        # Adjust scrollbars for the grid
                        ".ag-body-viewport::-webkit-scrollbar, .ag-body-horizontal-scroll-viewport::-webkit-scrollbar": {"width": "8px", "height": "8px", "background": "transparent"},
                        ".ag-body-viewport::-webkit-scrollbar-thumb, .ag-body-horizontal-scroll-viewport::-webkit-scrollbar-thumb": {"background": "rgba(0,0,0,0.1)", "border-radius": "4px"},
                        ".ag-body-viewport:hover::-webkit-scrollbar-thumb, .ag-body-horizontal-scroll-viewport:hover::-webkit-scrollbar-thumb": {"background": "rgba(0,0,0,0.2)"},
                        ".ag-body-viewport::-webkit-scrollbar-thumb:hover, .ag-body-horizontal-scroll-viewport::-webkit-scrollbar-thumb:hover": {"background": "rgba(0,0,0,0.4)"}
                    }
                )
                
                selected_rows = grid_response['selected_rows']
                
                if selected_rows is not None:
                    sel_list = []
                    if isinstance(selected_rows, pd.DataFrame) and not selected_rows.empty:
                        sel_list = selected_rows.to_dict('records')
                    elif isinstance(selected_rows, list) and len(selected_rows) > 0:
                        sel_list = selected_rows
                        
                    if len(sel_list) > 0:
                        selected_idx = sel_list[0].get('Original_Index')
                        if selected_idx is not None:
                            selected_data = df.iloc[selected_idx]
                            lat = selected_data.get('緯度')
                            lon = selected_data.get('経度')
                            name = selected_data.get('山名', '不明')
                            
                            if pd.notnull(lat) and pd.notnull(lon):
                                # GPX Upload & Persistence Feature
                                import os
                                gpx_path = f"data/gpx/{selected_idx}.gpx"
                        gpx_points = None
                        gpx_duration = None
                        gpx_data = None
                        
                        if os.path.exists(gpx_path):
                            with open(gpx_path, "r", encoding="utf-8") as f:
                                gpx_data = f.read()
                        else:
                            uploaded_file = st.file_uploader("活動記録(GPXファイル)をアップロードして軌跡とコースタイムを表示", type=["gpx"], key=f"gpx_uploader_{selected_idx}")
                            if uploaded_file is not None:
                                gpx_data = uploaded_file.getvalue().decode("utf-8")
                                os.makedirs("data/gpx", exist_ok=True)
                                with open(gpx_path, "w", encoding="utf-8") as f:
                                    f.write(gpx_data)
                                st.success("GPXデータを保存しました！")
                        
                        if gpx_data:
                            try:
                                import gpxpy
                                import pytz
                                gpx = gpxpy.parse(gpx_data)
                                
                                points = []
                                all_details = []
                                start_time = None
                                cumulative_dist = 0.0
                                last_gpx_point = None
                                
                                jst = pytz.timezone('Asia/Tokyo')
                                
                                for track in gpx.tracks:
                                    for segment in track.segments:
                                        for point in segment.points:
                                            # Convert from UTC to JST if tz aware
                                            pt_time = point.time
                                            if pt_time and pt_time.tzinfo is not None:
                                                pt_time = pt_time.astimezone(jst)
                                                
                                            if start_time is None and pt_time is not None:
                                                start_time = pt_time
                                                
                                            if last_gpx_point is not None:
                                                cumulative_dist += point.distance_2d(last_gpx_point)
                                            last_gpx_point = point
                                            
                                            time_str = pt_time.strftime("%H:%M:%S") if pt_time else "-"
                                            elapsed = ""
                                            if start_time and pt_time:
                                                delta = pt_time - start_time
                                                hours, remainder = divmod(delta.seconds, 3600)
                                                minutes, _ = divmod(remainder, 60)
                                                elapsed = f"{hours}h{minutes:02d}m"
                                                
                                            ele = int(point.elevation) if point.elevation else 0
                                            dist_km = cumulative_dist / 1000.0
                                            
                                            # We send all details to frontend for the map
                                            detail_dict = {
                                                "elapsed": elapsed,
                                                "time_str": time_str,
                                                "dist_km": dist_km,
                                                "elevation": ele,
                                                "lat": point.latitude,
                                                "lng": point.longitude,
                                                "time_obj": pt_time
                                            }
                                            all_details.append(detail_dict)
                                
                                table_points = []
                                summary_points = {}
                                
                                if all_details:
                                    last_added_time = None
                                    for i, pt in enumerate(all_details):
                                        # Downsample for table: roughly 10 mins (600 seconds)
                                        # Always include first and last point
                                        if i == 0 or i == len(all_details) - 1:
                                            table_points.append(pt)
                                            last_added_time = pt['time_obj']
                                        elif pt['time_obj'] and last_added_time:
                                            diff = (pt['time_obj'] - last_added_time).total_seconds()
                                            if diff >= 600:
                                                table_points.append(pt)
                                                last_added_time = pt['time_obj']
                                                
                                    # Calculate Summary Points
                                    start_pt = all_details[0]
                                    end_pt = all_details[-1]
                                    import math
                                    
                                    def haversine(lat1, lon1, lat2, lon2):
                                        R = 6371.0 # Earth radius in km
                                        dlat = math.radians(lat2 - lat1)
                                        dlon = math.radians(lon2 - lon1)
                                        a = math.sin(dlat / 2)**2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon / 2)**2
                                        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
                                        return R * c * 1000 # distance in meters

                                    # Summit Arrival: find the first point that is within 100 meters 
                                    # (or the absolute closest point if 100m is never reached) of the registered mountain coordinates
                                    try:
                                        base_lat = float(lat)
                                        base_lon = float(lon)
                                        closest_pt = min(all_details, key=lambda p: haversine(base_lat, base_lon, p['lat'], p['lng']))
                                        min_dist = haversine(base_lat, base_lon, closest_pt['lat'], closest_pt['lng'])
                                        
                                        # Target threshold: whichever is larger between 100m or (min_dist + 50m)
                                        threshold_dist = max(100.0, min_dist + 50.0)
                                        
                                        summit_pt = closest_pt
                                        summit_idx = all_details.index(closest_pt)
                                        
                                        # Scan to find the *first* time we entered this threshold area
                                        for i in range(summit_idx, -1, -1):
                                            pt = all_details[i]
                                            if haversine(base_lat, base_lon, pt['lat'], pt['lng']) <= threshold_dist:
                                                summit_pt = pt
                                            else:
                                                break
                                                
                                        # Descent start: look forwards from the closest point
                                        # until we leave the threshold area
                                        descent_start_pt = closest_pt
                                        for i in range(summit_idx, len(all_details)):
                                            pt = all_details[i]
                                            if haversine(base_lat, base_lon, pt['lat'], pt['lng']) <= threshold_dist:
                                                descent_start_pt = pt
                                            else:
                                                break
                                    except (ValueError, TypeError):
                                        # Fallback if base coordinates are invalid
                                        summit_pt = all_details[len(all_details)//2]
                                        descent_start_pt = summit_pt
                                            
                                    summary_points = {
                                        "登山開始": start_pt,
                                        "登頂": summit_pt,
                                        "下山開始": descent_start_pt,
                                        "登山終了": end_pt
                                    }

                                    st.markdown("##### 山行サマリー")
                                    # Create columns for summary
                                    cols = st.columns(4)
                                    for i, (label, pt) in enumerate(summary_points.items()):
                                        with cols[i]:
                                            st.metric(label=label, value=pt["time_str"], delta=f"{pt['elevation']}m", delta_color="off")

                                    # Summary view is now the only UI above the map
                            except Exception as e:
                                st.error(f"GPX読み込みエラー: {e}")

                        # Render Custom GPX Map Component
                        if "google_maps" in st.secrets and "api_key" in st.secrets["google_maps"]:
                            api_key = st.secrets["google_maps"]["api_key"]
                            
                            from src.components.gpx_map import gpx_map
                            
                            # Strip out datetime objects for JSON serialization
                            frontend_all_details = [{k: v for k, v in pt.items() if k != 'time_obj'} for pt in (all_details if gpx_data else [])]
                            frontend_table_points = [{k: v for k, v in pt.items() if k != 'time_obj'} for pt in (table_points if gpx_data else [])]
                            
                            gpx_map(
                                api_key=api_key,
                                name=name,
                                lat=lat,
                                lon=lon,
                                gpx_points=frontend_all_details,
                                table_points=frontend_table_points,
                                gpx_duration=gpx_duration,
                                key=f"custom_gpx_map_{selected_idx}"
                            )
                            
                            if os.path.exists(gpx_path):
                                st.markdown("<br>", unsafe_allow_html=True)
                                col1, col2, col3 = st.columns([1, 2, 1])
                                if col2.button("軌跡データを削除", key=f"del_gpx_{selected_idx}", use_container_width=True):
                                    os.remove(gpx_path)
                                    st.rerun()
                        else:
                            st.error("Google Maps APIキーが設定されていません。")
                    else:
                        st.info("この記録には位置情報が登録されていません。")
            else:
                st.info("まだ記録がありません。「新規登録」から追加してください。")
                
        with tab2:
            render_map(df)
            
    elif mode == "新規登録":
        render_form()

if __name__ == "__main__":
    main()
