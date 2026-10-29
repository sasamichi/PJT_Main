/**
 * 地図タイルプロバイダ定義 (tiles.js)
 * 日本・オーストリア・スイス・台湾等の公的背景地図および世界衛星写真を網羅
 * 地図中心座標や選択国に応じた自動判定・動的ソートに対応
 */

// 各国の緯度経度バウンディングボックス (minLat, maxLat, minLon, maxLon)
const COUNTRY_BBOXES = {
  JP: { code: "JP", name: "日本",         bbox: [20.0, 46.0, 122.0, 154.0] },
  AT: { code: "AT", name: "オーストリア",   bbox: [46.3, 49.1, 9.5, 17.2] },
  CH: { code: "CH", name: "スイス",         bbox: [45.8, 47.9, 5.9, 10.5] },
  TW: { code: "TW", name: "台湾",           bbox: [21.8, 25.4, 119.9, 122.1] }
};

function detectCountryFromCoord(lat, lon) {
  if (lat == null || lon == null || isNaN(lat) || isNaN(lon)) return null;
  for (const [code, c] of Object.entries(COUNTRY_BBOXES)) {
    const [minLat, maxLat, minLon, maxLon] = c.bbox;
    if (lat >= minLat && lat <= maxLat && lon >= minLon && lon <= maxLon) {
      return code;
    }
  }
  return null;
}

const TILE_GROUPS = [
  {
    countryCode: "JP",
    group: "🗾 日本 (国土地理院)",
    tiles: ["gsi-std", "gsi-photo", "gsi-pale", "gsi-relief"]
  },
  {
    countryCode: "AT",
    group: "🇦🇹 オーストリア (basemap.at)",
    tiles: ["at-basemap-std", "at-basemap-grau", "at-basemap-ortho"]
  },
  {
    countryCode: "CH",
    group: "🇨🇭 スイス (swisstopo)",
    tiles: ["ch-swisstopo-color", "ch-swisstopo-grey", "ch-swisstopo-image"]
  },
  {
    countryCode: "TW",
    group: "🇹🇼 台湾 (NLSC 国土測絵中心)",
    tiles: ["tw-nlsc-emap", "tw-nlsc-photo", "tw-nlsc-emap8"]
  },
  {
    countryCode: "Global",
    group: "🌐 世界標準・衛星写真 (Global)",
    tiles: ["osm-std", "esri-sat", "google-roads", "google-hybrid", "carto-dark"]
  }
];

function getSortedTileGroups(activeCountryCode) {
  if (!activeCountryCode || activeCountryCode === "Global") {
    return TILE_GROUPS.slice().sort((a, b) => {
      if (a.countryCode === "JP") return -1;
      if (b.countryCode === "JP") return 1;
      if (a.countryCode === "Global") return -1;
      if (b.countryCode === "Global") return 1;
      return 0;
    });
  }

  // 1. 最上位: 現在地の公的タイル
  // 2. 第2位: 🌐 世界標準・衛星写真 (Global)
  // 3. 第3位以降: その他の公的タイル
  return TILE_GROUPS.slice().sort((a, b) => {
    if (a.countryCode === activeCountryCode) return -1;
    if (b.countryCode === activeCountryCode) return 1;
    if (a.countryCode === "Global") return -1;
    if (b.countryCode === "Global") return 1;
    return a.group.localeCompare(b.group);
  });
}

const TILE_PROVIDERS = {
  // --- 日本（国土地理院） ---
  "gsi-std": {
    name: "地理院地図 (標準)",
    category: "JP",
    url: "https://cyberjapandata.gsi.go.jp/xyz/std/{z}/{x}/{y}.png",
    options: {
      maxZoom: 18,
      attribution: '&copy; <a href="https://maps.gsi.go.jp/development/ichiran.html" target="_blank">国土地理院</a>'
    }
  },
  "gsi-photo": {
    name: "地理院地図 (写真・オルソ)",
    category: "JP",
    url: "https://cyberjapandata.gsi.go.jp/xyz/ort/{z}/{x}/{y}.jpg",
    options: {
      maxZoom: 18,
      attribution: '&copy; <a href="https://maps.gsi.go.jp/development/ichiran.html" target="_blank">国土地理院</a>'
    }
  },
  "gsi-pale": {
    name: "地理院地図 (淡色地図)",
    category: "JP",
    url: "https://cyberjapandata.gsi.go.jp/xyz/pale/{z}/{x}/{y}.png",
    options: {
      maxZoom: 18,
      attribution: '&copy; <a href="https://maps.gsi.go.jp/development/ichiran.html" target="_blank">国土地理院</a>'
    }
  },
  "gsi-relief": {
    name: "地理院地図 (陰影起伏図)",
    category: "JP",
    url: "https://cyberjapandata.gsi.go.jp/xyz/relief/{z}/{x}/{y}.png",
    options: {
      maxZoom: 15,
      attribution: '&copy; <a href="https://maps.gsi.go.jp/development/ichiran.html" target="_blank">国土地理院</a>'
    }
  },

  // --- オーストリア（basemap.at: 連邦州・BEV公式） ---
  "at-basemap-std": {
    name: "🇦🇹 basemap.at (標準地図)",
    category: "AT",
    url: "https://maps.wien.gv.at/basemap/geolandbasemap/normal/google3857/{z}/{y}/{x}.png",
    options: {
      maxZoom: 19,
      attribution: 'Datenquelle: <a href="https://basemap.at" target="_blank">basemap.at</a>'
    }
  },
  "at-basemap-grau": {
    name: "🇦🇹 basemap.at (グレースケール)",
    category: "AT",
    url: "https://maps.wien.gv.at/basemap/bmapgrau/normal/google3857/{z}/{y}/{x}.png",
    options: {
      maxZoom: 19,
      attribution: 'Datenquelle: <a href="https://basemap.at" target="_blank">basemap.at</a>'
    }
  },
  "at-basemap-ortho": {
    name: "🇦🇹 basemap.at (オルソ高精細航空写真)",
    category: "AT",
    url: "https://maps.wien.gv.at/basemap/bmaporthofoto30cm/normal/google3857/{z}/{y}/{x}.jpeg",
    options: {
      maxZoom: 19,
      attribution: 'Datenquelle: <a href="https://basemap.at" target="_blank">basemap.at</a>'
    }
  },

  // --- スイス（swisstopo: 連邦測量局公式） ---
  "ch-swisstopo-color": {
    name: "🇨🇭 swisstopo (公式国土地図カラー)",
    category: "CH",
    url: "https://wmts.geo.admin.ch/1.0.0/ch.swisstopo.pixelkarte-farbe/default/current/3857/{z}/{x}/{y}.jpeg",
    options: {
      maxZoom: 19,
      attribution: '&copy; <a href="https://www.swisstopo.admin.ch" target="_blank">swisstopo</a>'
    }
  },
  "ch-swisstopo-grey": {
    name: "🇨🇭 swisstopo (公式国土地図グレー)",
    category: "CH",
    url: "https://wmts.geo.admin.ch/1.0.0/ch.swisstopo.pixelkarte-grau/default/current/3857/{z}/{x}/{y}.jpeg",
    options: {
      maxZoom: 19,
      attribution: '&copy; <a href="https://www.swisstopo.admin.ch" target="_blank">swisstopo</a>'
    }
  },
  "ch-swisstopo-image": {
    name: "🇨🇭 swisstopo (SWISSIMAGE オルソ航空写真)",
    category: "CH",
    url: "https://wmts.geo.admin.ch/1.0.0/ch.swisstopo.swissimage/default/current/3857/{z}/{x}/{y}.jpeg",
    options: {
      maxZoom: 19,
      attribution: '&copy; <a href="https://www.swisstopo.admin.ch" target="_blank">swisstopo</a>'
    }
  },

  // --- 台湾（NLSC: 内政部国土測絵中心公式） ---
  "tw-nlsc-emap": {
    name: "🇹🇼 NLSC 台湾通用電子地図 (標準)",
    category: "TW",
    url: "https://wmts.nlsc.gov.tw/wmts/EMAP/default/GoogleMapsCompatible/{z}/{y}/{x}",
    options: {
      maxZoom: 19,
      attribution: '&copy; <a href="https://maps.nlsc.gov.tw" target="_blank">國土測繪中心 NLSC</a>'
    }
  },
  "tw-nlsc-photo": {
    name: "🇹🇼 NLSC 正射影像図 (高解像度航空写真)",
    category: "TW",
    url: "https://wmts.nlsc.gov.tw/wmts/PHOTO2/default/GoogleMapsCompatible/{z}/{y}/{x}",
    options: {
      maxZoom: 19,
      attribution: '&copy; <a href="https://maps.nlsc.gov.tw" target="_blank">國土測繪中心 NLSC</a>'
    }
  },
  "tw-nlsc-emap8": {
    name: "🇹🇼 NLSC 台湾通用電子地図 (英語併記)",
    category: "TW",
    url: "https://wmts.nlsc.gov.tw/wmts/EMAP8/default/GoogleMapsCompatible/{z}/{y}/{x}",
    options: {
      maxZoom: 19,
      attribution: '&copy; <a href="https://maps.nlsc.gov.tw" target="_blank">國土測繪中心 NLSC</a>'
    }
  },

  // --- グローバル / 世界標準 ---
  "osm-std": {
    name: "OpenStreetMap (標準)",
    category: "Global",
    url: "https://tile.openstreetmap.org/{z}/{x}/{y}.png",
    options: {
      maxZoom: 19,
      attribution: '&copy; <a href="https://www.openstreetmap.org/copyright" target="_blank">OpenStreetMap</a> contributors'
    }
  },
  "esri-sat": {
    name: "🛰️ Esri World Imagery (世界衛星写真)",
    category: "Global",
    url: "https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}",
    options: {
      maxZoom: 18,
      attribution: '&copy; <a href="https://www.esri.com" target="_blank">Esri</a>, Maxar, Earthstar Geographics'
    }
  },
  "google-roads": {
    name: "Google Map (標準道路地図)",
    category: "Global",
    url: "https://mt1.google.com/vt/lyrs=m&x={x}&y={y}&z={z}",
    options: {
      maxZoom: 20,
      attribution: '&copy; Google'
    }
  },
  "google-hybrid": {
    name: "Google Map (航空写真・地名)",
    category: "Global",
    url: "https://mt1.google.com/vt/lyrs=y&x={x}&y={y}&z={z}",
    options: {
      maxZoom: 20,
      attribution: '&copy; Google'
    }
  },
  "carto-dark": {
    name: "CartoDB (Dark 夜間)",
    category: "Global",
    url: "https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png",
    options: {
      maxZoom: 19,
      subdomains: 'abcd',
      attribution: '&copy; <a href="https://carto.com/" target="_blank">CARTO</a>'
    }
  }
};

function createTileLayer(providerKey) {
  const p = TILE_PROVIDERS[providerKey] || TILE_PROVIDERS["gsi-std"];
  return L.tileLayer(p.url, p.options);
}
