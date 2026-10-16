/**
 * 地図タイルプロバイダ定義 (tiles.js)
 */

const TILE_PROVIDERS = {
  "osm-std": {
    name: "OpenStreetMap (標準)",
    url: "https://tile.openstreetmap.org/{z}/{x}/{y}.png",
    options: {
      maxZoom: 19,
      attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
    }
  },
  "gsi-std": {
    name: "地理院地図 (標準)",
    url: "https://cyberjapandata.gsi.go.jp/xyz/std/{z}/{x}/{y}.png",
    options: {
      maxZoom: 18,
      attribution: '&copy; <a href="https://maps.gsi.go.jp/development/ichiran.html">国土地理院</a>'
    }
  },
  "gsi-photo": {
    name: "地理院地図 (写真・オルソ)",
    url: "https://cyberjapandata.gsi.go.jp/xyz/ort/{z}/{x}/{y}.jpg",
    options: {
      maxZoom: 18,
      attribution: '&copy; <a href="https://maps.gsi.go.jp/development/ichiran.html">国土地理院</a>'
    }
  },
  "gsi-pale": {
    name: "地理院地図 (淡色地図)",
    url: "https://cyberjapandata.gsi.go.jp/xyz/pale/{z}/{x}/{y}.png",
    options: {
      maxZoom: 18,
      attribution: '&copy; <a href="https://maps.gsi.go.jp/development/ichiran.html">国土地理院</a>'
    }
  },
  "gsi-relief": {
    name: "地理院地図 (陰影起伏図)",
    url: "https://cyberjapandata.gsi.go.jp/xyz/relief/{z}/{x}/{y}.png",
    options: {
      maxZoom: 15,
      attribution: '&copy; <a href="https://maps.gsi.go.jp/development/ichiran.html">国土地理院</a>'
    }
  },
  "google-roads": {
    name: "Google Map (標準道路地図)",
    url: "https://mt1.google.com/vt/lyrs=m&x={x}&y={y}&z={z}",
    options: {
      maxZoom: 20,
      attribution: '&copy; Google'
    }
  },
  "google-hybrid": {
    name: "Google Map (航空写真・地名)",
    url: "https://mt1.google.com/vt/lyrs=y&x={x}&y={y}&z={z}",
    options: {
      maxZoom: 20,
      attribution: '&copy; Google'
    }
  },
  "carto-dark": {
    name: "CartoDB (Dark 夜間)",
    url: "https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png",
    options: {
      maxZoom: 19,
      subdomains: 'abcd',
      attribution: '&copy; <a href="https://carto.com/">CARTO</a>'
    }
  }
};

function createTileLayer(providerKey) {
  const p = TILE_PROVIDERS[providerKey] || TILE_PROVIDERS["gsi-std"];
  return L.tileLayer(p.url, p.options);
}
