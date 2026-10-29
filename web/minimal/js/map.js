// map.js: 最低限Webサイト 地図ビューロジック (階層に戻るナビゲーション対応)
(function() {
  'use strict';

  const data = window.MINIMAL_DATA || { nodes: [], stats: {} };

  let map = null;
  let markerLayerGroup = null;
  let activeMarkers = [];
  let currentTargetNodeId = null;

  // フィルター状態
  const filters = {
    airSea: true,       // 空港・港湾
    shinkansen: true,   // 新幹線・主要駅
    railways: true,     // 一般鉄道駅
    roads: true,        // IC・高速施設・道の駅
    weather: false      // 気象観測点 (初期オフ)
  };

  const shinkansenKeywords = ['新幹線', '東京', '品川', '新横浜', '小田原', '熱海', '三島', '新富士', '静岡', '掛川', '浜松', '豊橋', '三河安城', '名古屋', '岐阜羽島', '米原', '京都', '新大阪', '新神戸', '西明石', '姫路', '相生', '岡山', '新倉敷', '福山', '新尾道', '三原', '東広島', '広島', '新岩国', '徳山', '新山口', '厚狭', '新下関', '小倉', '博多', '上野', '大宮', '小山', '宇都宮', '那須塩原', '新白河', '郡山', '福島', '白石蔵王', '仙台', '古川', 'くりこま高原', '一ノ関', '水沢江刺', '北上', '新花巻', '盛岡', 'いわて沼宮内', '二戸', '八戸', '七戸十和田', '新青森', '奥津軽いまべつ', '木古内', '新函館北斗', '熊谷', '本庄早稲田', '高崎', '上毛高原', '越後湯沢', '浦佐', '長岡', '燕三条', '新潟', '安中榛名', '軽井沢', '佐久平', '上田', '長野', '飯山', '上越妙高', '糸魚川', '黒部宇奈月温泉', '富山', '新高岡', '金沢', '小松', '加賀温泉', '芦原温泉', '福井', '越前たけふ', '敦賀', '新鳥栖', '久留米', '筑後船小屋', '新大牟田', '新玉名', '熊本', '新八代', '新水俣', '出水', '川内', '鹿児島中央', '武雄温泉', '嬉野温泉', '新大村', '諫早', '長崎'];

  function getNodeColor(kind, name) {
    if (kind === '空港') return '#0284c7';
    if (kind.includes('港湾')) return '#0d9488';
    if (kind === '鉄道駅') {
      if (shinkansenKeywords.some(k => name.includes(k))) return '#dc2626';
      return '#2563eb';
    }
    if (kind.includes('IC') || kind.includes('高速') || kind === '道の駅') return '#d97706';
    if (kind.includes('気象')) return '#059669';
    return '#64748b';
  }

  function init() {
    const mapEl = document.getElementById('map');
    if (!mapEl) return;

    map = L.map('map', {
      center: [36.2048, 138.2529],
      zoom: 6,
      minZoom: 4,
      maxZoom: 18
    });
    window.leafletMap = map;

    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
      attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors',
      maxZoom: 19
    }).addTo(map);

    markerLayerGroup = L.layerGroup().addTo(map);

    setupFilters();
    map.on('zoomend', updateMarkers);

    handleUrlParams();
    updateMarkers();
  }

  function setupFilters() {
    const filterInputs = document.querySelectorAll('.filter-chip input[type="checkbox"]');
    filterInputs.forEach(input => {
      const type = input.dataset.filter;
      if (type && filters.hasOwnProperty(type)) {
        input.checked = filters[type];
        input.addEventListener('change', () => {
          filters[type] = input.checked;
          updateMarkers();
        });
      }
    });
  }

  function updateMarkers() {
    if (!map || !markerLayerGroup) return;
    markerLayerGroup.clearLayers();

    const zoom = map.getZoom();
    const bounds = map.getBounds();
    let count = 0;

    data.nodes.forEach(node => {
      if (!node.lat || !node.lng) return;

      const isAirSea = node.kind === '空港' || node.kind.includes('港湾');
      const isRail = node.kind === '鉄道駅';
      const isShinkansen = isRail && shinkansenKeywords.some(k => node.name.includes(k));
      const isRoad = node.kind.includes('IC') || node.kind.includes('高速') || node.kind === '道の駅';
      const isWeather = node.kind.includes('気象');

      if (isAirSea && !filters.airSea) return;
      if (isRoad && !filters.roads) return;
      if (isWeather && !filters.weather) return;
      if (isRail) {
        if (isShinkansen && !filters.shinkansen) return;
        if (!isShinkansen && !filters.railways) return;
      }

      if (zoom <= 7 && !isAirSea && !isShinkansen) return;
      if (zoom <= 10 && !isAirSea && !isShinkansen && !node.kind.includes('主要')) return;
      if (zoom >= 11 && !bounds.contains([node.lat, node.lng])) return;

      const color = getNodeColor(node.kind, node.name);
      const radius = isAirSea || isShinkansen ? 6 : 4;

      const marker = L.circleMarker([node.lat, node.lng], {
        radius: radius,
        fillColor: color,
        color: '#ffffff',
        weight: 1.5,
        opacity: 1,
        fillOpacity: 0.85
      });

      // ポップアップ内に「階層ビューに戻る」ボタンを明示
      const backBtnHtml = window.IS_EMBED 
        ? `<button class="popup-back-btn" onclick="window.returnToTreeFromMap('${node.id}');">📖 階層ツリーでこの場所を見る</button>`
        : `<a href="index.html?view=japan&nodeId=${node.id}" class="popup-back-btn" style="text-align:center;">📖 階層ツリーでこの場所を見る</a>`;

      const popupHtml = `
        <div class="popup-title">${node.name}</div>
        <div class="popup-row"><b>種別:</b> <span class="badge-kind" data-kind="${node.kind}">${node.kind}</span></div>
        <div class="popup-row"><b>所在地:</b> ${node.pref || ''} ${node.city || ''}</div>
        <div class="popup-row" style="margin-top:6px;">
          ${backBtnHtml}
        </div>
      `;
      marker.bindPopup(popupHtml);

      markerLayerGroup.addLayer(marker);
      count++;
    });

    const infoEl = document.getElementById('map-marker-count');
    if (infoEl) {
      infoEl.textContent = `表示中: ${count} 拠点 (ズーム: ${zoom})`;
    }
  }

  function handleUrlParams() {
    const params = new URLSearchParams(window.location.search);
    const lat = parseFloat(params.get('lat'));
    const lng = parseFloat(params.get('lng'));
    const name = params.get('name');
    const nodeId = params.get('nodeId');

    if (!isNaN(lat) && !isNaN(lng)) {
      map.setView([lat, lng], 14);
      setTimeout(() => {
        const targetNode = data.nodes.find(n => (nodeId && n.id === nodeId) || (Math.abs(n.lat - lat) < 0.001 && Math.abs(n.lng - lng) < 0.001));
        if (targetNode) {
          const color = getNodeColor(targetNode.kind, targetNode.name);
          const highlightMarker = L.circleMarker([lat, lng], {
            radius: 8,
            fillColor: color,
            color: '#dc2626',
            weight: 3,
            fillOpacity: 0.9
          }).addTo(map);

          const backBtnHtml = window.IS_EMBED 
            ? `<button class="popup-back-btn" onclick="window.returnToTreeFromMap('${targetNode.id}');">📖 階層ツリーでこの場所を見る</button>`
            : `<a href="index.html?view=japan&nodeId=${targetNode.id}" class="popup-back-btn" style="text-align:center;">📖 階層ツリーでこの場所を見る</a>`;

          const popupHtml = `
            <div class="popup-title">${targetNode.name}</div>
            <div class="popup-row"><b>種別:</b> <span class="badge-kind" data-kind="${targetNode.kind}">${targetNode.kind}</span></div>
            <div class="popup-row"><b>所在地:</b> ${targetNode.pref || ''} ${targetNode.city || ''}</div>
            <div class="popup-row" style="margin-top:6px;">
              ${backBtnHtml}
            </div>
          `;
          highlightMarker.bindPopup(popupHtml).openPopup();
        }
      }, 300);
    }
  }

  // 外部からのジャンプ用API (オールインワン埋め込み時用)
  window.jumpToMap = function(lat, lng, name, nodeId) {
    if (!map) return;
    currentTargetNodeId = nodeId;
    map.invalidateSize();
    map.setView([lat, lng], 14);
    setTimeout(() => {
      map.invalidateSize();
      const marker = L.circleMarker([lat, lng], {
        radius: 8,
        fillColor: '#dc2626',
        color: '#ffffff',
        weight: 2,
        fillOpacity: 0.9
      }).addTo(markerLayerGroup);

      const backBtnHtml = `<button class="popup-back-btn" onclick="window.returnToTreeFromMap('${nodeId || ''}');">📖 階層ツリーでこの場所を見る</button>`;

      marker.bindPopup(`
        <div class="popup-title">${name}</div>
        <div class="popup-row">座標: ${lat.toFixed(4)}, ${lng.toFixed(4)}</div>
        <div class="popup-row" style="margin-top:6px;">
          ${backBtnHtml}
        </div>
      `).openPopup();
    }, 200);
  };

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }

})();
