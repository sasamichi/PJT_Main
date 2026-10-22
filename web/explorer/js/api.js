/**
 * 共通ヘルパー ＆ バックエンドREST API通信 (api.js)
 */

const $ = (id) => document.getElementById(id);

const esc = (s) => String(s ?? "").replace(/[&<>"']/g, (c) => (
  { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]
));

let toastTimer = null;
function showToast(message) {
  const toast = $("toast");
  toast.innerText = message;
  toast.classList.add("show");
  clearTimeout(toastTimer);
  toastTimer = setTimeout(() => toast.classList.remove("show"), 3000);
}

async function apiJson(path, options) {
  const res = await fetch(path, options);
  const data = await res.json().catch(() => ({}));
  if (!res.ok) throw new Error(data.error || `HTTP ${res.status}`);
  return data;
}

const jsonRequest = (method, body) => ({
  method,
  headers: { "Content-Type": "application/json" },
  body: JSON.stringify(body)
});

// --- マスタ ---
const apiFetchNodes = (lat, lon, radiusKm = 35) =>
  apiJson(`/api/nodes?lat=${lat}&lon=${lon}&radius_km=${radiusKm}`);
const apiFetchRoutes = (cc) => apiJson(`/api/routes?country_code=${cc}`);
const apiFetchEdges = (routeId = "") =>
  apiJson(routeId ? `/api/edges?route_id=${encodeURIComponent(routeId)}` : "/api/edges");
const apiFetchMunicipalities = (cc) => apiJson(`/api/municipalities?country_code=${cc}`);

// --- 探索ログ（ポイント／ルート） ---
const apiFetchLogs = () => apiJson("/api/logs");
const apiSaveLog = (log) => apiJson("/api/logs", jsonRequest("POST", log));
const apiUpdateLog = (logId, fields) => apiJson("/api/logs", jsonRequest("PUT", { log_id: logId, ...fields }));
const apiDeleteLog = (logId) => apiJson(`/api/logs?log_id=${encodeURIComponent(logId)}`, { method: "DELETE" });

// --- 外部サービス（サーバー経由） ---
const apiSearchLocation = (q) => apiJson(`/api/search?q=${encodeURIComponent(q)}`);
const apiFetchWikidata = (lat, lon, radiusKm = 15) =>
  apiJson(`/api/wikidata?lat=${lat}&lon=${lon}&radius_km=${radiusKm}`);
