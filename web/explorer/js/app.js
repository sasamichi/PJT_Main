/**
 * 机上探索 Web GIS メインアプリケーション (app.js)
 */

let mapPanes = [];
let isSyncing = false;
let currentTool = "view"; // "view", "point", "coord"
let activeMarker = null;

// デフォルト中心位置（函館駅付近）
const DEFAULT_LAT = 41.7737;
const DEFAULT_LON = 140.7264;
const DEFAULT_ZOOM = 13;

document.addEventListener("DOMContentLoaded", () => {
  initTheme();
  initMapPanes();
  initSplitControls();
  initSubToolbar();
  initLayerToggles();
  initRecordPanel();
});

// --- テーマ（黒・白背景）初期化 ---
function initTheme() {
  const savedTheme = localStorage.getItem("explorer_theme") || "light";
  if (savedTheme === "dark") {
    document.body.classList.add("dark-mode");
    document.getElementById("btn-toggle-theme").innerText = "☀️ 白背景";
  } else {
    document.getElementById("btn-toggle-theme").innerText = "🌙 黒背景";
  }

  document.getElementById("btn-toggle-theme").addEventListener("click", () => {
    document.body.classList.toggle("dark-mode");
    const isDark = document.body.classList.contains("dark-mode");
    localStorage.setItem("explorer_theme", isDark ? "dark" : "light");
    document.getElementById("btn-toggle-theme").innerText = isDark ? "☀️ 白背景" : "🌙 黒背景";
  });
}

// --- 地図ペイン初期化（最大4ペイン作成） ---
function initMapPanes() {
  const configs = [
    { id: "pane-1", mapId: "map-1", defaultTile: "gsi-std", name: "Pane 1" },
    { id: "pane-2", mapId: "map-2", defaultTile: "gsi-photo", name: "Pane 2" },
    { id: "pane-3", mapId: "map-3", defaultTile: "gsi-pale", name: "Pane 3" },
    { id: "pane-4", mapId: "map-4", defaultTile: "osm-std", name: "Pane 4" }
  ];

  configs.forEach((cfg, idx) => {
    const map = L.map(cfg.mapId, {
      center: [DEFAULT_LAT, DEFAULT_LON],
      zoom: DEFAULT_ZOOM,
      zoomControl: false // コントロールは独自配置
    });

    // ズームコントロールを右下に
    L.control.zoom({ position: "bottomright" }).addTo(map);

    // タイル設定
    const tileLayer = createTileLayer(cfg.defaultTile);
    tileLayer.addTo(map);

    // レイヤーグループ
    const nodeLayer = L.layerGroup().addTo(map);
    const wikiLayer = L.layerGroup().addTo(map);

    const paneObj = {
      index: idx,
      id: cfg.id,
      map: map,
      tileLayer: tileLayer,
      nodeLayer: nodeLayer,
      wikiLayer: wikiLayer,
      currentTile: cfg.defaultTile
    };
    mapPanes.push(paneObj);

    // 地図イベントリスナー（同期 ＆ クリック）
    setupMapEvents(paneObj);
    setupPaneControls(paneObj);
  });

  // 初回レイアウトは「2画面（左右）」
  setSplitLayout("split-h");
  loadNodesToMaps();

  setTimeout(() => {
    mapPanes.forEach(p => p.map.invalidateSize());
  }, 300);
}

function setupMapEvents(paneObj) {
  const map = paneObj.map;

  // 連動同期 (Pan & Zoom)
  const syncHandler = () => {
    if (isSyncing) return;
    isSyncing = true;
    const center = map.getCenter();
    const zoom = map.getZoom();

    mapPanes.forEach(other => {
      if (other.index !== paneObj.index) {
        other.map.setView(center, zoom, { animate: false });
      }
    });
    isSyncing = false;
  };

  map.on("move", syncHandler);
  map.on("zoom", syncHandler);

  // 地図クリックイベント
  map.on("click", (e) => {
    const lat = e.latlng.lat;
    const lon = e.latlng.lng;

    // 代表座標の入力反映
    setClickedCoordinate(lat, lon);

    // クリック地点にピン
    if (activeMarker) {
      activeMarker.remove();
    }
    activeMarker = L.marker([lat, lon], {
      icon: L.divIcon({
        className: 'custom-pin',
        html: '<div style="background:#2563eb; width:12px; height:12px; border-radius:50%; border:2px solid #fff; box-shadow:0 0 4px rgba(0,0,0,0.5);"></div>',
        iconSize: [12, 12],
        iconAnchor: [6, 6]
      })
    }).addTo(map);

    // 記録パネルを開く
    const panel = document.getElementById("record-panel");
    if (!panel.classList.contains("open")) {
      panel.classList.add("open");
      document.getElementById("btn-toggle-record").classList.add("active");
    }
  });
}

function setupPaneControls(paneObj) {
  // タイル切り替え
  const selTile = document.getElementById(`select-tile-${paneObj.index + 1}`);
  if (selTile) {
    // 選択肢の追加
    selTile.innerHTML = "";
    Object.keys(TILE_PROVIDERS).forEach(k => {
      const p = TILE_PROVIDERS[k];
      const opt = document.createElement("option");
      opt.value = k;
      opt.innerText = p.name;
      if (k === paneObj.currentTile) opt.selected = true;
      selTile.appendChild(opt);
    });

    selTile.addEventListener("change", (e) => {
      paneObj.map.removeLayer(paneObj.tileLayer);
      paneObj.tileLayer = createTileLayer(e.target.value);
      paneObj.tileLayer.addTo(paneObj.map);
      paneObj.currentTile = e.target.value;
    });
  }

  // 地名検索
  const searchBtn = document.getElementById(`btn-search-${paneObj.index + 1}`);
  const searchInput = document.getElementById(`input-search-${paneObj.index + 1}`);
  if (searchBtn && searchInput) {
    const doSearch = async () => {
      const q = searchInput.value.trim();
      if (!q) return;
      const results = await apiSearchLocation(q);
      if (results && results.length > 0) {
        const top = results[0];
        paneObj.map.setView([top.lat, top.lon], 15);
        showToast(`検索: ${top.title} へ移動しました`);
      } else {
        showToast("該当する場所が見つかりませんでした。");
      }
    };

    searchBtn.addEventListener("click", doSearch);
    searchInput.addEventListener("keypress", (e) => {
      if (e.key === "Enter") doSearch();
    });
  }
}

// --- 画面分割制御 ---
function initSplitControls() {
  const btns = document.querySelectorAll(".split-btn");
  btns.forEach(btn => {
    btn.addEventListener("click", (e) => {
      btns.forEach(b => b.classList.remove("active"));
      const target = e.currentTarget;
      target.classList.add("active");
      const layout = target.getAttribute("data-layout");
      setSplitLayout(layout);
    });
  });
}

function setSplitLayout(layout) {
  const grid = document.getElementById("map-grid");
  grid.className = ""; // リセット

  const p1 = document.getElementById("pane-1");
  const p2 = document.getElementById("pane-2");
  const p3 = document.getElementById("pane-3");
  const p4 = document.getElementById("pane-4");

  if (layout === "single") {
    grid.classList.add("layout-single");
    p1.style.display = "block";
    p2.style.display = "none";
    p3.style.display = "none";
    p4.style.display = "none";
    document.getElementById("badge-screens").innerText = "1 地図画面";
  } else if (layout === "split-h") {
    grid.classList.add("layout-split-h");
    p1.style.display = "block";
    p2.style.display = "block";
    p3.style.display = "none";
    p4.style.display = "none";
    document.getElementById("badge-screens").innerText = "2 地図画面";
  } else if (layout === "split-v") {
    grid.classList.add("layout-split-v");
    p1.style.display = "block";
    p2.style.display = "block";
    p3.style.display = "none";
    p4.style.display = "none";
    document.getElementById("badge-screens").innerText = "2 地図画面";
  } else if (layout === "triple") {
    grid.classList.add("layout-triple");
    p1.style.display = "block";
    p2.style.display = "block";
    p3.style.display = "block";
    p4.style.display = "none";
    document.getElementById("badge-screens").innerText = "3 地図画面";
  } else if (layout === "quad") {
    grid.classList.add("layout-quad");
    p1.style.display = "block";
    p2.style.display = "block";
    p3.style.display = "block";
    p4.style.display = "block";
    document.getElementById("badge-screens").innerText = "4 地図画面";
  }

  // Leafletのコンテナサイズ変更通知
  setTimeout(() => {
    mapPanes.forEach(p => p.map.invalidateSize());
  }, 100);
}

// --- サブツールバー ---
function initSubToolbar() {
  const toolBtns = document.querySelectorAll(".tool-btn");
  toolBtns.forEach(btn => {
    btn.addEventListener("click", (e) => {
      toolBtns.forEach(b => b.classList.remove("active"));
      const target = e.currentTarget;
      target.classList.add("active");
      currentTool = target.getAttribute("data-tool");
      
      if (currentTool === "other-map") {
        const center = mapPanes[0].map.getCenter();
        const url = `https://www.google.com/maps/@${center.lat},${center.lon},15z`;
        window.open(url, "_blank");
      }
    });
  });
}

// --- レイヤー表示制御 ---
function initLayerToggles() {
  const chkPoints = document.getElementById("toggle-layer-points");
  const chkWiki = document.getElementById("toggle-layer-wiki");

  chkPoints.addEventListener("change", (e) => {
    mapPanes.forEach(p => {
      if (e.target.checked) {
        p.nodeLayer.addTo(p.map);
      } else {
        p.map.removeLayer(p.nodeLayer);
      }
    });
  });

  chkWiki.addEventListener("change", async (e) => {
    if (e.target.checked) {
      loadWikidataToMaps();
    } else {
      mapPanes.forEach(p => p.wikiLayer.clearLayers());
    }
  });
}

// --- 交通拠点を地図にロード ---
async function loadNodesToMaps() {
  try {
    const data = await apiFetchNodes("JP");
    const nodes = data.nodes || [];

    mapPanes.forEach(p => {
      p.nodeLayer.clearLayers();
      nodes.forEach(nd => {
        try {
          const lat = parseFloat(nd["緯度"]);
          const lon = parseFloat(nd["経度"]);
          const name = nd["日本語名"] || nd["公用語名"];
          const marker = L.circleMarker([lat, lon], {
            radius: 4,
            color: "#2563eb",
            fillColor: "#60a5fa",
            fillOpacity: 0.8,
            weight: 1
          }).bindPopup(`<strong>${name}</strong><br>種別: ${nd["種別"]}<br>ID: ${nd["node_id"]}`);
          p.nodeLayer.addLayer(marker);
        } catch (e) {}
      });
    });
  } catch (err) {
    console.error("Failed to load nodes", err);
  }
}

// --- Wikidata史跡を地図にロード ---
async function loadWikidataToMaps() {
  const center = mapPanes[0].map.getCenter();
  showToast("周辺のWikidata史跡を取得中...");
  try {
    const data = await apiFetchWikidata(center.lat, center.lon, 15);
    const items = data.items || [];
    mapPanes.forEach(p => {
      p.wikiLayer.clearLayers();
      items.forEach(w => {
        const marker = L.circleMarker([w.lat, w.lon], {
          radius: 5,
          color: "#9333ea",
          fillColor: "#c084fc",
          fillOpacity: 0.8,
          weight: 1
        }).bindPopup(`<strong>${w.name}</strong><br><a href="${w.url}" target="_blank">Wikidataリンク</a>`);
        p.wikiLayer.addLayer(marker);
      });
    });
    showToast(`Wikidataスポットを ${items.length} 件表示しました`);
  } catch (err) {
    console.error(err);
  }
}

// ログから地図移動
window.jumpToCoord = function(lat, lon) {
  mapPanes.forEach(p => p.map.setView([lat, lon], 15));
  if (activeMarker) activeMarker.remove();
  activeMarker = L.marker([lat, lon]).addTo(mapPanes[0].map);
};
