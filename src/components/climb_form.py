import streamlit as st
from datetime import date
from src.lib.google_sheets import add_climb

def render_form():
    """
    Renders the form to add a new climb.
    """
    st.subheader("新規記録の追加")
    
    with st.form("add_climb_form", clear_on_submit=True):
        st.info("必要事項を入力し、「記録を保存」をクリックしてください。GPXファイルをアップロードすると、ダッシュボードの地図に軌跡が表示されます。")
        
        # List of Japanese prefectures
        prefectures = [
            "北海道", "青森県", "岩手県", "宮城県", "秋田県", "山形県", "福島県",
            "茨城県", "栃木県", "群馬県", "埼玉県", "千葉県", "東京都", "神奈川県",
            "新潟県", "富山県", "石川県", "福井県", "山梨県", "長野県", "岐阜県",
            "静岡県", "愛知県", "三重県", "滋賀県", "京都府", "大阪府", "兵庫県",
            "奈良県", "和歌山県", "鳥取県", "島根県", "岡山県", "広島県", "山口県",
            "徳島県", "香川県", "愛媛県", "高知県", "福岡県", "佐賀県", "長崎県",
            "熊本県", "大分県", "宮崎県", "鹿児島県", "沖縄県", "その他"
        ]
        
        col1, col2 = st.columns(2)
        
        with col1:
            climb_date = st.date_input("日付", value=date.today())
            mountain_name = st.text_input("山名", placeholder="例: 富士山")
            prefecture = st.selectbox("都道府県", options=prefectures)
            elevation = st.text_input("標高 (m)", placeholder="例: 3776")
            uploaded_gpx = st.file_uploader("GPXファイルをアップロード (軌跡表示用)", type=["gpx"])
        
        with col2:
            lat = st.number_input("緯度", format="%.6f", value=35.3606)
            lon = st.number_input("経度", format="%.6f", value=138.7274)
            url = st.text_input("URL", placeholder="YAMAPなどのURL")
            remarks = st.text_area("備考", placeholder="感想など")
            
        submitted = st.form_submit_button("記録を保存")
        
        if submitted:
            if not mountain_name:
                st.error("山名は必須です。")
                return
                
            # Combine lat/lon for storage
            lat_lon_str = f"{lat}, {lon}" if (lat != 0.0 or lon != 0.0) else ""
            
            # Extract GPX content if uploaded (just to save it)
            gpx_saved_content = None
            if uploaded_gpx is not None:
                gpx_saved_content = uploaded_gpx.getvalue().decode("utf-8")

            data = {
                "日付": climb_date.strftime("%Y-%m-%d"),
                "山名": mountain_name,
                "都道府県": prefecture,
                "標高": elevation,
                "緯度経度": lat_lon_str,
                "URL": url,
                "備考": remarks
            }
            
            from src.lib.google_sheets import get_climbs
            import os
            
            success = add_climb(data)
            if success:
                st.success(f"{mountain_name} の記録を保存しました！")
                
                # If we have GPX data, we need to save it locally relative to its new index
                if gpx_saved_content:
                    # After success add, the index of this new item will be the last one 
                    # in the newly fetched DataFrame. We force a re-fetch (cache is cleared in add_climb).
                    new_df = get_climbs()
                    if new_df is not None and not new_df.empty:
                        new_idx = len(new_df) - 1
                        
                        os.makedirs("data/gpx", exist_ok=True)
                        save_path = f"data/gpx/{new_idx}.gpx"
                        with open(save_path, "w", encoding="utf-8") as f:
                            f.write(gpx_saved_content)
                        st.success(f"GPXファイルをシステムに保存しました (ID: {new_idx})")
                        
                import time
                time.sleep(1) # Let the user see the success message
                st.rerun() # Refresh to show new data
