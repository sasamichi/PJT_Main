/**
 * 机上探索 Web GIS メインアプリケーション (app.js)
 * 地図ペイン（1/2/4画面）・連動同期・ツール・登録拠点／追加データ／Wikidataの重畳表示
 */

// --- 定数 ---
const COLORS = { node: "#2563eb", mine: "#f97316", route: "#ef4444", wiki: "#a855f7" };
const COUNTRY_CENTERS = { JP: [41.7737, 140.7264], AT: [48.2082, 16.3738] };
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
// draft: 入力中の記録（ポイントまたはルート）。editingId があれば既存ログの編集中
const draft = { type: "point", point: null, route: [], editingId: null };

let mapPanes = [];
let currentTool = "view";
let isSyncing = false;
let nearNodes = [];
let wikiItems = [];
let lastNodeCenter = null;
let lastWikiCenter = null;
let nodeSeq = 0;
let wikiSeq = 0;
let viewTimer = null;

document.addEventListener("DOMContentLoaded", () => {
  initTheme();
  initMapPanes();
  initSplitControls();
  initToolbar();
  initLayerToggles();
  initRecordPanel();
});

// ---------------------------------------------------------------
// テーマ（黒・白）。?theme=dark|light でデータ管理画面から引き継ぎ可能
// ---------------------------------------------------------------
function applyTheme(theme) {
  const dark = theme === "dark";
  document.body.classList.toggle("dark-mode", dark);
  localStorage.setItem("explorer_theme", theme);
  $("btn-toggle-theme").innerText = dark ? "☀️ 白背景" : "🌙 黒背景";
  $("link-admin").href = `http://localhost:8501/?theme=${theme}`;
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
    // 拠点が多い都市部でも軽快に動くよう、円マーカーはCanvas描画
    const map = L.map(`map-${n}`, { center: COUNTRY_CENTERS.JP, zoom: DEFAULT_ZOOM, zoomControl: false, preferCanvas: true });
    L.control.zoom({ position: "bottomright" }).addTo(map);

    const pane = {
      index: idx, el, map, currentTile: tileKey, visible: true,
      tileLayer: createTileLayer(tileKey).addTo(map),
      layers: { nodes: L.layerGroup().addTo(map), mine: L.layerGroup().addTo(map),
                wiki: L.layerGroup().addTo(map), draft: L.layerGroup().addTo(map) }
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

  // 連動同期（描画フレームごとに間引き）
  map.on("move", () => {
    if (isSyncing) return;
    cancelAnimationFrame(frame);
    frame = requestAnimationFrame(() => syncAll(map.getCenter(), map.getZoom(), pane.index));
  });

  // 移動が落ち着いたら、距離に応じて拠点・Wikidataを再取得
  map.on("moveend", () => {
    clearTimeout(viewTimer);
    viewTimer = setTimeout(() => {
      const c = map.getCenter();
      if (!lastNodeCenter || c.distanceTo(lastNodeCenter) > NODE_RELOAD_M) { lastNodeCenter = c; loadNodes(c); }
      if (!lastWikiCenter || c.distanceTo(lastWikiCenter) > WIKI_RELOAD_M) { lastWikiCenter = c; loadWiki(c); }
    }, 400);
  });

  map.on("click", (e) => handleMapClick(e.latlng));
  map.on("dblclick", () => { if (currentTool === "route") finishRoute(); });

  // ポップアップ内のボタン（編集・削除）はLeafletがクリック伝播を止めるため、開いた要素へ直接登録
  map.on("popupopen", (e) => e.popup.getElement().addEventListener("click", handleLogAction));
}

function setupPaneControls(pane) {
  const n = pane.index + 1;

  const select = $(`select-tile-${n}`);
  Object.entries(TILE_PROVIDERS).forEach(([key, p]) => {
    select.add(new Option(p.name, key, false, key === pane.currentTile));
  });
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

  // 表示サイズ確定後に再計算し、位置を揃えてから描画し直す
  setTimeout(() => {
    const ref = mapPanes[0].map;
    mapPanes.forEach((p) => { if (p.visible) p.map.invalidateSize(); });
    syncAll(ref.getCenter(), ref.getZoom(), 0);
    renderAll();
  }, 100);
}

// ---------------------------------------------------------------
// ツール（閲覧／ポイント／ルート／座標）
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
  // 既存ログの編集中は、そのログの種別と違う描画ツールへは切り替えない
  if (draft.editingId && (tool === "point" || tool === "route") && tool !== draft.type) {
    showToast("編集中は記録種別を変更できません");
    return;
  }
  currentTool = tool;
  document.querySelectorAll(".tool-btn[data-tool]").forEach((b) => b.classList.toggle("active", b.dataset.tool === tool));
  $("map-grid").dataset.tool = tool;
  // ルート確定のダブルクリックでズームしないようにする
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

// ダブルクリック＝2回目のクリックで余分に増えた頂点を除いて確定
function finishRoute() {
  draft.route.pop();
  setTool("view");
  draftChanged();
}

// ドラッグ終了イベント内で自分自身を描画し直さないよう、次のイベントループで反映
function draftChanged() {
  setTimeout(() => { renderOverlays(); onDraftChanged(); }, 0);
}

// ---------------------------------------------------------------
// 描画：追加データ（オレンジ点・赤線）／入力中データ
// ---------------------------------------------------------------
const pinIcon = (isDraft) => L.divIcon({
  className: "", html: `<div class="pin-dot${isDraft ? " draft" : ""}"></div>`, iconSize: [18, 18], iconAnchor: [9, 9]
});
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
// 描画：登録拠点（青）／Wikidata（紫）
// ---------------------------------------------------------------
function drawNodes() {
  mapPanes.forEach((p) => {
    p.layers.nodes.clearLayers();
    if (!p.visible) return;
    nearNodes.forEach((nd) => {
      const lat = parseFloat(nd["緯度"]), lon = parseFloat(nd["経度"]);
      if (!Number.isFinite(lat) || !Number.isFinite(lon)) return;
      const name = nd["日本語名"] || nd["公用語名"];
      L.circleMarker([lat, lon], { radius: 5, color: "#1d4ed8", fillColor: COLORS.node, fillOpacity: 0.85, weight: 1.5 })
        .bindPopup(`<strong>${esc(name)}</strong><br>種別: ${esc(nd["種別"])}<br>ID: ${esc(nd.node_id)}`)
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

function renderAll() {
  drawNodes();
  drawWiki();
  renderOverlays();
}

async function loadNodes(center) {
  const seq = ++nodeSeq;
  try {
    const data = await apiFetchNodes(center.lat, center.lng, 35);
    if (seq !== nodeSeq) return; // より新しい要求が走っていれば破棄
    nearNodes = data.nodes;
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
    wikiItems = data.items;
    drawWiki();
    $("badge-wiki").innerText = `Wikidata ${wikiItems.length}`;
  } catch (err) {
    if (seq !== wikiSeq) return;
    $("badge-wiki").innerText = "Wikidata 取得失敗";
    showToast("Wikidataの取得に失敗しました（地図移動で再試行されます）: " + err.message);
    lastWikiCenter = null; // 次の移動で必ず再取得する
  }
}

// ---------------------------------------------------------------
// レイヤー表示切替
// ---------------------------------------------------------------
function initLayerToggles() {
  const bind = (checkboxId, layerName, onEnable) => {
    $(checkboxId).addEventListener("change", (e) => {
      mapPanes.forEach((p) => {
        if (e.target.checked) p.layers[layerName].addTo(p.map); else p.map.removeLayer(p.layers[layerName]);
      });
      if (e.target.checked && onEnable) onEnable();
    });
  };
  bind("toggle-layer-nodes", "nodes");
  bind("toggle-layer-mine", "mine");
  bind("toggle-layer-wiki", "wiki", () => loadWiki(mapPanes[0].map.getCenter()));
}
