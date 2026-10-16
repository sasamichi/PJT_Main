/**
 * バックエンドREST API通信モジュール (api.js)
 */

const API_BASE = "";

async function apiFetchNodes(countryCode = "JP", lat = null, lon = null, radiusKm = 35) {
  let url = `${API_BASE}/api/nodes?country_code=${countryCode}`;
  if (lat !== null && lon !== null) {
    url += `&lat=${lat}&lon=${lon}&radius_km=${radiusKm}`;
  }
  const res = await fetch(url);
  if (!res.ok) throw new Error("Failed to fetch nodes");
  return await res.json();
}

async function apiFetchRoutes(countryCode = "JP") {
  const res = await fetch(`${API_BASE}/api/routes?country_code=${countryCode}`);
  if (!res.ok) throw new Error("Failed to fetch routes");
  return await res.json();
}

async function apiFetchMunicipalities(countryCode = "JP") {
  const res = await fetch(`${API_BASE}/api/municipalities?country_code=${countryCode}`);
  if (!res.ok) throw new Error("Failed to fetch municipalities");
  return await res.json();
}

async function apiFetchRouteNodes(routeId = "") {
  const res = await fetch(`${API_BASE}/api/route_nodes?route_id=${routeId}`);
  if (!res.ok) throw new Error("Failed to fetch route nodes");
  return await res.json();
}

async function apiFetchLogs() {
  const res = await fetch(`${API_BASE}/api/logs`);
  if (!res.ok) throw new Error("Failed to fetch logs");
  return await res.json();
}

async function apiSaveLog(logData) {
  const res = await fetch(`${API_BASE}/api/logs`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json"
    },
    body: JSON.stringify(logData)
  });
  if (!res.ok) throw new Error("Failed to save log");
  return await res.json();
}

async function apiSearchLocation(query) {
  if (!query) return [];
  const res = await fetch(`${API_BASE}/api/search?q=${encodeURIComponent(query)}`);
  if (!res.ok) return [];
  return await res.json();
}

async function apiFetchWikidata(lat, lon, radiusKm = 10) {
  const res = await fetch(`${API_BASE}/api/wikidata?lat=${lat}&lon=${lon}&radius_km=${radiusKm}`);
  if (!res.ok) return { items: [] };
  return await res.json();
}
