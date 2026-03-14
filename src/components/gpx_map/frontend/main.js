let map = null;
let trackPolyline = null;
let hoverMarker = null;

function renderComponent(args) {
    const root = document.getElementById("app-root");
    root.innerHTML = ''; // Clear previous

    const name = args.name || "Unknown";
    const gpxPoints = args.gpxPoints || [];
    const tablePoints = args.tablePoints || gpxPoints;
    const gpxDuration = args.gpxDuration || "";
    const baseLat = args.lat || 35.681167; // default Tokyo
    const baseLng = args.lon || 139.767052;

    // Build Maps Container
    const mapDiv = document.createElement("div");
    mapDiv.id = "map";
    root.appendChild(mapDiv);

    // Initialize Map
    map = new google.maps.Map(mapDiv, {
        center: { lat: baseLat, lng: baseLng },
        zoom: 14,
        mapTypeId: 'terrain'
    });

    // Add OpenTopoMap Layer
    const openTopoMapType = new google.maps.ImageMapType({
        getTileUrl: function (coord, zoom) {
            return `https://tile.opentopomap.org/${zoom}/${coord.x}/${coord.y}.png`;
        },
        tileSize: new google.maps.Size(256, 256),
        name: "OpenTopoMap",
        maxZoom: 17
    });
    map.mapTypes.set('opentopomap', openTopoMapType);
    map.setMapTypeId('opentopomap');

    // Default Marker (Mountain Summit)
    const marker = new google.maps.Marker({
        position: { lat: baseLat, lng: baseLng },
        map: map,
        title: name
    });

    // Hover Marker (Blue Dot)
    hoverMarker = new google.maps.Marker({
        map: map,
        icon: 'http://maps.google.com/mapfiles/ms/icons/blue-dot.png',
        visible: false,
        zIndex: 1000
    });

    if (gpxPoints.length > 0) {
        // Draw Track
        trackPolyline = new google.maps.Polyline({
            path: gpxPoints.map(p => ({ lat: p.lat, lng: p.lng })),
            geodesic: true,
            strokeColor: "#FF0000",
            strokeOpacity: 0.8,
            strokeWeight: 4,
        });
        trackPolyline.setMap(map);

        // Fit Bounds
        const bounds = new google.maps.LatLngBounds();
        gpxPoints.forEach(p => bounds.extend(p));
        map.fitBounds(bounds);

        // Build Details Table using the downsampled tablePoints
        if (tablePoints && tablePoints.length > 0 && tablePoints[0].elapsed !== undefined) {
            buildDetailsTable(root, tablePoints);
        }
    } else {
        const infoWindow = new google.maps.InfoWindow({
            content: `<b>${name}</b><br>周辺の登山道`
        });
        infoWindow.open(map, marker);
    }

    // Tell Streamlit how tall we are
    setTimeout(() => {
        setFrameHeight(document.body.scrollHeight + 50);
    }, 500);
}

function buildDetailsTable(root, points) {
    const detailsContainer = document.createElement("div");
    detailsContainer.className = "details-container";

    const header = document.createElement("div");
    header.className = "details-header";
    header.innerText = "詳細レコード";
    detailsContainer.appendChild(header);

    const tableWrapper = document.createElement("div");
    tableWrapper.className = "table-wrapper";

    const table = document.createElement("table");
    const thead = document.createElement("thead");
    thead.innerHTML = `
        <tr>
            <th>時刻</th>
            <th>経過</th>
            <th>距離(km)</th>
            <th>標高(m)</th>
        </tr>
    `;
    table.appendChild(thead);

    const tbody = document.createElement("tbody");
    points.forEach((point, index) => {
        const tr = document.createElement("tr");

        // Hover interaction
        tr.addEventListener("mouseenter", () => {
            hoverMarker.setPosition({ lat: point.lat, lng: point.lng });
            hoverMarker.setVisible(true);
        });
        tr.addEventListener("mouseleave", () => {
            hoverMarker.setVisible(false);
        });

        // Cells
        tr.innerHTML = `
            <td>${point.time_str || '-'}</td>
            <td>${point.elapsed || '-'}</td>
            <td>${point.dist_km !== undefined ? point.dist_km.toFixed(1) : '-'}</td>
            <td>${point.elevation !== undefined ? point.elevation : '-'}</td>
        `;

        tbody.appendChild(tr);
    });

    table.appendChild(tbody);
    tableWrapper.appendChild(table);
    detailsContainer.appendChild(tableWrapper);
    root.appendChild(detailsContainer);
}
