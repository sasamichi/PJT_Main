/**
 * 世界交通網・地域データ基盤 公開Webサイト
 * 地図制御モジュール (Leaflet.js)
 */

const PublicMap = {
  map: null,
  markerLayer: null,
  activeCountryMeta: null,
  tileLayers: {},

  init: function (containerId) {
    // タイルレイヤーの定義
    const osmLayer = L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
      maxZoom: 19,
      attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors',
    });

    const gsiStdLayer = L.tileLayer("https://cyberjapandata.gsi.go.jp/xyz/std/{z}/{x}/{y}.png", {
      maxZoom: 18,
      attribution: '&copy; <a href="https://maps.gsi.go.jp/development/ichiran.html">国土地理院</a>',
    });

    const gsiPhotoLayer = L.tileLayer("https://cyberjapandata.gsi.go.jp/xyz/seamlessphoto/{z}/{x}/{y}.jpg", {
      maxZoom: 18,
      attribution: '&copy; <a href="https://maps.gsi.go.jp/development/ichiran.html">国土地理院(航空写真)</a>',
    });

    this.tileLayers = {
      "OpenStreetMap (世界標準)": osmLayer,
      "国土地理院 (日本詳細)": gsiStdLayer,
      "航空写真 (オルソ)": gsiPhotoLayer,
    };

    // 地図の初期化 (デフォルト日本中心)
    this.map = L.map(containerId, {
      center: [36.2048, 138.2529],
      zoom: 6,
      layers: [osmLayer],
      zoomControl: true,
    });

    // レイヤーコントロール
    L.control.layers(this.tileLayers, null, { position: "topleft" }).addTo(this.map);

    // マーカー用レイヤーグループ
    this.markerLayer = L.layerGroup().addTo(this.map);

    return this;
  },

  // 国の変更に合わせて地図の中心・ズームを移動
  setCountryView: function (mapMeta) {
    this.activeCountryMeta = mapMeta;
    if (mapMeta && mapMeta.center && mapMeta.center[0] !== 0) {
      this.map.setView(mapMeta.center, mapMeta.zoom || 6);
    }
  },

  // 地図表示を国の初期位置にリセット
  resetView: function () {
    if (this.activeCountryMeta && this.activeCountryMeta.center) {
      this.map.setView(this.activeCountryMeta.center, this.activeCountryMeta.zoom || 6);
    }
  },

  // 指定座標へスムーズに移動し、マーカーをハイライト
  flyToLocation: function (lat, lon, zoom = 14, popupHtml = null) {
    if (lat == null || lon == null) return;
    this.map.flyTo([lat, lon], Math.max(this.map.getZoom(), zoom), { duration: 1.2 });
    if (popupHtml) {
      const popup = L.popup({ autoClose: false, closeOnClick: false })
        .setLatLng([lat, lon])
        .setContent(popupHtml)
        .openOn(this.map);
    }
  },

  // 複数のノード（駅や拠点）を地図上にプロット
  plotNodes: function (nodes, maxCount = 800) {
    this.markerLayer.clearLayers();
    if (!nodes || nodes.length === 0) return 0;

    let plotted = 0;
    const bounds = L.latLngBounds();

    for (const node of nodes) {
      if (node.lat == null || node.lon == null) continue;
      if (plotted >= maxCount) break;

      const marker = L.circleMarker([node.lat, node.lon], {
        radius: 5,
        fillColor: "#2563eb",
        color: "#ffffff",
        weight: 1.5,
        opacity: 1,
        fillOpacity: 0.85,
      });

      // ポップアップ内容
      const popupContent = `
        <div class="popup-title">${node.name || "名称未登録"}</div>
        ${node.name_official ? `<div class="popup-sub">${node.name_official}</div>` : ""}
        <div>
          <span class="popup-tag">${node.category || "拠点"}</span>
          ${node.status ? `<span class="popup-tag">${node.status}</span>` : ""}
          ${node.municipality_name ? `<span class="popup-tag">${node.municipality_name}</span>` : ""}
        </div>
        <div class="popup-links">
          <a href="https://www.google.com/maps/search/?api=1&query=${node.lat},${node.lon}" target="_blank" rel="noopener">
            🗺️ Google Maps で開く &raquo;
          </a>
        </div>
      `;

      marker.bindPopup(popupContent);
      this.markerLayer.addLayer(marker);
      bounds.extend([node.lat, node.lon]);
      plotted++;
    }

    // 表示マーカー数カウント要素の更新
    const countEl = document.getElementById("map-marker-count");
    if (countEl) {
      countEl.innerText = `${plotted} 件の拠点を表示中`;
    }

    return plotted;
  },

  // 路線シーケンスの駅群を地図にプロットし、ラインで繋ぐ
  plotSequence: function (sequenceNodes) {
    this.markerLayer.clearLayers();
    if (!sequenceNodes || sequenceNodes.length === 0) return;

    const latlngs = [];
    const bounds = L.latLngBounds();

    sequenceNodes.forEach((node, idx) => {
      if (node.lat == null || node.lon == null) return;
      const pt = [node.lat, node.lon];
      latlngs.push(pt);
      bounds.extend(pt);

      // 起点・終点は色を変えて目立たせる
      let fillColor = "#2563eb";
      let radius = 6;
      if (node.role === "起点") {
        fillColor = "#10b981"; // 緑
        radius = 8;
      } else if (node.role === "終点") {
        fillColor = "#ef4444"; // 赤
        radius = 8;
      } else if (node.role === "分岐駅") {
        fillColor = "#f59e0b"; // 橙
        radius = 7;
      }

      const marker = L.circleMarker(pt, {
        radius: radius,
        fillColor: fillColor,
        color: "#ffffff",
        weight: 2,
        opacity: 1,
        fillOpacity: 0.9,
      });

      const popupContent = `
        <div class="popup-title">${node.node_name}</div>
        <div class="popup-sub">順序: ${node.seq} ${node.station_number ? `(${node.station_number})` : ""}</div>
        <div>
          <span class="popup-tag">${node.role || "駅"}</span>
          ${node.section ? `<span class="popup-tag">${node.section}</span>` : ""}
          ${node.status ? `<span class="popup-tag">${node.status}</span>` : ""}
        </div>
        <div class="popup-links">
          <a href="https://www.google.com/maps/search/?api=1&query=${node.lat},${node.lon}" target="_blank" rel="noopener">
            🗺️ Google Maps で確認 &raquo;
          </a>
        </div>
      `;

      marker.bindPopup(popupContent);
      this.markerLayer.addLayer(marker);
    });

    // 駅同士を結ぶ折れ線（点と点の繋がり）を描画
    if (latlngs.length > 1) {
      const line = L.polyline(latlngs, {
        color: "#3b82f6",
        weight: 3.5,
        opacity: 0.8,
        dashArray: "6, 6",
      });
      this.markerLayer.addLayer(line);
    }

    if (bounds.isValid()) {
      this.map.fitBounds(bounds, { padding: [40, 40], maxZoom: 12 });
    }

    const countEl = document.getElementById("map-marker-count");
    if (countEl) {
      countEl.innerText = `駅順序 ${sequenceNodes.length} 駅をプロット`;
    }
  },
};
