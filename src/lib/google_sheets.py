import streamlit as st
import pandas as pd
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime

# Sheet ID from user request
SHEET_ID = "1A_eiENf6qzQQ8JtYaydOoWqvHTAKlcrwzAQ1JHHurOA"
WORKSHEET_NAME = "Sheet1"  # Assuming default

# Column names based on requirements
COLUMNS = ["日付", "山名", "都道府県", "標高", "緯度経度", "URL", "備考"]

def parse_lat_lon(lat_lon_str):
    """Parses 'lat, lon' string into separate float values."""
    try:
        if not lat_lon_str or not isinstance(lat_lon_str, str):
            return None, None
        parts = lat_lon_str.split(',')
        if len(parts) != 2:
            return None, None
        return float(parts[0].strip()), float(parts[1].strip())
    except ValueError:
        return None, None

def get_connection():
    """Establishes connection to Google Sheets."""
    try:
        # Check if secrets exist
        if "gsheets" not in st.secrets:
            return None
            
        credentials = st.secrets["gsheets"]
        # gspread uses a dict for credentials if passed directly, 
        # or we can verify the structure matches what gspread expects
        gc = gspread.service_account_from_dict(credentials)
        return gc
    except Exception as e:
        st.error(f"Google Sheets connection failed: {e}")
        return None

@st.cache_data(ttl=60)
def get_climbs():
    """
    Fetches climb data from Google Sheets.
    Returns a pandas DataFrame.
    """
    gc = get_connection()
    
    # If gc is None or exception occurred, df might differ.
    # Logic flow:
    # 1. Try GC. If success, return df (but we want to clean it first).
    # 2. If fail/no GC, get mock data.
    
    df = None
    if gc:
        try:
            sh = gc.open_by_key(SHEET_ID)
            try:
                worksheet = sh.worksheet(WORKSHEET_NAME)
            except:
                worksheet = sh.get_worksheet(0)
                
            data = worksheet.get_all_records()
            df = pd.DataFrame(data)
        except Exception as e:
            st.warning(f"Failed to fetch from Google Sheets: {e}. Using mock data.")
            
    if df is None:
        df = get_mock_data()

    # --- Common Data Cleaning ---
    # Ensure all columns exist
    for col in COLUMNS:
        if col not in df.columns:
            df[col] = "" 

    # Split '緯度経度'
    if '緯度経度' in df.columns:
        df['緯度'], df['経度'] = zip(*df['緯度経度'].apply(parse_lat_lon))
    else:
         df['緯度'] = None
         df['経度'] = None
    
    # Convert '標高' to numeric
    if '標高' in df.columns:
        # cleanup: remove commas if string, etc.
        # But assume simple structure first.
        # errors='coerce' turns '' to NaN.
        df['標高'] = pd.to_numeric(df['標高'], errors='coerce').fillna(0).astype(int)

    return df

def add_climb(data_dict):
    """
    Adds a new climb record to the Google Sheet.
    data_dict: dict containing values for COLUMNS
    """
    gc = get_connection()
    
    if gc:
        try:
            sh = gc.open_by_key(SHEET_ID)
            try:
                worksheet = sh.worksheet(WORKSHEET_NAME)
            except:
                worksheet = sh.get_worksheet(0)
            
            # Prepare row data in correct order
            row = [str(data_dict.get(col, "")) for col in COLUMNS]
            worksheet.append_row(row)
            st.cache_data.clear() # Clear cache to show new data
            return True
        except Exception as e:
            st.error(f"Failed to add data to Google Sheets: {e}")
            return False
    else:
        # In mock mode, we can't save persistently, but we can restart
        st.warning("Running in mock mode. Data cannot be saved to Google Sheets.")
        return False

def get_mock_data():
    """Returns sample data for development."""
    mock_data = [
        {
            "日付": "2023-08-11",
            "山名": "富士山",
            "都道府県": "静岡県・山梨県",
            "標高": "3776",
            "緯度経度": "35.3606, 138.7274",
            "URL": "https://www.fujisan-climb.jp/",
            "備考": "日本最高峰。ご来光が綺麗だった。"
        },
        {
            "日付": "2023-10-05",
            "山名": "高尾山",
            "都道府県": "東京都",
            "標高": "599",
            "緯度経度": "35.6250, 139.2437",
            "URL": "https://www.takaotozan.co.jp/",
            "備考": "紅葉にはまだ早かったが、天気が良く気持ちよかった。"
        },
        {
            "日付": "2024-05-03",
            "山名": "筑波山",
            "都道府県": "茨城県",
            "標高": "877",
            "緯度経度": "36.2253, 140.1069",
            "URL": "",
            "備考": "ロープウェイを使わずに登った。結構きつい。"
        }
    ]
    return pd.DataFrame(mock_data)
