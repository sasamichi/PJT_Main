/**
 * 探索ログ記録パネル (records.js)
 * ポイント／ルートの登録・編集・削除、複数選択ピッカー、SNS下書き
 * ※ draft / renderOverlays / setTool / focusOn は app.js 側で定義
 */

const ID_RE = /[A-Z]{2}-[A-Z]+-\d+/g;

let appLogs = [];
let pickers = {};

// ---------------------------------------------------------------
// ルート座標の変換（"緯度,経度;緯度,経度;..." ⇔ [[lat,lon],...]）
// ---------------------------------------------------------------
function parseRoute(text) {
  return String(text || "").split(";")
    .map((p) => p.split(",").map(parseFloat))
    .filter((p) => p.length === 2 && p.every(Number.isFinite));
}

const formatRoute = (pts) => pts.map(([lat, lon]) => `${lat.toFixed(6)},${lon.toFixed(6)}`).join(";");

function routeLengthKm(pts) {
  let m = 0;
  for (let i = 1; i < pts.length; i++) m += L.latLng(pts[i - 1]).distanceTo(L.latLng(pts[i]));
  return m / 1000;
}

function parseCoords(text) {
  const m = String(text).match(/(-?\d+(?:\.\d+)?)\s*[,，\s]\s*(-?\d+(?:\.\d+)?)/);
  return m ? [parseFloat(m[1]), parseFloat(m[2])] : null;
}

// 描画方法（ポイント／ルート）は専用列を持たず、ルート座標の有無で判定する（記録種別は探索カテゴリ）
const isRouteLog = (log) => !!String(log["ルート座標"] || "").trim();

const logLocation = (log) => {
  if (isRouteLog(log)) return parseRoute(log["ルート座標"])[0] || null;
  const lat = parseFloat(log["緯度"]), lon = parseFloat(log["経度"]);
  return Number.isFinite(lat) && Number.isFinite(lon) ? [lat, lon] : null;
};

// ---------------------------------------------------------------
// 複数選択ピッカー（入力補完＋チップ表示）
// ---------------------------------------------------------------
function createPicker(name) {
  const input = $(`log-${name}`), list = $(`dl-${name}`), chips = $(`chips-${name}`);
  const labelToId = new Map(), idToLabel = new Map();
  let ids = [];

  const renderChips = () => {
    chips.innerHTML = ids.map((id) =>
      `<span class="chip">${esc(idToLabel.get(id) || id)}<button type="button" data-id="${esc(id)}" title="外す">×</button></span>`
    ).join("");
  };

  const tryAdd = () => {
    const text = input.value.trim();
    const id = labelToId.get(text) || (text.match(ID_RE) || [])[0];
    if (id && !ids.includes(id)) { ids.push(id); renderChips(); updateSnsDrafts(); }
    if (id) input.value = "";
  };

  input.addEventListener("input", () => { if (labelToId.has(input.value.trim())) tryAdd(); });
  input.addEventListener("change", tryAdd);
  chips.addEventListener("click", (e) => {
    const btn = e.target.closest("button[data-id]");
    if (btn) { ids = ids.filter((i) => i !== btn.dataset.id); renderChips(); updateSnsDrafts(); }
  });

  return {
    setOptions(items) {
      labelToId.clear();
      const frag = document.createDocumentFragment();
      items.forEach(({ id, label }) => {
        labelToId.set(label, id);
        idToLabel.set(id, label);
        const opt = document.createElement("option");
        opt.value = label;
        frag.appendChild(opt);
      });
      list.replaceChildren(frag);
      renderChips();
    },
    getIds: () => ids.slice(),
    setIds(newIds) { ids = newIds.slice(); renderChips(); },
    clear() { ids = []; input.value = ""; renderChips(); }
  };
}

// ---------------------------------------------------------------
// パネル初期化
// ---------------------------------------------------------------
function openRecordPanel() {
  $("record-panel").classList.add("open");
  $("btn-toggle-record").classList.add("active");
}

function showTab(targetId) {
  document.querySelectorAll(".panel-tab").forEach((t) => t.classList.toggle("active", t.dataset.target === targetId));
  document.querySelectorAll(".tab-content").forEach((c) => { c.hidden = c.id !== targetId; });
  if (targetId === "tab-logs") renderLogsList();
  if (targetId === "tab-sns") updateSnsDrafts();
}

function initRecordPanel() {
  pickers = { route: createPicker("route"), node: createPicker("node"), municipality: createPicker("municipality") };

  $("btn-toggle-record").addEventListener("click", () => {
    const open = $("record-panel").classList.toggle("open");
    $("btn-toggle-record").classList.toggle("active", open);
  });
  $("btn-close-record").addEventListener("click", () => {
    $("record-panel").classList.remove("open");
    $("btn-toggle-record").classList.remove("active");
  });
  document.querySelectorAll(".panel-tab").forEach((t) => t.addEventListener("click", () => showTab(t.dataset.target)));

  $("log-country").addEventListener("change", (e) => {
    const cc = e.target.value;
    focusOn(...COUNTRY_CENTERS[cc], 12);
    loadMasterOptions(cc);
    if (typeof updateAllTileSelectors === "function") {
      updateAllTileSelectors(cc);
    }
  });
  $("log-type").addEventListener("change", (e) => {
    setTool(e.target.value === "ルート" ? "route" : "point");
    onDraftChanged(); // 編集中などで切替が拒否された場合に表示を戻す
  });
  $("log-coords").addEventListener("change", (e) => {
    const p = parseCoords(e.target.value);
    if (p) setDraftPoint(...p); else onDraftChanged();
  });

  $("btn-route-undo").addEventListener("click", () => { draft.route.pop(); draftChanged(); });
  $("btn-route-clear").addEventListener("click", () => { draft.route = []; draftChanged(); });
  $("btn-cancel-edit").addEventListener("click", resetForm);
  $("exploration-form").addEventListener("submit", handleSubmit);
  $("logs-list-container").addEventListener("click", handleLogAction);

  // 保存先振り分けラジオの切り替えリスナー
  document.querySelectorAll('input[name="save-destination"]').forEach((r) => {
    r.addEventListener("change", (e) => {
      const isThemeSpot = e.target.value === "theme_spot";
      $("fields-theme-spot").style.display = isThemeSpot ? "block" : "none";
      $("field-log-category").style.display = isThemeSpot ? "none" : "block";
    });
  });

  ["log-title", "log-memo", "log-tags", "log-url"].forEach((id) => $(id).addEventListener("input", updateSnsDrafts));
  $("btn-copy-x").addEventListener("click", () => copyText("draft-x", "X用下書き"));
  $("btn-copy-note").addEventListener("click", () => copyText("draft-note", "note用下書き"));

  loadMasterOptions("JP");
  refreshLogs();
  onDraftChanged();
}

function copyText(id, label) {
  navigator.clipboard.writeText($(id).value);
  showToast(`${label}をコピーしました`);
}

async function loadMasterOptions(cc) {
  try {
    const [r, m] = await Promise.all([apiFetchRoutes(cc), apiFetchMunicipalities(cc)]);
    pickers.route.setOptions(r.routes.map((x) => ({ id: x.route_id, label: `${x["日本語名"] || x["公用語名"]} (${x.route_id})` })));
    pickers.municipality.setOptions(m.municipalities.map((x) => {
      const mid = x.municipality_id || x.municipality_id_tmp;
      return { id: mid, label: `${x["日本語名"] || x["公用語名"]} (${mid})` };
    }));
  } catch (err) {
    showToast("マスタの読み込みに失敗しました: " + err.message);
  }
}

// app.js から地図周辺の拠点が読み込まれるたびに呼ばれる
function refreshNodeOptions(nodes) {
  pickers.node.setOptions(nodes.map((n) => ({
    id: n.node_id, label: `${n["日本語名"] || n["公用語名"]}／${n["種別"]} (${n.node_id})`
  })));
}

async function refreshLogs() {
  try {
    appLogs = (await apiFetchLogs()).logs;
    renderLogsList();
    renderOverlays();
  } catch (err) {
    showToast("ログの読み込みに失敗しました: " + err.message);
  }
}

// ---------------------------------------------------------------
// 下書き（draft）の変化をフォームへ反映
// ---------------------------------------------------------------
function onDraftChanged() {
  const isRoute = draft.type === "route";
  const editing = draft.editingId;

  $("log-type").value = isRoute ? "ルート" : "ポイント";
  $("log-type").disabled = !!editing;
  $("field-point").hidden = isRoute;
  $("field-route").hidden = !isRoute;

  if (isRoute) {
    $("route-summary").innerText = `頂点 ${draft.route.length} / ${routeLengthKm(draft.route).toFixed(2)} km`;
  } else {
    $("log-coords").value = draft.point ? `${draft.point[0].toFixed(6)}, ${draft.point[1].toFixed(6)}` : "";
  }

  $("edit-banner").hidden = !editing;
  $("edit-banner-text").innerText = editing ? `✏️ 編集中: ${editing}` : "";
  $("btn-submit-log").innerText = editing ? "上書き更新" : "探索ログを保存";
  updateSnsDrafts();
}

function resetForm() {
  draft.editingId = null;
  draft.point = null;
  draft.route = [];
  ["log-title", "log-memo", "log-url"].forEach((id) => { $(id).value = ""; });
  Object.values(pickers).forEach((p) => p.clear());
  draftChanged();
  renderOverlays();
}

// ---------------------------------------------------------------
// 保存（新規／上書き）
// ---------------------------------------------------------------
async function handleSubmit(e) {
  e.preventDefault();
  const title = $("log-title").value.trim();
  if (!title) return showToast("タイトルを入力してください");

  const isRoute = draft.type === "route";
  let location;
  if (isRoute) {
    if (draft.route.length < 2) return showToast("ルートは2点以上クリックしてください");
    location = draft.route[0];
  } else {
    const typed = parseCoords($("log-coords").value);
    if (typed) draft.point = typed;
    if (!draft.point) return showToast("地図をクリックして座標を指定してください");
    location = draft.point;
  }

  const dest = document.querySelector('input[name="save-destination"]:checked')?.value || "log";
  const svStatus = $("log-sv-status").value; // 確認済 / 未確認 / SVなし

  // 1. 中世史跡への振り分け保存
  if (dest === "theme_spot") {
    const spotPayload = {
      country_code: $("log-country").value,
      日本語名: title,
      種別: $("spot-category").value,
      時代区分: $("spot-era").value,
      関連人物_出来事: $("spot-person").value.trim(),
      緯度: location[0].toFixed(6),
      経度: location[1].toFixed(6),
      近隣ノード_id: pickers.node.getIds()[0] || "",
      municipality_id: pickers.municipality.getIds().join(","),
      SV確認済: svStatus,
      備考_解説: $("log-memo").value.trim(),
      GoogleMap: `https://www.google.com/maps/@?api=1&map_action=pano&viewpoint=${location[0].toFixed(6)},${location[1].toFixed(6)}`,
      Wikipedia_ja: $("log-url").value.trim()
    };
    if (!spotPayload.municipality_id) return showToast("所在自治体を「対象自治体」から選択してください（必須）");
    try {
      const res = await apiSaveThemeSpot(spotPayload);
      showToast(`中世史跡として登録しました (${res.spot.spot_id})`);
      resetForm();
      if (window.refreshThemeSpots) await window.refreshThemeSpots();
    } catch (err) {
      showToast("史跡の保存に失敗しました: " + err.message);
    }
    return;
  }

  // 2. 通常の探索ログ保存
  const tags = $("log-tags").value.trim();
  const memo = $("log-memo").value.trim();
  if (!memo) return showToast("本文（探索メモ）を入力してください（必須）");
  const geoguessr = { "確認済": "確認済", "未確認": "未確認", "SVなし": "対象外" }[svStatus];

  const payload = {
    country_code: $("log-country").value,
    記録種別: $("log-category").value,
    タイトル: title,
    対象路線_ids: pickers.route.getIds().join(","),
    対象ノード_ids: pickers.node.getIds().join(","),
    対象自治体_ids: pickers.municipality.getIds().join(","),
    緯度: location[0].toFixed(6),
    経度: location[1].toFixed(6),
    ルート座標: isRoute ? formatRoute(draft.route) : "",
    タグ: tags,
    本文: memo,
    Webリンク: $("log-url").value.trim(),
    Geoguessr候補: geoguessr
  };

  try {
    const res = draft.editingId ? await apiUpdateLog(draft.editingId, payload) : await apiSaveLog(payload);
    showToast(`${draft.editingId ? "更新" : "保存"}しました (${res.log.log_id})`);
    resetForm();
    await refreshLogs();
  } catch (err) {
    showToast("保存に失敗しました: " + err.message);
  }
}

// ---------------------------------------------------------------
// 編集・削除・位置修正・地図表示
// ---------------------------------------------------------------
function editLog(logId) {
  const log = appLogs.find((l) => l.log_id === logId);
  if (!log) return;
  const isRoute = isRouteLog(log);
  const splitIds = (s) => String(s || "").match(ID_RE) || [];

  draft.editingId = null;
  setTool(isRoute ? "route" : "point");
  draft.point = isRoute ? null : logLocation(log);
  draft.route = isRoute ? parseRoute(log["ルート座標"]) : [];
  draft.editingId = logId;

  // log_id は国コードを含まないため、関連IDの先頭（例: JP-RT-…）から対象国を推定する
  const cc = ((String(log["対象路線_ids"] || "") + "," + String(log["対象ノード_ids"] || "") + "," + String(log["対象自治体_ids"] || "")).match(ID_RE) || [""])[0].split("-")[0];
  if (cc !== $("log-country").value && [...$("log-country").options].some((o) => o.value === cc)) {
    $("log-country").value = cc;
    loadMasterOptions(cc);
  }
  $("log-title").value = log["タイトル"];
  $("log-tags").value = log["タグ"];
  $("log-memo").value = log["本文"];
  $("log-url").value = log["Webリンク"];
  pickers.route.setIds(splitIds(log["対象路線_ids"]));
  pickers.node.setIds(splitIds(log["対象ノード_ids"]));
  $("log-category").value = log["記録種別"] || "鉄道探索";
  $("log-sv-status").value = { "確認済": "確認済", "未確認": "未確認", "対象外": "SVなし" }[log["Geoguessr候補"]] || "未確認";
  pickers.municipality.setIds(splitIds(log["対象自治体_ids"]));

  showTab("tab-input");
  openRecordPanel();
  draftChanged();
  const loc = logLocation(log);
  if (loc) focusOn(loc[0], loc[1], 14);
}

async function deleteLog(logId) {
  if (!confirm(`ログ ${logId} を削除しますか？\nこの操作は元に戻せません。`)) return;
  try {
    await apiDeleteLog(logId);
    if (draft.editingId === logId) resetForm();
    showToast(`${logId} を削除しました`);
    await refreshLogs();
  } catch (err) {
    showToast("削除に失敗しました: " + err.message);
  }
}

// 保存済みポイントをドラッグして位置修正
async function moveLog(logId, lat, lon) {
  try {
    await apiUpdateLog(logId, { 緯度: lat.toFixed(6), 経度: lon.toFixed(6) });
    showToast(`${logId} の位置を更新しました`);
  } catch (err) {
    showToast("位置の更新に失敗しました: " + err.message);
  }
  await refreshLogs();
}

// 一覧・地図ポップアップ内のボタン共通処理
function handleLogAction(e) {
  const btn = e.target.closest("button[data-act]");
  if (!btn) return;
  const id = btn.dataset.id;
  if (btn.dataset.act === "edit") editLog(id);
  else if (btn.dataset.act === "delete") deleteLog(id);
  else if (btn.dataset.act === "focus") {
    const loc = logLocation(appLogs.find((l) => l.log_id === id) || {});
    if (loc) focusOn(loc[0], loc[1], 15);
  }
}

const logActionButtons = (id, withFocus = true) =>
  (withFocus ? `<button data-act="focus" data-id="${esc(id)}">📍 地図で見る</button>` : "") +
  `<button data-act="edit" data-id="${esc(id)}">✏️ 編集</button>` +
  `<button data-act="delete" data-id="${esc(id)}" class="danger">🗑️ 削除</button>`;

function logPopupHtml(log) {
  const memo = log["本文"] ? esc(log["本文"].slice(0, 80)) + (log["本文"].length > 80 ? "…" : "") : "";
  return `<div class="log-popup"><strong>${esc(log["タイトル"])}</strong>` +
    `<div class="sub">${esc(log.log_id)} / ${esc(log["記録種別"])} / ${esc(log["探索日"])}</div>` +
    `${memo ? `<div>${memo}</div>` : ""}` +
    `<div class="actions">${logActionButtons(log.log_id, false)}</div></div>`;
}

function renderLogsList() {
  const box = $("logs-list-container");
  if (!appLogs.length) {
    box.innerHTML = '<p class="hint">探索ログはまだありません。</p>';
    return;
  }
  box.innerHTML = appLogs.slice().reverse().map((l) => {
    const isRoute = isRouteLog(l);
    const memo = l["本文"] ? esc(l["本文"].slice(0, 60)) + (l["本文"].length > 60 ? "…" : "") : "";
    return `<div class="log-card">
      <div class="log-card-head"><strong>${esc(l.log_id)}</strong><span>${isRoute ? "〰️ ルート" : "📍 ポイント"} / ${esc(l["探索日"])}</span></div>
      <div class="log-card-title">${esc(l["タイトル"])}</div>
      <div class="hint">${memo}</div>
      <div class="actions">${logActionButtons(l.log_id)}</div>
    </div>`;
  }).join("");
}

// ---------------------------------------------------------------
// SNS / note 下書き
// ---------------------------------------------------------------
function updateSnsDrafts() {
  const title = $("log-title").value.trim() || "探索ログ";
  const memo = $("log-memo").value.trim();
  const tags = $("log-tags").value.trim();
  const url = $("log-url").value.trim();
  const tagList = tags.split(",").map((t) => t.trim()).filter(Boolean).map((t) => `#${t}`).join(" ");
  const where = draft.type === "route"
    ? `ルート（頂点${draft.route.length}・約${routeLengthKm(draft.route).toFixed(2)}km）`
    : (draft.point ? `${draft.point[0].toFixed(6)}, ${draft.point[1].toFixed(6)}` : "");

  $("draft-x").value = `【机上探索: ${title}】\n${memo.length > 80 ? memo.slice(0, 80) + "..." : memo}\n${tagList}`;
  $("draft-note").value = `# ${title}\n\n## 探索概要\n- 位置: ${where}\n- タグ: ${tags}\n\n## 沿線記録と考察\n${memo}\n\n---\n*参考: ${url}*`;
}
