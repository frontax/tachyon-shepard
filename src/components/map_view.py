import streamlit as st
import pandas as pd
import streamlit.components.v1 as components

def render_map(df):
    """
    Renders a map with markers using Google Maps JavaScript API.
    """
    st.subheader("登山マップ (Google Maps)")
    
    # Check for API Key
    if "google_maps" not in st.secrets or "api_key" not in st.secrets["google_maps"]:
        st.error("Google Maps APIキーが設定されていません。.streamlit/secrets.toml に [google_maps] api_key = '...' を追加してください。")
        return

    api_key = st.secrets["google_maps"]["api_key"]

    if df.empty:
        st.info("データがありません。")
        return

    # Filter out invalid lat/lon
    valid_locations = df[pd.to_numeric(df['緯度'], errors='coerce').notnull() & 
                         pd.to_numeric(df['経度'], errors='coerce').notnull()]
    
    if valid_locations.empty:
        st.warning("位置情報を持つデータがありません。")
        center_lat = 35.6895
        center_lon = 139.6917
        zoom = 5
        markers_js = "[]"
    else:
        # Calculate center
        center_lat = valid_locations['緯度'].astype(float).mean()
        center_lon = valid_locations['経度'].astype(float).mean()
        zoom = 7

        # Generate markers JS data
        markers_data = []
        for index, row in valid_locations.iterrows():
            try:
                lat = float(row['緯度'])
                lon = float(row['経度'])
                name = row['山名'].replace("'", "\\'") # Escape quotes
                date = str(row['日付'])
                elev = str(row['標高'])
                
                content = f"<b>{name}</b><br>日付: {date}<br>標高: {elev}m"
                markers_data.append(f"{{lat: {lat}, lng: {lon}, content: '{content}'}}")
            except:
                continue
        
        markers_js = "[" + ",".join(markers_data) + "]"

    # HTML/JS for Google Maps
    html_code = f"""
    <!DOCTYPE html>
    <html>
      <head>
        <title>Mountain Map</title>
        <script src="https://maps.googleapis.com/maps/api/js?key={api_key}&callback=initMap" async defer></script>
        <style>
          #map {{
            height: 800px;
            width: 100%;
          }}
          html, body {{
            height: 100%;
            margin: 0;
            padding: 0;
          }}
        </style>
        <script>
          function initMap() {{
            const center = {{ lat: {center_lat}, lng: {center_lon} }};
            const map = new google.maps.Map(document.getElementById("map"), {{
              zoom: {zoom},
              center: center,
            }});

            const markers = {markers_js};
            const infoWindow = new google.maps.InfoWindow();

            markers.forEach(markerData => {{
              const marker = new google.maps.Marker({{
                position: {{ lat: markerData.lat, lng: markerData.lng }},
                map: map,
              }});

              marker.addListener("click", () => {{
                infoWindow.setContent(markerData.content);
                infoWindow.open(map, marker);
              }});
            }});
          }}
        </script>
      </head>
      <body>
        <div id="map"></div>
      </body>
    </html>
    """

    components.html(html_code, height=800)

import json

def render_trail_map(lat, lon, name, gpx_points=None, gpx_duration=None, highlight_point=None):
    """
    Renders a centered map with terrain mapTypeId for viewing mountain trails.
    Can also render a GPX track as a red polyline if provided, and show course time.
    """
    if "google_maps" not in st.secrets or "api_key" not in st.secrets["google_maps"]:
        st.error("Google Maps APIキーが設定されていません。")
        return

    api_key = st.secrets["google_maps"]["api_key"]
    safe_name = str(name).replace("'", "\\'")
    
    # Format the info window content
    info_content = f"<b>{safe_name}</b><br>周辺の登山道"
    if gpx_duration:
        info_content += f"<br>所要時間 (移動時間): {gpx_duration}"

    # Prepare GPX data for JS
    gpx_js = json.dumps(gpx_points) if gpx_points else "[]"

    html_code = f"""
    <!DOCTYPE html>
    <html>
      <head>
        <script src="https://maps.googleapis.com/maps/api/js?key={api_key}&callback=initTrailMap" async defer></script>
        <style>
          #trail-map {{
            height: 400px;
            width: 100%;
          }}
          html, body {{
            height: 100%;
            margin: 0;
            padding: 0;
          }}
        </style>
        <script>
          function initTrailMap() {{
            const center = {{ lat: {lat}, lng: {lon} }};
            const map = new google.maps.Map(document.getElementById("trail-map"), {{
              zoom: 14,
              center: center,
              mapTypeId: 'opentopo',
              mapTypeControlOptions: {{
                mapTypeIds: ['opentopo', 'osm', 'roadmap', 'terrain']
              }}
            }});
            
            // Define OpenStreetMap Type (Fallback)
            const osmMapType = new google.maps.ImageMapType({{
                getTileUrl: function(coord, zoom) {{
                    return "https://tile.openstreetmap.org/" + zoom + "/" + coord.x + "/" + coord.y + ".png";
                }},
                tileSize: new google.maps.Size(256, 256),
                maxZoom: 19,
                minZoom: 0,
                name: "OSM 標準"
            }});
            
            // Define OpenTopoMap Type (Excellent for hiking trails and contours)
            const openTopoMapType = new google.maps.ImageMapType({{
                getTileUrl: function(coord, zoom) {{
                    return "https://tile.opentopomap.org/" + zoom + "/" + coord.x + "/" + coord.y + ".png";
                }},
                tileSize: new google.maps.Size(256, 256),
                maxZoom: 17,
                name: "地形図 (登用)",
                opacity: 1.0
            }});

            map.mapTypes.set('opentopo', openTopoMapType);
            map.mapTypes.set('osm', osmMapType);
            map.setMapTypeId('opentopo');

            const marker = new google.maps.Marker({{
              position: center,
              map: map,
              title: "{safe_name}"
            }});
            
            const infoWindow = new google.maps.InfoWindow({{
                content: "{info_content}"
            }});
            
            marker.addListener("click", () => {{
                infoWindow.open(map, marker);
            }});
            
            // Render GPX Track if provided
            const trackPoints = {gpx_js};
            const highlightPointStr = '{json.dumps(highlight_point) if highlight_point else "null"}';
            const highlightPoint = highlightPointStr !== 'null' ? JSON.parse(highlightPointStr) : null;
            
            if (trackPoints.length > 0) {{
                const flightPath = new google.maps.Polyline({{
                    path: trackPoints,
                    geodesic: true,
                    strokeColor: "#FF0000",
                    strokeOpacity: 0.8,
                    strokeWeight: 4,
                }});
                flightPath.setMap(map);
                
                if (highlightPoint) {{
                    const hMarker = new google.maps.Marker({{
                        position: highlightPoint,
                        map: map,
                        icon: 'http://maps.google.com/mapfiles/ms/icons/blue-dot.png',
                        title: '選択地点',
                        zIndex: 1000
                    }});
                    map.setCenter(highlightPoint);
                    map.setZoom(16);
                }} else {{
                    // Adjust map bounds to show the entire track
                    const bounds = new google.maps.LatLngBounds();
                    for (let i = 0; i < trackPoints.length; i++) {{
                        bounds.extend(trackPoints[i]);
                    }}
                    map.fitBounds(bounds);
                }}
            }} else {{
                // Open immediately if no track was loaded
                infoWindow.open(map, marker);
            }}
          }}
        </script>
      </head>
      <body>
        <div id="trail-map"></div>
      </body>
    </html>
    """

    components.html(html_code, height=400)
