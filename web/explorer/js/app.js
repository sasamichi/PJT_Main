/**
 * 机上探索 Web GIS メインアプリケーション (app.js)
 * 地図ペイン（1/2/4画面）・連動同期・ツール・登録拠点／追加データ／Wikidataの重畳表示
 * 路線ツアーモード: 起点から終点へ1駅ずつ進むモード（［◀ 前駅］［次駅 ▶］、駅間キロ、自動ズーム）
 */

// --- 定数 ---
const COLORS = {
  node: "#2563eb",
  mine: "#f97316",
  route: "#ef4444",
  wiki: "#a855f7",
  edge: "#3b82f6",
  spot: "#b91c1c",
  tour: "#10b981"
};
const COUNTRY_CENTERS = {
  JP: [35.6812, 139.7671], // 東京
  AT: [48.2082, 16.3738],  // ウィーン
  CH: [46.9480, 7.4474],   // ベルン
  TW: [25.0330, 121.5654]  // 台北
};
const DEFAULT_ZOOM = 13;
const PANE_DEFAULT_TILES = ["gsi-std", "gsi-photo", "gsi-pale", "osm-std"];
const LAYOUTS = {
  "single":  { cls: "layout-single",  panes: 1 },
  "split-h": { cls: "layout-split-h", panes: 2 },
  "split-v": { cls: "layout-split-v", panes: 2 },
  "quad":    { cls: "layout-quad",    panes: 4 }
};
const NODE_RELOAD_M = 10000;  // 拠点：10km以上動いたら再取得（取得半径35km）
const WIKI_RELOAD_M = 5000;   // Wikidata：5km以上動いたら再取得（取得半径15km）

// --- 状態 ---
const draft = { type: "point", point: null, route: [], editingId: null };

let mapPanes = [];
let currentTool = "view";
let currentMode = "tour"; // 'tour' | 'free'
let isSyncing = false;
let nearNodes = [];
let allEdges = [];
let themeSpots = [];
let wikiItems = [];
let lastNodeCenter = null;
let lastWikiCenter = null;
let nodeSeq = 0;
let wikiSeq = 0;
let viewTimer = null;
let currentDetectedCountry = "JP";

// 路線ツアー状態 & 全局ノードキャッシュ
const nodeMasterCache = new Map();

let tourState = {
  activeRouteId: "",
  sequence: [],
  currentIndex: 0
};

function resolveNodeInfo(nodeId, edgeName, edgeLat, edgeLon) {
  const cached = nodeMasterCache.get(nodeId);
  const near = nearNodes.find((n) => n.node_id === nodeId);

  // 名称: ID文字列以外の意味のある日本語名・名称を優先
  let name = "";
  if (edgeName && edgeName !== nodeId && !edgeName.match(/^[A-Z]{2}-ND-\d+$/)) {
    name = edgeName;
  } else if (cached && cached.name && !cached.name.match(/^[A-Z]{2}-ND-\d+$/)) {
    name = cached.name;
  } else if (near) {
    name = near["日本語名"] || near["名称"] || near["公用語名"] || "";
  }
  if (!name) name = (cached && cached.name) || edgeName || nodeId;

  // 座標: エッジ -> キャッシュ -> nearNodes
  let lat = null, lon = null;
  if (edgeLat != null && !isNaN(parseFloat(edgeLat))) {
    lat = parseFloat(edgeLat);
  } else if (cached && cached.lat != null && !isNaN(cached.lat)) {
    lat = cached.lat;
  } else if (near && near["緯度"] && !isNaN(parseFloat(near["緯度"]))) {
    lat = parseFloat(near["緯度"]);
  }

  if (edgeLon != null && !isNaN(parseFloat(edgeLon))) {
    lon = parseFloat(edgeLon);
  } else if (cached && cached.lon != null && !isNaN(cached.lon)) {
    lon = cached.lon;
  } else if (near && near["経度"] && !isNaN(parseFloat(near["経度"]))) {
    lon = parseFloat(near["経度"]);
  }

  return { name, lat, lon };
}

document.addEventListener("DOMContentLoaded", () => {
  initTheme();
  initMapPanes();
  initSplitControls();
  initToolbar();
  initTourControls();
  initLayerToggles();
  initRecordPanel();
  initContextMenu();
  initSvDrawer();
  loadAllEdges();
  loadThemeSpots();
});

// ---------------------------------------------------------------
// テーマ（黒・白）
// ---------------------------------------------------------------
function applyTheme(theme) {
  const dark = theme === "dark";
  document.body.classList.toggle("dark-mode", dark);
  localStorage.setItem("explorer_theme", theme);
  $("btn-toggle-theme").innerText = dark ? "☀️ 白背景" : "🌙 黒背景";
  const linkAdmin = $("link-admin");
  if (linkAdmin) linkAdmin.href = `http://localhost:8501/?theme=${theme}`;
}

function initTheme() {
  const requested = new URLSearchParams(location.search).get("theme");
  applyTheme(requested || localStorage.getItem("explorer_theme") || "light");
  $("btn-toggle-theme").addEventListener("click", () =>
    applyTheme(document.body.classList.contains("dark-mode") ? "light" : "dark"));
}

// ---------------------------------------------------------------
// 地図ペイン
// ---------------------------------------------------------------
function createPaneElement(n) {
  const pane = document.createElement("div");
  pane.className = "map-pane";
  pane.innerHTML = `
    <div class="pane-floating-header">
      <div class="pane-search-box">
        <input type="text" id="input-search-${n}" placeholder="地名、住所、歴史スポットを検索">
        <button id="btn-search-${n}">検索</button>
      </div>
      <select class="pane-tile-select" id="select-tile-${n}"></select>
    </div>
    <div class="map-container" id="map-${n}"></div>
    <div class="pane-badge">Pane ${n}</div>`;
  $("map-grid").appendChild(pane);
  return pane;
}

function initMapPanes() {
  PANE_DEFAULT_TILES.forEach((tileKey, idx) => {
    const n = idx + 1;
    const el = createPaneElement(n);
    const map = L.map(`map-${n}`, { center: COUNTRY_CENTERS.JP, zoom: DEFAULT_ZOOM, zoomControl: false, preferCanvas: true });
    L.control.zoom({ position: "bottomright" }).addTo(map);

    const pane = {
      index: idx, el, map, currentTile: tileKey, visible: true,
      tileLayer: createTileLayer(tileKey).addTo(map),
      layers: {
        edges: L.layerGroup().addTo(map),
        nodes: L.layerGroup().addTo(map),
        spots: L.layerGroup().addTo(map),
        mine:  L.layerGroup().addTo(map),
        wiki:  L.layerGroup().addTo(map),
        draft: L.layerGroup().addTo(map),
        tour:  L.layerGroup().addTo(map)
      }
    };
    mapPanes.push(pane);
    setupMapEvents(pane);
    setupPaneControls(pane);
  });

  setLayout("split-h");
  lastNodeCenter = lastWikiCenter = L.latLng(COUNTRY_CENTERS.JP);
  loadNodes(lastNodeCenter);
  loadWiki(lastWikiCenter);
}

function syncAll(center, zoom, exceptIndex = -1) {
  isSyncing = true;
  mapPanes.forEach((p) => { if (p.index !== exceptIndex) p.map.setView(center, zoom, { animate: false }); });
  isSyncing = false;
}

function setupMapEvents(pane) {
  const map = pane.map;
  let frame = null;

  map.on("move", () => {
    if (isSyncing) return;
    cancelAnimationFrame(frame);
    frame = requestAnimationFrame(() => syncAll(map.getCenter(), map.getZoom(), pane.index));
  });

  map.on("moveend", () => {
    clearTimeout(viewTimer);
    viewTimer = setTimeout(() => {
      const c = map.getCenter();
      if (!lastNodeCenter || c.distanceTo(lastNodeCenter) > NODE_RELOAD_M) { lastNodeCenter = c; loadNodes(c); }
      if (!lastWikiCenter || c.distanceTo(lastWikiCenter) > WIKI_RELOAD_M) { lastWikiCenter = c; loadWiki(c); }

      // 地図中心から国を自動判定してタイルセレクタを優先並び替え
      if (typeof detectCountryFromCoord === "function") {
        const detected = detectCountryFromCoord(c.lat, c.lng);
        if (detected && detected !== currentDetectedCountry) {
          updateAllTileSelectors(detected);
        }
      }
    }, 400);
  });

  map.on("click", (e) => handleMapClick(e.latlng));
  map.on("dblclick", () => { if (currentTool === "route") finishRoute(); });
  map.on("popupopen", (e) => e.popup.getElement().addEventListener("click", handleLogAction));
}

function updateTileSelector(pane, countryCode) {
  const n = pane.index + 1;
  const select = $(`select-tile-${n}`);
  if (!select) return;

  const currentVal = pane.currentTile;
  select.innerHTML = "";

  const sortedGroups = typeof getSortedTileGroups === "function"
    ? getSortedTileGroups(countryCode)
    : (typeof TILE_GROUPS !== "undefined" ? TILE_GROUPS : []);

  if (sortedGroups.length > 0) {
    sortedGroups.forEach((grp) => {
      const optgroup = document.createElement("optgroup");
      const isCurrent = grp.countryCode === countryCode && countryCode !== "Global";
      optgroup.label = isCurrent ? `📍 ${grp.group} (現在地)` : grp.group;
      grp.tiles.forEach((key) => {
        const p = TILE_PROVIDERS[key];
        if (p) {
          const opt = new Option(p.name, key, false, key === currentVal);
          optgroup.appendChild(opt);
        }
      });
      select.appendChild(optgroup);
    });
  } else {
    Object.entries(TILE_PROVIDERS).forEach(([key, p]) => {
      select.add(new Option(p.name, key, false, key === currentVal));
    });
  }

  select.value = currentVal;
}

function updateAllTileSelectors(countryCode) {
  if (!countryCode) return;
  currentDetectedCountry = countryCode;
  mapPanes.forEach((p) => updateTileSelector(p, countryCode));
}

function setupPaneControls(pane) {
  const n = pane.index + 1;

  updateTileSelector(pane, currentDetectedCountry);

  const select = $(`select-tile-${n}`);
  select.addEventListener("change", (e) => {
    pane.map.removeLayer(pane.tileLayer);
    pane.tileLayer = createTileLayer(e.target.value).addTo(pane.map);
    pane.tileLayer.bringToBack();
    pane.currentTile = e.target.value;
  });

  const input = $(`input-search-${n}`);
  const doSearch = async () => {
    const q = input.value.trim();
    if (!q) return;
    showToast(`検索中: ${q}...`);
    try {
      const results = await apiSearchLocation(q);
      if (results.length) {
        focusOn(results[0].lat, results[0].lon, 14);
        showToast(`${results[0].title} へ移動しました`);
      } else {
        showToast("該当する場所が見つかりませんでした");
      }
    } catch (err) {
      showToast("検索に失敗しました: " + err.message);
    }
  };
  $(`btn-search-${n}`).addEventListener("click", doSearch);
  input.addEventListener("keydown", (e) => { if (e.key === "Enter") doSearch(); });
}

function focusOn(lat, lon, minZoom = DEFAULT_ZOOM) {
  const map = mapPanes[0].map;
  map.setView([lat, lon], Math.max(map.getZoom(), minZoom));
}

// ---------------------------------------------------------------
// 画面分割（1 / 2左右 / 2上下 / 4）
// ---------------------------------------------------------------
function initSplitControls() {
  document.querySelectorAll(".split-btn").forEach((btn) =>
    btn.addEventListener("click", () => setLayout(btn.dataset.layout)));
}

function setLayout(name) {
  const cfg = LAYOUTS[name];
  $("map-grid").className = cfg.cls;
  document.querySelectorAll(".split-btn").forEach((b) => b.classList.toggle("active", b.dataset.layout === name));
  $("badge-screens").innerText = `${cfg.panes} 地図画面`;
  mapPanes.forEach((p) => { p.visible = p.index < cfg.panes; p.el.style.display = p.visible ? "block" : "none"; });

  setTimeout(() => {
    const ref = mapPanes[0].map;
    mapPanes.forEach((p) => { if (p.visible) p.map.invalidateSize(); });
    syncAll(ref.getCenter(), ref.getZoom(), 0);
    renderAll();
  }, 100);
}

// ---------------------------------------------------------------
// ツールバー
// ---------------------------------------------------------------
function initToolbar() {
  document.querySelectorAll(".tool-btn[data-tool]").forEach((btn) =>
    btn.addEventListener("click", () => setTool(btn.dataset.tool)));

  $("btn-other-map").addEventListener("click", () => {
    const map = mapPanes[0].map, c = map.getCenter();
    window.open(`https://www.google.com/maps/@${c.lat},${c.lng},${map.getZoom()}z`, "_blank");
  });
}

function setTool(tool) {
  if (draft.editingId && (tool === "point" || tool === "route") && tool !== draft.type) {
    showToast("編集中は記録種別を変更できません");
    return;
  }
  currentTool = tool;
  document.querySelectorAll(".tool-btn[data-tool]").forEach((b) => b.classList.toggle("active", b.dataset.tool === tool));
  $("map-grid").dataset.tool = tool;
  mapPanes.forEach((p) => (tool === "route" ? p.map.doubleClickZoom.disable() : p.map.doubleClickZoom.enable()));

  if (tool === "point" || tool === "route") {
    draft.type = tool;
    draftChanged();
  }
}

function handleMapClick(latlng) {
  if (currentTool === "point") {
    setDraftPoint(latlng.lat, latlng.lng);
    openRecordPanel();
  } else if (currentTool === "route") {
    draft.route.push([latlng.lat, latlng.lng]);
    draftChanged();
    openRecordPanel();
  } else if (currentTool === "coord") {
    navigator.clipboard.writeText(`${latlng.lat.toFixed(6)}, ${latlng.lng.toFixed(6)}`);
    showToast(`座標をコピー: ${latlng.lat.toFixed(6)}, ${latlng.lng.toFixed(6)}`);
  }
}

function setDraftPoint(lat, lon) {
  draft.type = "point";
  draft.point = [lat, lon];
  draftChanged();
}

function finishRoute() {
  draft.route.pop();
  setTool("view");
  draftChanged();
}

function draftChanged() {
  setTimeout(() => { renderOverlays(); onDraftChanged(); }, 0);
}

// ---------------------------------------------------------------
// アイコンキャッシュ（L.icon プーリングによるパフォーマンス最適化）
// ---------------------------------------------------------------
const explorerIconCache = {};
function getExplorerIcon(file, size = 22) {
  const key = `${file}_${size}`;
  if (!explorerIconCache[key]) {
    explorerIconCache[key] = L.icon({
      iconUrl: `assets/icons/${file}`,
      iconSize: [size, size],
      iconAnchor: [size / 2, size / 2],
      popupAnchor: [0, -Math.round(size / 2)],
      className: "custom-map-icon",
    });
  }
  return explorerIconCache[key];
}

// ---------------------------------------------------------------
// 描画：追加データ（オレンジ点・赤線）／入力中データ
// ---------------------------------------------------------------
const pinIcon = (isDraft) => getExplorerIcon(isDraft ? "pin-draft.svg" : "pin-saved.svg", 22);
const vertexIcon = L.divIcon({ className: "", html: '<div class="vertex-dot"></div>', iconSize: [12, 12], iconAnchor: [6, 6] });

function drawSavedLog(pane, log) {
  if (log["記録種別"] === "ルート") {
    const pts = parseRoute(log["ルート座標"]);
    if (pts.length < 2) return;
    L.polyline(pts, { color: COLORS.route, weight: 4, opacity: 0.9 })
      .bindPopup(logPopupHtml(log)).addTo(pane.layers.mine);
  } else {
    const loc = logLocation(log);
    if (!loc) return;
    L.marker(loc, { icon: pinIcon(false), draggable: true, title: log["タイトル"] })
      .bindPopup(logPopupHtml(log))
      .on("dragend", (e) => { const ll = e.target.getLatLng(); moveLog(log.log_id, ll.lat, ll.lng); })
      .addTo(pane.layers.mine);
  }
}

function drawDraft(pane) {
  const layer = pane.layers.draft;
  if (draft.type === "point" && draft.point) {
    L.marker(draft.point, { icon: pinIcon(true), draggable: true })
      .on("dragend", (e) => { const ll = e.target.getLatLng(); setDraftPoint(ll.lat, ll.lng); })
      .addTo(layer);
  }
  if (draft.type === "route" && draft.route.length) {
    L.polyline(draft.route, { color: COLORS.route, weight: 4, dashArray: "8 6" }).addTo(layer);
    draft.route.forEach((pt, i) => {
      L.marker(pt, { icon: vertexIcon, draggable: true, title: "ドラッグで移動 / 右クリックで削除" })
        .on("dragend", (e) => { const ll = e.target.getLatLng(); draft.route[i] = [ll.lat, ll.lng]; draftChanged(); })
        .on("contextmenu", () => { draft.route.splice(i, 1); draftChanged(); })
        .addTo(layer);
    });
  }
}

function renderOverlays() {
  mapPanes.forEach((p) => {
    p.layers.mine.clearLayers();
    p.layers.draft.clearLayers();
    if (!p.visible) return;
    appLogs.forEach((log) => { if (log.log_id !== draft.editingId) drawSavedLog(p, log); });
    drawDraft(p);
  });
  const routes = appLogs.filter((l) => l["記録種別"] === "ルート").length;
  $("badge-points").innerText = `${appLogs.length - routes} ポイント`;
  $("badge-routes").innerText = `${routes} ルート`;
}

// ---------------------------------------------------------------
// 描画：登録拠点（青）／Wikidata（紫）／エッジ（青線）／中世史跡（赤）
// ---------------------------------------------------------------
function drawNodes() {
  mapPanes.forEach((p) => {
    p.layers.nodes.clearLayers();
    if (!p.visible) return;
    nearNodes.forEach((nd) => {
      const lat = parseFloat(nd["緯度"]), lon = parseFloat(nd["経度"]);
      if (!Number.isFinite(lat) || !Number.isFinite(lon)) return;
      const name = nd["名称"] || nd["日本語名"] || nd["公用語名"] || nd.node_id;
      const cat = String(nd["種別"] || "");
      const sub = String(nd["大分類"] || nd["細品種別"] || "");

      let iconFile = "train-station.svg";
      if (cat.includes("道の駅") || sub.includes("道の駅")) iconFile = "roadside-station.svg";
      else if (cat.includes("SA") || cat.includes("PA")) iconFile = "highway-sa.svg";
      else if (cat.includes("IC") || cat.includes("JCT") || cat.includes("高速")) iconFile = "highway-ic.svg";
      else if (sub.includes("新幹線") || cat.includes("新幹線")) iconFile = "train-shinkansen.svg";
      else if (cat.includes("地下鉄")) iconFile = "subway.svg";
      else if (cat.includes("電停")) iconFile = "tram.svg";
      else if (cat.includes("駅") || cat.includes("鉄道")) iconFile = "train-station.svg";
      else if (cat.includes("空港") || sub.includes("空港")) iconFile = "airport.svg";
      else if (cat.includes("港") || sub.includes("港")) iconFile = "port.svg";
      else if (cat.includes("気象観測点") || sub.includes("アメダス")) iconFile = "weather.svg";
      else if (cat.includes("トンネル") || cat.includes("橋梁") || cat.includes("峠")) iconFile = "structure.svg";

      const nodeIcon = getExplorerIcon(iconFile, 22);

      L.marker([lat, lon], { icon: nodeIcon })
        .bindPopup(`<strong>${esc(name)}</strong><br>種別: ${esc(cat)}<br>ID: ${esc(nd.node_id)}`)
        .addTo(p.layers.nodes);
    });
  });
  $("badge-nodes").innerText = `周辺拠点 ${nearNodes.length}`;
}

function drawWiki() {
  mapPanes.forEach((p) => {
    p.layers.wiki.clearLayers();
    if (!p.visible) return;
    wikiItems.forEach((w) => {
      L.circleMarker([w.lat, w.lon], { radius: 5, color: "#7e22ce", fillColor: COLORS.wiki, fillOpacity: 0.85, weight: 1.5 })
        .bindPopup(`<strong>${esc(w.name)}</strong><br><a href="${esc(w.url)}" target="_blank" rel="noopener">Wikidata</a>`)
        .addTo(p.layers.wiki);
    });
  });
}

function drawAllEdges() {
  mapPanes.forEach((pane) => {
    pane.layers.edges.clearLayers();
    allEdges.forEach((e) => {
      if (e["ライン座標_geojson"]) {
        try {
          const geo = JSON.parse(e["ライン座標_geojson"]);
          const lineLayer = L.geoJSON(geo, {
            style: { color: COLORS.edge, weight: 3, opacity: 0.75 }
          });
          const fromName = e["from_node_name"] || e["from_node_id"];
          const toName = e["to_node_name"] || e["to_node_id"];
          const dist = e["距離_km"] ? `${e["距離_km"]} km` : "";
          lineLayer.bindPopup(`<strong>${esc(fromName)} ⇆ ${esc(toName)}</strong><br>距離: ${esc(dist)}<br>路線ID: ${esc(e.route_id)}`);
          pane.layers.edges.addLayer(lineLayer);
        } catch (err) {}
      }
    });
  });
}

function drawThemeSpots() {
  mapPanes.forEach((pane) => {
    pane.layers.spots.clearLayers();
    themeSpots.forEach((s) => {
      const lat = parseFloat(s["緯度"]), lon = parseFloat(s["経度"]);
      if (isNaN(lat) || isNaN(lon)) return;
      const name = s["名称"] || s["日本語名"] || s["公用語名"] || "史跡";
      
      const spotIcon = getExplorerIcon("spot-castle.svg", 24);

      L.marker([lat, lon], { icon: spotIcon })
        .bindPopup(`<strong>${esc(name)}</strong><br>時代: ${esc(s["時代区分"] || "")}<br>種別: ${esc(s["種別"] || "")}`)
        .addTo(pane.layers.spots);
    });
  });
}

function renderAll() {
  drawAllEdges();
  drawNodes();
  drawThemeSpots();
  drawWiki();
  renderOverlays();
}

async function loadNodes(center) {
  const seq = ++nodeSeq;
  try {
    const z = mapPanes[0] ? mapPanes[0].map.getZoom() : DEFAULT_ZOOM;
    const radiusKm = z >= 14 ? 20 : z >= 12 ? 35 : z >= 10 ? 55 : 80;
    const data = await apiFetchNodes(center.lat.toFixed(4), center.lng.toFixed(4), radiusKm);
    if (seq !== nodeSeq) return;
    nearNodes = data.nodes || [];
    drawNodes();
    refreshNodeOptions(nearNodes);
  } catch (err) {
    showToast("拠点の取得に失敗しました: " + err.message);
  }
}

async function loadWiki(center) {
  if (!$("toggle-layer-wiki").checked) return;
  const seq = ++wikiSeq;
  $("badge-wiki").innerText = "Wikidata 取得中…";
  try {
    const data = await apiFetchWikidata(center.lat, center.lng, 15);
    if (seq !== wikiSeq) return;
    wikiItems = data.items || [];
    drawWiki();
    $("badge-wiki").innerText = `Wikidata ${wikiItems.length}`;
  } catch (err) {
    if (seq !== wikiSeq) return;
    $("badge-wiki").innerText = "Wikidata 取得失敗";
    showToast("Wikidataの取得に失敗しました（地図移動で再試行されます）: " + err.message);
    lastWikiCenter = null;
  }
}

async function loadAllEdges() {
  try {
    const edgeData = await apiFetchEdges();
    allEdges = edgeData.edges || [];
    drawAllEdges();
  } catch (err) {}
  loadTourRouteOptions();
}

async function loadThemeSpots() {
  try {
    const data = await apiFetchThemeSpots();
    themeSpots = data.spots || [];
    drawThemeSpots();
  } catch (err) {}
}

// ---------------------------------------------------------------
// 探索モード ＆ 路線ツアー機能
// ---------------------------------------------------------------
function initTourControls() {
  $("btn-mode-tour").addEventListener("click", () => setExploreMode("tour"));
  $("btn-mode-free").addEventListener("click", () => setExploreMode("free"));

  $("btn-tour-prev").addEventListener("click", tourPrev);
  $("btn-tour-next").addEventListener("click", tourNext);

  $("tour-route-select").addEventListener("change", (e) => {
    const rid = e.target.value;
    if (rid) loadTourRoute(rid);
  });
}

function setExploreMode(mode) {
  currentMode = mode;
  $("btn-mode-tour").classList.toggle("active", mode === "tour");
  $("btn-mode-free").classList.toggle("active", mode === "free");
  $("tour-nav-bar").style.display = mode === "tour" ? "flex" : "none";
  showToast(mode === "tour" ? "路線ツアーモードを開始しました" : "フリー探索モードに切り替えました");
}

async function loadTourRouteOptions() {
  const select = $("tour-route-select");
  select.innerHTML = '<option value="">路線を選択...</option>';
  try {
    const rData = await apiFetchRoutes("JP");
    const routes = rData.routes || [];

    // 新幹線全線 & 国内主要航空路のroute_idを優先
    const featuredRids = [
      "JP-RT-001127", // 東海道新幹線
      "JP-RT-001028", // 山陽新幹線
      "JP-RT-001208", // 東北新幹線
      "JP-RT-001181", // 上越新幹線
      "JP-RT-001222", // 北陸新幹線
      "JP-RT-000881", // 九州新幹線
      "JP-RT-001362", // 西九州新幹線
      "JP-RT-001360", // 北海道新幹線
      "JP-RT-001395", // 東京(羽田) - 札幌(新千歳)
      "JP-RT-001396", // 東京(羽田) - 福岡
      "JP-RT-001397", // 東京(羽田) - 那覇
      "JP-RT-001399", // 東京(羽田) - 大阪(伊丹)
    ];

    const edgeRouteIds = new Set(allEdges.map((e) => e.route_id).filter(Boolean));

    routes.sort((a, b) => {
      const aFeatured = featuredRids.includes(a.route_id);
      const bFeatured = featuredRids.includes(b.route_id);
      if (aFeatured && !bFeatured) return -1;
      if (!aFeatured && bFeatured) return 1;

      const aHasEdges = edgeRouteIds.has(a.route_id);
      const bHasEdges = edgeRouteIds.has(b.route_id);
      if (aHasEdges && !bHasEdges) return -1;
      if (!aHasEdges && bHasEdges) return 1;

      return 0;
    });

    routes.slice(0, 150).forEach((r) => {
      const opt = document.createElement("option");
      opt.value = r.route_id;
      const isF = featuredRids.includes(r.route_id);
      const hasE = edgeRouteIds.has(r.route_id);
      const mark = isF ? "★ " : hasE ? "◆ " : "";
      opt.innerText = `${mark}${r["日本語名"] || r["公用語名"] || r["路線名"]} (${r.route_id})`;
      select.appendChild(opt);
    });

    // 初期選択: 東海道新幹線（登録済みの場合）
    const initialRid = featuredRids.find((rid) => edgeRouteIds.has(rid)) || (allEdges[0] ? allEdges[0].route_id : "");
    if (initialRid) {
      select.value = initialRid;
      loadTourRoute(initialRid);
    }
  } catch (err) {}
}

async function loadTourRoute(routeId) {
  try {
    const eData = await apiFetchEdges(routeId);
    const edges = eData.edges || [];
    if (!edges.length) {
      showToast("この路線の区間データはまだ登録されていません");
      return;
    }

    edges.sort((a, b) => (parseInt(a["区間順序"] || a["順序"]) || 0) - (parseInt(b["区間順序"] || b["順序"]) || 0));

    // 全区間のノードIDを収集
    const allNodeIds = [...new Set([edges[0]["from_node_id"], ...edges.map((e) => e["to_node_id"])].filter(Boolean))];

    // エッジ側の情報をキャッシュに先行登録
    edges.forEach((e) => {
      if (e["from_node_id"] && e["from_node_name"] && e["from_lat"] && e["from_lon"]) {
        nodeMasterCache.set(e["from_node_id"], {
          name: e["from_node_name"],
          lat: parseFloat(e["from_lat"]),
          lon: parseFloat(e["from_lon"])
        });
      }
      if (e["to_node_id"] && e["to_node_name"] && e["to_lat"] && e["to_lon"]) {
        nodeMasterCache.set(e["to_node_id"], {
          name: e["to_node_name"],
          lat: parseFloat(e["to_lat"]),
          lon: parseFloat(e["to_lon"])
        });
      }
    });

    // キャッシュに情報（名前・座標）がないノードIDがあれば、/api/nodes?ids= で一括補完（二重防御）
    const missingIds = allNodeIds.filter((nid) => {
      const c = nodeMasterCache.get(nid);
      return !c || !c.name || c.name === nid || isNaN(c.lat) || isNaN(c.lon);
    });

    if (missingIds.length > 0) {
      try {
        const nData = await apiFetchNodesByIds(missingIds);
        if (nData && nData.nodes) {
          nData.nodes.forEach((n) => {
            nodeMasterCache.set(n.node_id, {
              name: n["日本語名"] || n["名称"] || n["公用語名"] || n.node_id,
              lat: parseFloat(n["緯度"]),
              lon: parseFloat(n["経度"])
            });
          });
        }
      } catch (err) {
        console.warn("ノード一括取得スキップ:", err);
      }
    }

    const seq = [];
    let cumKm = 0.0;

    // 起点ステップ
    const firstE = edges[0];
    const fromResolved = resolveNodeInfo(
      firstE["from_node_id"],
      firstE["from_node_name"],
      firstE["from_lat"],
      firstE["from_lon"]
    );
    seq.push({
      node_id: firstE["from_node_id"],
      name: fromResolved.name,
      lat: fromResolved.lat,
      lon: fromResolved.lon,
      num: firstE["from_路線内番号"] || "1",
      km: 0.0,
      total_km: 0.0,
    });

    // 以降の各ステップ
    edges.forEach((e) => {
      const dist = parseFloat(e["距離_km"]) || 0.0;
      cumKm = Math.round((cumKm + dist) * 100) / 100;
      const toResolved = resolveNodeInfo(
        e["to_node_id"],
        e["to_node_name"],
        e["to_lat"],
        e["to_lon"]
      );
      seq.push({
        node_id: e["to_node_id"],
        name: toResolved.name,
        lat: toResolved.lat,
        lon: toResolved.lon,
        num: e["to_路線内番号"] || "",
        km: dist,
        total_km: cumKm,
      });
    });

    tourState.activeRouteId = routeId;
    tourState.sequence = seq;
    tourState.currentIndex = 0;

    // 起点座標から国を自動判定してタイルセレクタを優先並び替え
    if (seq[0] && seq[0].lat && seq[0].lon && typeof detectCountryFromCoord === "function") {
      const tourCountry = detectCountryFromCoord(seq[0].lat, seq[0].lon);
      if (tourCountry && tourCountry !== currentDetectedCountry) {
        updateAllTileSelectors(tourCountry);
      }
    }

    showToast(`ツアー路線をロードしました: ${edges.length} 区間 / ${cumKm.toFixed(1)} km`);
    tourUpdateView();
  } catch (err) {
    showToast("路線の読み込みに失敗しました: " + err.message);
  }
}

function tourPrev() {
  if (tourState.currentIndex > 0) {
    tourState.currentIndex--;
    tourUpdateView();
  }
}

function tourNext() {
  if (tourState.currentIndex < tourState.sequence.length - 1) {
    tourState.currentIndex++;
    tourUpdateView();
  }
}

async function tourUpdateView() {
  const seq = tourState.sequence;
  if (!seq.length) return;

  const idx = tourState.currentIndex;
  const currentStep = seq[idx];

  $("btn-tour-prev").disabled = idx === 0;
  $("btn-tour-next").disabled = idx === seq.length - 1;

  // 再度最新のキャッシュ・周辺情報で補完
  const resolved = resolveNodeInfo(
    currentStep.node_id,
    currentStep.name,
    currentStep.lat,
    currentStep.lon
  );

  // 万一それでも名前がIDのまま、あるいは座標が欠落していれば即時オンデマンド取得
  if ((resolved.name === currentStep.node_id || resolved.lat == null) && !currentStep._fetched) {
    currentStep._fetched = true;
    try {
      const singleData = await apiFetchNodesByIds([currentStep.node_id]);
      if (singleData && singleData.nodes && singleData.nodes[0]) {
        const n = singleData.nodes[0];
        resolved.name = n["日本語名"] || n["名称"] || n["公用語名"] || currentStep.node_id;
        resolved.lat = parseFloat(n["緯度"]);
        resolved.lon = parseFloat(n["経度"]);
        nodeMasterCache.set(currentStep.node_id, {
          name: resolved.name,
          lat: resolved.lat,
          lon: resolved.lon
        });
      }
    } catch (e) {}
  }

  currentStep.name = resolved.name;
  currentStep.lat = resolved.lat;
  currentStep.lon = resolved.lon;

  // 拠点名表示（太字）
  $("tour-current-info").innerHTML = `
    <span>${idx + 1}/${seq.length}: <b style="font-size:13px; color:#1e293b;">${esc(resolved.name)}</b></span>
    ${currentStep.num ? `<span style="font-size:11px; color:#2563eb;"> [${esc(currentStep.num)}]</span>` : ""}
  `;

  $("tour-meta").innerText = `累計 ${currentStep.total_km.toFixed(1)} km (区間: ${currentStep.km.toFixed(1)} km)`;

  const lat = resolved.lat;
  const lon = resolved.lon;

  if (lat !== null && lon !== null && !isNaN(lat) && !isNaN(lon)) {
    focusOn(lat, lon, 14);
    updateSvView(lat, lon);

    loadNodes({ lat, lng: lon });

    mapPanes.forEach((pane) => {
      pane.layers.tour.clearLayers();
      const marker = L.circleMarker([lat, lon], {
        radius: 9,
        fillColor: COLORS.tour,
        color: "#ffffff",
        weight: 3,
        fillOpacity: 1
      });
      pane.layers.tour.addLayer(marker);
    });
  }
}

// ---------------------------------------------------------------
// ストリートビュードロワー
// ---------------------------------------------------------------
function initSvDrawer() {
  const btnTourSv = $("btn-tour-sv");
  if (btnTourSv) {
    btnTourSv.addEventListener("click", () => {
      const seq = tourState.sequence;
      const idx = tourState.currentIndex;
      if (seq && seq[idx] && seq[idx].lat && seq[idx].lon) {
        const step = seq[idx];
        window.open(`https://www.google.com/maps/@?api=1&map_action=pano&viewpoint=${step.lat},${step.lon}`, "_blank");
      } else {
        const c = mapPanes[0].map.getCenter();
        window.open(`https://www.google.com/maps/@?api=1&map_action=pano&viewpoint=${c.lat},${c.lng}`, "_blank");
      }
    });
  }

  const btnClose = $("btn-close-sv");
  if (btnClose) {
    btnClose.addEventListener("click", () => {
      const drawer = $("sv-drawer");
      if (drawer) drawer.classList.remove("open");
    });
  }
}

function updateSvView(lat, lon) {
  const placeholder = $("sv-placeholder");
  const iframe = $("sv-iframe");
  if (!placeholder) return;

  placeholder.innerHTML = `
    <div style="text-align:center;">
      <div style="font-size:14px; font-weight:700; margin-bottom:8px; color:#fff;">📍 座標: ${lat.toFixed(5)}, ${lon.toFixed(5)}</div>
      <a href="https://www.google.com/maps/@?api=1&map_action=pano&viewpoint=${lat},${lon}" target="_blank" rel="noopener" class="btn-primary" style="display:inline-block; padding:8px 16px; text-decoration:none;">
        👀 Googleストリートビューを別窓で開く
      </a>
      <div style="font-size:11px; color:#94a3b8; margin-top:8px;">※ 外部セキュリティ規約に準拠し、公式ビューアーを安全に呼び出します。</div>
    </div>
  `;
  placeholder.style.display = "flex";
  if (iframe) iframe.style.display = "none";
}

// ---------------------------------------------------------------
// レイヤートグル
// ---------------------------------------------------------------
function initLayerToggles() {
  const bind = (id, layerName) => {
    const el = $(id);
    if (!el) return;
    el.addEventListener("change", (e) => {
      mapPanes.forEach((p) => {
        if (e.target.checked) p.layers[layerName].addTo(p.map);
        else p.map.removeLayer(p.layers[layerName]);
      });
    });
  };
  bind("toggle-layer-edges", "edges");
  bind("toggle-layer-nodes", "nodes");
  bind("toggle-layer-spots", "spots");
  bind("toggle-layer-mine", "mine");
  bind("toggle-layer-wiki", "wiki");
}

// ---------------------------------------------------------------
// 地図右クリック・コンテキストメニュー
// ---------------------------------------------------------------
let contextCoords = null;

function initContextMenu() {
  const menu = $("map-context-menu");
  if (!menu) return;

  mapPanes.forEach((pane) => {
    pane.map.on("contextmenu", (e) => {
      if (e.originalEvent) e.originalEvent.preventDefault();
      contextCoords = e.latlng;
      menu.style.left = `${e.originalEvent.pageX}px`;
      menu.style.top = `${e.originalEvent.pageY}px`;
      menu.style.display = "block";
    });
  });

  $("ctx-open-sv").addEventListener("click", () => {
    if (!contextCoords) return;
    window.open(`https://www.google.com/maps/@?api=1&map_action=pano&viewpoint=${contextCoords.lat},${contextCoords.lng}`, "_blank");
    menu.style.display = "none";
  });

  $("ctx-copy-coords").addEventListener("click", () => {
    if (!contextCoords) return;
    const coordStr = `${contextCoords.lat.toFixed(6)}, ${contextCoords.lng.toFixed(6)}`;
    navigator.clipboard.writeText(coordStr).then(() => {
      showToast(`📋 座標をコピーしました: ${coordStr}`);
    }).catch(() => {
      showToast(`座標: ${coordStr}`);
    });
    menu.style.display = "none";
  });

  $("ctx-add-point").addEventListener("click", () => {
    if (!contextCoords) return;
    openRecordPanel();
    draft.type = "point";
    draft.point = [contextCoords.lat, contextCoords.lng];
    $("log-coords").value = `${contextCoords.lat.toFixed(6)}, ${contextCoords.lng.toFixed(6)}`;
    draftChanged();
    renderOverlays();
    showToast(`📍 ポイントを配置しました: ${contextCoords.lat.toFixed(5)}, ${contextCoords.lng.toFixed(5)}`);
    menu.style.display = "none";
  });

  document.addEventListener("click", (e) => {
    if (!menu.contains(e.target)) menu.style.display = "none";
  });

  document.addEventListener("keydown", (e) => {
    if (e.key === "Escape") menu.style.display = "none";
  });
}
