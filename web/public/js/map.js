/**
 * 世界交通網・地域データ基盤 公開Webサイト
 * 地図制御モジュール (Leaflet.js)
 * -------------------------------------------------------------
 * 【対応要件 (docs/03_コンテンツと画面仕様書 完全準拠)】:
 * 1. 背景タイル: OSM + グローバル衛星写真 + 国土地理院（標準・淡色・航空写真）
 * 2. レイヤ別ON/OFF制御: 鉄道、高速道路、道の駅・一般道、空海、気象観測点、構造物、路線区間エッジ
 * 3. 路線区間エッジ描画: edges.csv に基づく路線カラー付き実形状(GeoJSON)または直線補完
 * 4. ナレッジパネル連動、ストリートビュー直接起動ポップアップ
 */

const PublicMap = {
  map: null,
  activeCountryMeta: null,
  baseTileLayers: {},
  overlayLayers: {
    edgesRail: null,
    edgesAir: null,
    railways: null,
    highways: null,
    roadStations: null,
    airSea: null,
    amedas: null,
    structures: null,
    municipalities: null,
  },
  layerControl: null,
  currentRouteLayers: null, // 単一路線表示用の一時レイヤー
  allNodes: [],             // 全ノードキャッシュ (ビューポート連動描画用)
  muniMarkersMap: {},       // 自治体ID -> L.marker キャッシュ (リストからの直接フォーカス用)
  nodeMarkersMap: {},       // 観測所・拠点ID -> L.marker キャッシュ
  _renderTimer: null,
  _iconCache: {},           // L.icon インスタンスキャッシュ（パフォーマンス最適化）

  // L.icon プーリングキャッシュ取得
  getBadgeIcon: function (iconFile, size) {
    const key = `${iconFile}_${size}`;
    if (!this._iconCache[key]) {
      this._iconCache[key] = L.icon({
        iconUrl: `assets/icons/${iconFile}`,
        iconSize: [size, size],
        iconAnchor: [size / 2, size / 2],
        popupAnchor: [0, -Math.round(size / 2)],
        className: "custom-map-icon",
      });
    }
    return this._iconCache[key];
  },

  // アイコンキャッシュの事前生成（全16種 × 各種サイズ）
  initIconCache: function () {
    const iconFiles = [
      "train-shinkansen.svg", "train-station.svg", "subway.svg", "tram.svg",
      "highway-ic.svg", "highway-sa.svg", "roadside-station.svg", "airport.svg",
      "port.svg", "structure.svg", "gov-pref.svg", "gov-muni.svg", "weather.svg",
      "spot-castle.svg", "pin-saved.svg", "pin-draft.svg"
    ];
    const sizes = [18, 20, 22, 24, 25, 26, 28, 30, 32];
    iconFiles.forEach((file) => {
      sizes.forEach((s) => {
        this.getBadgeIcon(file, s);
      });
    });
  },

  init: function (containerId) {
    // 0. アイコンキャッシュの事前生成（高パフォーマンス描画用）
    this.initIconCache();

    // 1. ベースタイルレイヤーの定義
    const osmLayer = L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
      maxZoom: 19,
      attribution: '&copy; <a href="https://www.openstreetmap.org/copyright" target="_blank">OpenStreetMap</a>',
    });

    const gsiStdLayer = L.tileLayer("https://cyberjapandata.gsi.go.jp/xyz/std/{z}/{x}/{y}.png", {
      maxZoom: 18,
      attribution: '&copy; <a href="https://maps.gsi.go.jp/development/ichiran.html" target="_blank">国土地理院(標準)</a>',
    });

    const gsiPaleLayer = L.tileLayer("https://cyberjapandata.gsi.go.jp/xyz/pale/{z}/{x}/{y}.png", {
      maxZoom: 18,
      attribution: '&copy; <a href="https://maps.gsi.go.jp/development/ichiran.html" target="_blank">国土地理院(淡色)</a>',
    });

    const gsiPhotoLayer = L.tileLayer("https://cyberjapandata.gsi.go.jp/xyz/seamlessphoto/{z}/{x}/{y}.jpg", {
      maxZoom: 18,
      attribution: '&copy; <a href="https://maps.gsi.go.jp/development/ichiran.html" target="_blank">国土地理院(写真)</a>',
    });

    const esriSatLayer = L.tileLayer("https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}", {
      maxZoom: 18,
      attribution: '&copy; <a href="https://www.esri.com/" target="_blank">Esri World Imagery</a>',
    });

    this.baseTileLayers = {
      "🌐 OpenStreetMap (世界標準)": osmLayer,
      "🗾 国土地理院 標準地図 (日本)": gsiStdLayer,
      "📄 国土地理院 淡色地図 (日本)": gsiPaleLayer,
      "📸 国土地理院 航空写真 (日本)": gsiPhotoLayer,
      "🛰️ グローバル衛星写真 (Esri)": esriSatLayer,
    };

    // 2. オーバーレイレイヤーグループの生成 (都道府県庁は通常レイヤー、市区町村役場は件数クラスタ化で超高速化)
    this.overlayLayers.prefGov = L.layerGroup();
    if (typeof L.markerClusterGroup === "function") {
      this.overlayLayers.muniGov = L.markerClusterGroup({
        showCoverageOnHover: false,
        maxClusterRadius: 45,
        spiderfyOnMaxZoom: true,
        disableClusteringAtZoom: 13,
        chunkedLoading: true,
        chunkInterval: 50,
        chunkDelay: 20,
      });
      // 気象観測地点（アメダス）用クラスタグループ
      this.overlayLayers.amedas = L.markerClusterGroup({
        showCoverageOnHover: false,
        maxClusterRadius: 45,
        spiderfyOnMaxZoom: true,
        disableClusteringAtZoom: 13,
        chunkedLoading: true,
        chunkInterval: 50,
        chunkDelay: 20,
      });
    } else {
      this.overlayLayers.muniGov = L.layerGroup();
      this.overlayLayers.amedas = L.layerGroup();
    }
    this.overlayLayers.municipalities = L.layerGroup();
    this.overlayLayers.edgesRail = L.layerGroup();
    this.overlayLayers.edgesAir = L.layerGroup();
    this.overlayLayers.railways = L.layerGroup();
    this.overlayLayers.highways = L.layerGroup();
    this.overlayLayers.roadStations = L.layerGroup();
    this.overlayLayers.airSea = L.layerGroup();
    this.overlayLayers.structures = L.layerGroup();

    const overlayMapControls = {
      "🏛️ 都道府県庁代表点": this.overlayLayers.prefGov,
      "🏛️ 市区町村役場代表点": this.overlayLayers.muniGov,
      "🌡️ 気象観測地点 (アメダス)": this.overlayLayers.amedas,
    };

    // 3. 地図の初期化 (デフォルト日本中心・国土地理院淡色地図・自治体ノード・アメダス初期表示)
    this.map = L.map(containerId, {
      center: [36.2048, 138.2529],
      zoom: 6,
      layers: [
        gsiPaleLayer, // 背景地図のデフォルトを「国土地理院淡色地図」に設定
        this.overlayLayers.prefGov,
        this.overlayLayers.muniGov,
        this.overlayLayers.amedas,
      ],
      zoomControl: true,
    });

    // 4. レイヤーコントロールの追加
    this.layerControl = L.control.layers(this.baseTileLayers, overlayMapControls, {
      position: "topleft",
      collapsed: true,
    }).addTo(this.map);

    // 単一路線シーケンス描画用
    this.currentRouteLayers = L.layerGroup().addTo(this.map);

    // クイックレイヤ切替バーの初期化・連動
    this.initQuickLayerBar();

    // 背景地図をドラッグまたはズームした際に自然にポップアップを閉じる（静止時は開いたまま維持）
    this.map.on("dragstart", () => {
      this.map.closePopup();
    });
    this.map.on("zoomstart", () => {
      this.map.closePopup();
    });

    // ウィンドウリサイズ検知とinvalidateSize実行（デバウンス付き）
    let resizeTimer = null;
    window.addEventListener("resize", () => {
      clearTimeout(resizeTimer);
      resizeTimer = setTimeout(() => {
        if (this.map) this.map.invalidateSize();
      }, 100);
    });

    // コンテナサイズ変化をミリ秒単位で検知する ResizeObserver
    if (window.ResizeObserver) {
      const resizeObserver = new ResizeObserver(() => {
        if (this.map) this.map.invalidateSize();
      });
      const mapContainerEl = document.getElementById(containerId);
      if (mapContainerEl) resizeObserver.observe(mapContainerEl);
    }

    // 地図移動・ズーム完了時に表示領域（ビューポート）内の拠点を動的再描画
    this.map.on("moveend", () => {
      clearTimeout(this._renderTimer);
      this._renderTimer = setTimeout(() => {
        this.renderViewportNodes();
      }, 250);
    });

    return this;
  },

  // クイックレイヤ切替バーの初期化・双方向連動
  initQuickLayerBar: function () {
    const quickBar = document.getElementById("map-layer-quick-bar");
    if (!quickBar) return;

    const layerMap = {
      prefGov: this.overlayLayers.prefGov,
      muniGov: this.overlayLayers.muniGov,
      amedas: this.overlayLayers.amedas,
    };

    quickBar.querySelectorAll(".layer-pill").forEach((btn) => {
      const key = btn.getAttribute("data-layer");
      const targetLayer = layerMap[key];
      if (targetLayer && this.map.hasLayer(targetLayer)) {
        btn.classList.add("active");
      } else {
        btn.classList.remove("active");
      }

      btn.addEventListener("click", () => {
        if (!targetLayer) return;
        if (this.map.hasLayer(targetLayer)) {
          this.map.removeLayer(targetLayer);
          btn.classList.remove("active");
        } else {
          this.map.addLayer(targetLayer);
          btn.classList.add("active");
        }
      });
    });

    this.map.on("overlayadd", (e) => {
      for (const [key, layer] of Object.entries(layerMap)) {
        if (layer === e.layer) {
          const btn = quickBar.querySelector(`.layer-pill[data-layer="${key}"]`);
          if (btn) btn.classList.add("active");
        }
      }
    });

    this.map.on("overlayremove", (e) => {
      for (const [key, layer] of Object.entries(layerMap)) {
        if (layer === e.layer) {
          const btn = quickBar.querySelector(`.layer-pill[data-layer="${key}"]`);
          if (btn) btn.classList.remove("active");
        }
      }
    });
  },

  // 国の変更に合わせて地図の中心・ズームを移動
  setCountryView: function (mapMeta, countryCode) {
    this.activeCountryMeta = mapMeta;
    if (mapMeta && mapMeta.center && mapMeta.center[0] !== 0) {
      this.map.setView(mapMeta.center, mapMeta.zoom || 6);
    }
    // 日本以外の場合は OSM を初期ベースレイヤーに切替、日本の場合は淡色地図
    if (countryCode && countryCode !== "JP") {
      this.map.removeLayer(this.baseTileLayers["📄 国土地理院 淡色地図 (日本)"]);
      this.map.removeLayer(this.baseTileLayers["🗾 国土地理院 標準地図 (日本)"]);
      this.map.addLayer(this.baseTileLayers["🌐 OpenStreetMap (世界標準)"]);
    } else {
      this.map.removeLayer(this.baseTileLayers["🌐 OpenStreetMap (世界標準)"]);
      this.map.addLayer(this.baseTileLayers["📄 国土地理院 淡色地図 (日本)"]);
    }
  },

  // 地図表示を国の初期位置にリセット
  invalidateSize: function () {
    if (this.map) {
      this.map.invalidateSize();
    }
  },

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
      L.popup({ autoClose: true, closeOnClick: true })
        .setLatLng([lat, lon])
        .setContent(popupHtml)
        .openOn(this.map);
    }
  },

  // 全レイヤーのクリア
  clearAllOverlays: function () {
    Object.values(this.overlayLayers).forEach((layer) => layer.clearLayers());
    if (this.currentRouteLayers) this.currentRouteLayers.clearLayers();
  },

  // =========================================================================
  // 1. エッジ（路線区間ライン）の描画
  // =========================================================================
  
  // 自治体（役所・政庁代表点）のプロット (都道府県庁と市区町村役場を別レイヤー化・件数クラスタリング)
  // ※ 役所がある自治体のみを表示対象とするため、郡等は地図上から除外（リスト側には残存）
  plotMunicipalities: function (munis) {
    this.overlayLayers.prefGov.clearLayers();
    this.overlayLayers.muniGov.clearLayers();
    this.overlayLayers.municipalities.clearLayers();
    this.muniMarkersMap = {};
    if (!munis || munis.length === 0) return 0;

    let prefCount = 0;
    const muniMarkers = [];

    munis.forEach((m) => {
      if (m.lat == null || m.lon == null) return;
      // 役所のない郡は座標なしのため自然にスキップ、支庁・振興局庁舎はプロット
      if (m.category === "郡") return;

      const isPref = m.level === 1;
      const iconFile = isPref ? "gov-pref.svg" : "gov-muni.svg";
      const iconSize = isPref ? 28 : 22;
      const muniIcon = this.getBadgeIcon(iconFile, iconSize);
      const marker = L.marker([m.lat, m.lon], {
        icon: muniIcon,
        zIndexOffset: isPref ? 500 : 100,
      });

      // 各種URL項目の生成
      const urlLinks = [];
      if (m.website) {
        urlLinks.push(`<a href="${m.website}" target="_blank" rel="noopener" class="popup-url-btn">🔗 公式サイト</a>`);
      }
      if (m.wiki_ja) {
        urlLinks.push(`<a href="${m.wiki_ja}" target="_blank" rel="noopener" class="popup-url-btn">🌐 Wikipedia</a>`);
      }
      urlLinks.push(`<a href="https://www.google.com/maps/search/?api=1&query=${m.lat},${m.lon}" target="_blank" rel="noopener" class="popup-url-btn">🗺️ Google Maps</a>`);

      // 外部天気予報リンク（気象庁公式のみ）
      let weatherHtml = "";
      if (m.weather_urls && m.weather_urls.jma) {
        weatherHtml = `
          <div style="margin-top:6px; font-size:11px; color:var(--text-muted); font-weight:600;">天気予報リンク:</div>
          <div style="display:flex; gap:4px; flex-wrap:wrap; margin-top:3px;">
            <a href="${m.weather_urls.jma}" target="_blank" rel="noopener" class="popup-weather-btn">🌦️ 気象庁公式天気予報</a>
          </div>
        `;
      }

      const popupContent = `
        <div class="popup-title">🏛️ ${m.name}</div>
        <div class="popup-sub">${m.category || "自治体"} ${m.parent_name ? `(${m.parent_name})` : ""}</div>
        <div style="font-size:12px; margin:4px 0; color:var(--text-secondary);">
          ${m.code ? `<span>コード: <b>${m.code}</b></span>` : ""}
          ${m.pop ? `<span> | 人口: <b>${m.pop.toLocaleString()}人</b></span>` : ""}
        </div>
        <div style="display:flex; gap:4px; flex-wrap:wrap; margin-top:6px;">
          ${urlLinks.join("")}
        </div>
        ${weatherHtml}
        <div style="margin-top:8px; border-top:1px solid var(--border-color); padding-top:6px;">
          <button class="popup-return-btn" onclick="window.App && window.App.returnToTreeFromMap('${m.id}')">
            📖 階層ビューに戻る
          </button>
        </div>
      `;
      marker.bindPopup(popupContent, { maxWidth: 280 });
      this.muniMarkersMap[m.id] = marker;

      if (isPref) {
        this.overlayLayers.prefGov.addLayer(marker);
        prefCount++;
      } else {
        muniMarkers.push(marker);
      }
      this.overlayLayers.municipalities.addLayer(marker);
    });

    // 市区町村マーカーを一括追加（クラスタ対応時は超高速バッチ処理）
    if (typeof this.overlayLayers.muniGov.addLayers === "function") {
      this.overlayLayers.muniGov.addLayers(muniMarkers);
    } else {
      muniMarkers.forEach((m) => this.overlayLayers.muniGov.addLayer(m));
    }

    return prefCount + muniMarkers.length;
  },

  // 気象観測地点（アメダス）のプロット（件数クラスタリング）
  plotAmedas: function (nodes) {
    this.overlayLayers.amedas.clearLayers();
    this.nodeMarkersMap = {};
    if (!nodes || nodes.length === 0) return 0;

    const amedasNodes = nodes.filter(
      (n) =>
        (n.category === "気象観測点" ||
          (n.category && n.category.includes("気象")) ||
          n.sub_category === "気象") &&
        n.lat != null &&
        n.lon != null
    );

    const amedasMarkers = [];
    const amedasIcon = this.getBadgeIcon("weather.svg", 22);

    amedasNodes.forEach((node) => {
      const marker = L.marker([node.lat, node.lon], {
        icon: amedasIcon,
        zIndexOffset: 150,
      });

      const urlLinks = [];
      if (node.obs_url) {
        urlLinks.push(`<a href="${node.obs_url}" target="_blank" rel="noopener" class="popup-weather-btn" style="background:#fee2e2; color:#991b1b; border-color:#fecaca;">🌡️ 気象庁公式実況データ ↗</a>`);
      }
      if (node.wiki_ja) {
        urlLinks.push(`<a href="${node.wiki_ja}" target="_blank" rel="noopener" class="popup-url-btn">🌐 Wikipedia</a>`);
      }
      urlLinks.push(`<a href="https://www.google.com/maps/search/?api=1&query=${node.lat},${node.lon}" target="_blank" rel="noopener" class="popup-url-btn">🗺️ Google Maps</a>`);
      if (node.sv_url) {
        urlLinks.push(`<a href="${node.sv_url}" target="_blank" rel="noopener" class="popup-url-btn">👀 ストリートビュー</a>`);
      }

      // 所在自治体へのリンクボタン
      let returnBtnHtml = "";
      const muniId = (node.muni_ids && node.muni_ids[0]) || node.muni_id;
      if (muniId) {
        returnBtnHtml = `
          <div style="margin-top:8px; border-top:1px solid var(--border-color); padding-top:6px;">
            <button class="popup-return-btn" onclick="window.App && window.App.returnToTreeFromMap('${muniId}')">
              📖 所在自治体 (${node.muni_name || "一覧"}) を開く
            </button>
          </div>
        `;
      }

      const popupContent = `
        <div class="popup-title">🌡️ ${node.name}</div>
        <div class="popup-sub">気象庁 地上気象観測所 (AMeDAS) ${node.muni_name ? `(${node.muni_name})` : ""}</div>
        <div style="font-size:12px; margin:4px 0; color:var(--text-secondary);">
          ${node.code ? `<span>観測所番号: <b>${node.code}</b></span>` : ""}
          ${node.elevation != null ? `<span> | 標高: <b>${node.elevation}m</b></span>` : ""}
        </div>
        <div style="display:flex; gap:4px; flex-wrap:wrap; margin-top:6px;">
          ${urlLinks.join("")}
        </div>
        ${returnBtnHtml}
      `;

      marker.bindPopup(popupContent, { maxWidth: 280 });
      this.nodeMarkersMap[node.id] = marker;
      amedasMarkers.push(marker);
    });

    if (typeof this.overlayLayers.amedas.addLayers === "function") {
      this.overlayLayers.amedas.addLayers(amedasMarkers);
    } else {
      amedasMarkers.forEach((m) => this.overlayLayers.amedas.addLayer(m));
    }

    return amedasMarkers.length;
  },

  // 指定自治体へ地図を移動し、自動でポップアップを表示（クラスタ展開対応）
  focusMuni: function (muniId) {
    if (!muniId) return;

    // 自治体レイヤーが非表示の場合は表示する
    if (this.overlayLayers.prefGov && !this.map.hasLayer(this.overlayLayers.prefGov)) {
      this.map.addLayer(this.overlayLayers.prefGov);
    }
    if (this.overlayLayers.muniGov && !this.map.hasLayer(this.overlayLayers.muniGov)) {
      this.map.addLayer(this.overlayLayers.muniGov);
    }

    const quickBar = document.getElementById("map-layer-quick-bar");
    if (quickBar) {
      const prefBtn = quickBar.querySelector('.layer-pill[data-layer="prefGov"]');
      const muniBtn = quickBar.querySelector('.layer-pill[data-layer="muniGov"]');
      if (prefBtn) prefBtn.classList.add("active");
      if (muniBtn) muniBtn.classList.add("active");
    }

    const marker = this.muniMarkersMap[muniId];
    if (!marker) return;

    // 市区町村マーカークラスタの場合、zoomToShowLayer で自動ズーム展開してポップアップを開く
    if (
      this.overlayLayers.muniGov &&
      typeof this.overlayLayers.muniGov.zoomToShowLayer === "function" &&
      this.overlayLayers.muniGov.hasLayer(marker)
    ) {
      this.overlayLayers.muniGov.zoomToShowLayer(marker, () => {
        setTimeout(() => {
          marker.openPopup();
        }, 100);
      });
    } else {
      // 都道府県庁などの通常レイヤーの場合
      const latLng = marker.getLatLng();
      this.map.flyTo(latLng, 14, { duration: 0.8 });
      setTimeout(() => {
        marker.openPopup();
      }, 850);
    }
  },
  plotEdges: function (edges) {
    this.overlayLayers.edgesRail.clearLayers();
    this.overlayLayers.edgesAir.clearLayers();
    return 0; // 開設当初はエッジ非公開
  },
  plotNodesCategorized: function (nodes) {
    // 開設当初は交通拠点ノードは非公開（自治体ノード・気象観測点のみ公開）
    this.overlayLayers.railways.clearLayers();
    this.overlayLayers.highways.clearLayers();
    this.overlayLayers.roadStations.clearLayers();
    this.overlayLayers.airSea.clearLayers();
    this.overlayLayers.structures.clearLayers();
    this.allNodes = [];
    return 0;
  },

  // 現在表示中の地図領域（ビューポート）およびズームレベルに連動して拠点を描画
  renderViewportNodes: function () {
    // レイヤーのクリア（交通拠点ノードのみ。アメダスはMarkerClusterで独立管理）
    this.overlayLayers.railways.clearLayers();
    this.overlayLayers.highways.clearLayers();
    this.overlayLayers.roadStations.clearLayers();
    this.overlayLayers.airSea.clearLayers();
    this.overlayLayers.structures.clearLayers();

    if (!this.allNodes || this.allNodes.length === 0 || !this.map) return 0;

    const bounds = this.map.getBounds();
    const zoom = this.map.getZoom();

    // 表示領域を少し広げたバウンディングボックス
    const pad = zoom <= 7 ? 0.4 : 0.04;
    const south = bounds.getSouth() - pad;
    const north = bounds.getNorth() + pad;
    const west = bounds.getWest() - pad;
    const east = bounds.getEast() + pad;

    let counts = {
      railway: 0,
      highway: 0,
      roadStation: 0,
      airSea: 0,
      amedas: 0,
      structure: 0,
    };

    // ズームに応じたカテゴリ上限数（低ズーム時は大幅に絞り込み、高ズーム時は余裕を持たせる）
    const categoryLimit = zoom <= 7 ? 50 : (zoom <= 9 ? 150 : (zoom <= 11 ? 400 : 1200));

    for (let i = 0; i < this.allNodes.length; i++) {
      const node = this.allNodes[i];
      if (node.lat == null || node.lon == null) continue;

      // 画面外のノードは即座にスキップ
      if (node.lat < south || node.lat > north || node.lon < west || node.lon > east) {
        continue;
      }

      const cat = String(node.category || "");
      const sub = String(node.sub_category || "");
      const isRoadStation = cat.includes("道の駅") || sub.includes("道の駅") || cat === "交差点";
      const isHighway = !isRoadStation && (cat.includes("IC") || cat.includes("JCT") || cat.includes("高速") || cat.includes("SA") || cat.includes("PA") || sub.includes("高速"));
      const isRailStation = !isRoadStation && !isHighway && (cat.includes("駅") || cat.includes("鉄道") || cat.includes("電停") || sub.includes("駅"));
      const isShinkansen = isRailStation && (sub.includes("新幹線") || cat.includes("新幹線"));
      const isAirport = cat.includes("空港") || sub.includes("空港");
      const isPort = cat.includes("港") || sub.includes("港");
      const isAmedas = cat.includes("気象観測点") || sub.includes("アメダス");
      const isStructure = cat.includes("トンネル") || cat.includes("橋梁") || cat.includes("峠");

      // =====================================================================
      // きめ細かなLOD (Level of Detail) 段階的フィルタリング制御
      // =====================================================================
      // 段階1: zoom <= 7（広域・全国表示）
      // 新幹線駅、主要空港、主要港湾のみに厳選表示し負荷を徹底抑制
      if (zoom <= 7) {
        if (!isShinkansen && !isAirport && !isPort) {
          continue;
        }
      }
      // 段階2: zoom 8〜9（地方・広域都市圏）
      // 新幹線＋全空港＋主要港湾＋主要在来線駅＋主要高速IC
      else if (zoom <= 9) {
        if (isAmedas || isRoadStation || isStructure) {
          continue;
        }
        if (isRailStation && !isShinkansen && (i % 3 !== 0)) {
          continue; // 在来線駅は1/3に間引き
        }
        if (isHighway && (cat === "PA" || cat === "SA" || cat === "都市高速出入口" || (i % 2 !== 0))) {
          continue; // 高速も主要ICに絞る
        }
      }
      // 段階3: zoom 10〜11（都市圏・中縮尺）
      // 全鉄道駅、全高速施設、道の駅、主要アメダス
      else if (zoom <= 11) {
        if (isAmedas && (i % 2 !== 0)) {
          continue;
        }
        if (isStructure && zoom < 11) {
          continue;
        }
      }
      // 段階4: zoom >= 12（詳細・大縮尺）
      // すべての拠点ノードをフル表示

      let targetLayer = null;
      let markerColor = "#2563eb";

      // 1. 道の駅
      if (isRoadStation) {
        if (counts.roadStation >= categoryLimit) continue;
        targetLayer = this.overlayLayers.roadStations;
        markerColor = "#ea580c"; // 橙
        counts.roadStation++;
      }
      // 2. 高速道路施設 (IC/JCT/SA/PA)
      else if (isHighway) {
        if (counts.highway >= categoryLimit) continue;
        targetLayer = this.overlayLayers.highways;
        markerColor = "#15803d"; // 深緑
        counts.highway++;
      }
      // 3. 鉄道駅（新幹線、一般駅、地下鉄、電停）
      else if (isRailStation) {
        if (counts.railway >= categoryLimit) continue;
        targetLayer = this.overlayLayers.railways;
        markerColor = isShinkansen ? "#7c3aed" : "#2563eb"; // 新幹線: 紫、在来線: 青
        counts.railway++;
      }
      // 4. 空港・港湾
      else if (isAirport || isPort) {
        if (counts.airSea >= categoryLimit) continue;
        targetLayer = this.overlayLayers.airSea;
        markerColor = isAirport ? "#0284c7" : "#0d9488"; // 空港: 水色、港: 青緑
        counts.airSea++;
      }
      // 5. 気象観測点 (アメダス)
      else if (isAmedas) {
        if (counts.amedas >= categoryLimit) continue;
        targetLayer = this.overlayLayers.amedas;
        markerColor = "#dc2626"; // 赤
        counts.amedas++;
      }
      // 6. 構造物
      else if (isStructure) {
        if (counts.structure >= categoryLimit) continue;
        targetLayer = this.overlayLayers.structures;
        markerColor = "#78350f"; // 茶
        counts.structure++;
      }
      else {
        if (counts.railway >= categoryLimit) continue;
        targetLayer = this.overlayLayers.railways;
        counts.railway++;
      }

      if (!targetLayer) continue;

      // アイコンの生成
      const badgeIcon = this._createBadgeIcon(node, zoom <= 7, zoom);
      const marker = L.marker([node.lat, node.lon], {
        icon: badgeIcon,
        zIndexOffset: isShinkansen || isAirport ? 200 : (zoom <= 7 ? 50 : 100),
      });

      // ポップアップ内容
      let adjacentHtml = "";
      if (node.adjacent && node.adjacent.length > 0) {
        adjacentHtml = `
          <div style="margin:4px 0; font-size:11px; color:#4b5563;">
            <b>隣接拠点:</b><br>
            ${node.adjacent.map((a) => `
              ${a.direction === "prev" ? "◀ 前:" : "▶ 次:"} ${a.neighbor_name} (${a.dist_km}km)
            `).join("<br>")}
          </div>
        `;
      }

      const popupContent = `
        <div class="popup-title">${node.name || node.name_official || "名称未設定"}</div>
        ${node.yomi ? `<div class="popup-sub">${node.yomi}</div>` : ""}
        <div>
          <span class="popup-tag" style="background:${markerColor}; color:#fff;">${node.category || node.sub_category}</span>
          ${node.muni_name ? `<span class="popup-tag">${node.muni_name}</span>` : ""}
          ${node.elevation != null ? `<span class="popup-tag">標高 ${node.elevation}m</span>` : ""}
        </div>
        ${adjacentHtml}
        <div class="popup-links" style="margin-top:6px; display:flex; flex-direction:column; gap:4px;">
          ${node.sv_url ? `<a href="${node.sv_url}" target="_blank" rel="noopener" style="color:#0284c7;">👀 ストリートビューを開く &raquo;</a>` : ""}
          ${node.obs_url ? `<a href="${node.obs_url}" target="_blank" rel="noopener" style="color:#dc2626;">🌡️ 気象庁公式実況を開く &raquo;</a>` : ""}
          <a href="https://www.google.com/maps/search/?api=1&query=${node.lat},${node.lon}" target="_blank" rel="noopener">🗺️ Google Maps で開く &raquo;</a>
        </div>
      `;

      marker.bindPopup(popupContent, { autoClose: true, closeOnClick: false });
      marker.on("click", () => {
        if (window.App && window.App.openKnowledgeDrawer) {
          window.App.openKnowledgeDrawer(node, "node", true);
        }
      });

      targetLayer.addLayer(marker);
    }

    const totalPlotted = Object.values(counts).reduce((a, b) => a + b, 0);
    const countEl = document.getElementById("map-marker-count");
    if (countEl) {
      countEl.innerText = `表示中の拠点: ${totalPlotted.toLocaleString()} 件 (鉄道 ${counts.railway} / 高速 ${counts.highway} / 道の駅 ${counts.roadStation} / 空海 ${counts.airSea} / 気象 ${counts.amedas})`;
    }

    return totalPlotted;
  },

  // 高精細SVG円形バッジアイコンの取得（プールからキャッシュ再利用）
  _createBadgeIcon: function (node, isOverview, zoom) {
    const cat = String(node.category || "");
    const sub = String(node.sub_category || "");
    const isRoadStation = cat.includes("道の駅") || sub.includes("道の駅") || cat === "交差点";
    const isHighway = !isRoadStation && (cat.includes("IC") || cat.includes("JCT") || cat.includes("高速") || cat.includes("SA") || cat.includes("PA") || sub.includes("高速"));
    const isRailStation = !isRoadStation && !isHighway && (cat.includes("駅") || cat.includes("鉄道") || cat.includes("電停") || sub.includes("駅"));
    const isShinkansen = isRailStation && (sub.includes("新幹線") || cat.includes("新幹線"));
    const isSubway = isRailStation && cat.includes("地下鉄");
    const isTram = isRailStation && cat.includes("電停");

    let iconFile = "train-station.svg";
    let size = isOverview ? 20 : (zoom >= 12 ? 30 : 25);

    if (isRoadStation) {
      iconFile = "roadside-station.svg";
    } else if (isHighway) {
      const isSAPA = cat.includes("SA") || cat.includes("PA");
      iconFile = isSAPA ? "highway-sa.svg" : "highway-ic.svg";
    } else if (isShinkansen) {
      iconFile = "train-shinkansen.svg";
      size = isOverview ? 24 : 32;
    } else if (isSubway) {
      iconFile = "subway.svg";
    } else if (isTram) {
      iconFile = "tram.svg";
    } else if (isRailStation) {
      iconFile = "train-station.svg";
    } else if (cat.includes("空港") || sub.includes("空港")) {
      iconFile = "airport.svg";
      size = isOverview ? 24 : 32;
    } else if (cat.includes("港") || sub.includes("港")) {
      iconFile = "port.svg";
      size = isOverview ? 22 : 28;
    } else if (cat.includes("気象観測点") || sub.includes("アメダス")) {
      iconFile = "weather.svg";
      size = isOverview ? 18 : 24;
    } else if (cat.includes("トンネル") || cat.includes("橋梁") || cat.includes("峠")) {
      iconFile = "structure.svg";
    }

    return this.getBadgeIcon(iconFile, size);
  },

  // =========================================================================
  // 3. 単一路線シーケンス（Wikipedia風BSicon/駅順連動）の描画
  // =========================================================================
  plotRouteSequence: function (route, sequenceNodes) {
    if (this.currentRouteLayers) {
      this.currentRouteLayers.clearLayers();
    } else {
      this.currentRouteLayers = L.layerGroup().addTo(this.map);
    }

    if (!sequenceNodes || sequenceNodes.length === 0) return;

    const latlngs = [];
    const bounds = L.latLngBounds();
    const routeColor = route.color || "#2563eb";

    sequenceNodes.forEach((node, idx) => {
      if (node.lat == null || node.lon == null) return;
      const pt = [node.lat, node.lon];
      latlngs.push(pt);
      bounds.extend(pt);

      let fillColor = routeColor;
      let radius = 6;
      if (idx === 0) {
        fillColor = "#10b981"; // 起点: 緑
        radius = 8;
      } else if (idx === sequenceNodes.length - 1) {
        fillColor = "#ef4444"; // 終点: 赤
        radius = 8;
      }

      const marker = L.circleMarker(pt, {
        radius: radius,
        fillColor: fillColor,
        color: "#ffffff",
        weight: 2,
        opacity: 1,
        fillOpacity: 0.95,
      });

      const popupContent = `
        <div class="popup-title">${node.node_name}</div>
        <div class="popup-sub">${route.name} (順序: ${node.seq}${node.station_number ? ` / ${node.station_number}` : ""})</div>
        <div style="font-size:12px; margin:4px 0;">
          <span>駅間: ${node.km} km</span> | <span>累計: ${node.total_km} km</span>
        </div>
        <div>
          ${node.track_type ? `<span class="popup-tag">${node.track_type}</span>` : ""}
          ${node.muni_name ? `<span class="popup-tag">${node.muni_name}</span>` : ""}
        </div>
      `;

      marker.bindPopup(popupContent);
      marker.on("click", () => {
        if (window.App && window.App.openKnowledgeDrawerById) {
          window.App.openKnowledgeDrawerById(node.node_id, "node");
        }
      });

      this.currentRouteLayers.addLayer(marker);
    });

    // 駅間を結ぶ折れ線
    if (latlngs.length > 1) {
      const line = L.polyline(latlngs, {
        color: routeColor,
        weight: 4.5,
        opacity: 0.9,
      });
      this.currentRouteLayers.addLayer(line);
    }

    if (bounds.isValid()) {
      this.map.fitBounds(bounds, { padding: [50, 50], maxZoom: 13 });
    }

    const countEl = document.getElementById("map-marker-count");
    if (countEl) {
      countEl.innerText = `${route.name} (${sequenceNodes.length} 施設) を強調表示`;
    }
  },
};
