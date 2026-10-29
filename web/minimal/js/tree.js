// tree.js: 最低限Webサイト 階層ツリー・検索ロジック (テーブル表示 ＆ 多層ツリー完全対応)
(function() {
  'use strict';

  const data = window.MINIMAL_DATA || { countries: [], regions: [], nodes: [], stats: {} };

  // DOM要素
  const viewWorldArea = document.getElementById('view-world-area');
  const viewJapanArea = document.getElementById('view-japan-area');
  const worldCountryGrid = document.getElementById('world-country-grid');
  const worldSearchInput = document.getElementById('world-search-input');
  const worldSearchClearBtn = document.getElementById('world-search-clear-btn');
  const worldCountBadge = document.getElementById('world-count-badge');
  const bcWorld = document.getElementById('bc-world');
  const bcSep = document.getElementById('bc-sep');
  const bcCountry = document.getElementById('bc-country');
  const searchInput = document.getElementById('search-input');
  const searchClearBtn = document.getElementById('search-clear-btn');
  const treeContainer = document.getElementById('tree-container');
  const resultStats = document.getElementById('result-stats');
  const japanTreeTitle = document.getElementById('japan-tree-title');

  // 配列正規化ヘルパー (PowerShell単一要素オブジェクト化対策)
  function toArray(val) {
    if (!val) return [];
    if (Array.isArray(val)) return val;
    if (typeof val === 'object') return [val];
    return [];
  }

  // 国旗絵文字変換
  function getFlagEmoji(code) {
    if (!code || code.length !== 2) return '🌐';
    const offset = 127397;
    return String.fromCodePoint(...[...code.toUpperCase()].map(c => c.charCodeAt(0) + offset));
  }

  // 初期化 (Top画面は世界の国一覧テーブル)
  function init() {
    renderWorldCountries();
    setupEvents();
    showWorldView();

    // URLパラメータで view=japan または nodeId 指定がある場合は日本ツリーを開く
    const params = new URLSearchParams(window.location.search);
    const targetNodeId = params.get('nodeId');
    if (params.get('view') === 'japan' || targetNodeId) {
      window.showJapanView();
      if (targetNodeId) {
        setTimeout(() => window.highlightNodeInTree(targetNodeId), 150);
      }
    }
  }

  // 世界全カ国ビュー (Top画面) の表示
  window.showWorldView = function() {
    if (viewWorldArea) viewWorldArea.style.display = 'block';
    if (viewJapanArea) viewJapanArea.style.display = 'none';

    if (bcWorld) bcWorld.className = 'bc-item active';
    if (bcSep) bcSep.style.display = 'none';
    if (bcCountry) bcCountry.style.display = 'none';

    if (worldSearchInput) {
      worldSearchInput.value = '';
      if (worldSearchClearBtn) worldSearchClearBtn.style.display = 'none';
      renderWorldCountries();
    }
  };

  // 日本詳細ビュー (多層ツリー) の表示
  window.showJapanView = function() {
    if (viewWorldArea) viewWorldArea.style.display = 'none';
    if (viewJapanArea) viewJapanArea.style.display = 'block';

    if (bcWorld) bcWorld.className = 'bc-item';
    if (bcSep) bcSep.style.display = 'inline';
    if (bcCountry) {
      bcCountry.style.display = 'inline';
      bcCountry.className = 'bc-item active';
    }

    renderMultiLevelTree();
  };

  // 世界の国一覧（テーブル表示）
  function renderWorldCountries(filterQuery = '') {
    if (!worldCountryGrid) return;
    worldCountryGrid.innerHTML = '';
    const q = filterQuery.trim().toLowerCase();

    const countries = toArray(data.countries);
    const filtered = countries.filter(c => {
      if (!q) return true;
      return (c.name && c.name.toLowerCase().includes(q)) || 
             (c.code && c.code.toLowerCase().includes(q)) || 
             (c.en && c.en.toLowerCase().includes(q));
    });

    if (worldCountBadge) {
      worldCountBadge.textContent = `${filtered.length} カ国`;
    }

    // 日本を最上部に固定し、残りは五十音順
    filtered.sort((a, b) => {
      if (a.code === 'JP') return -1;
      if (b.code === 'JP') return 1;
      return (a.name || '').localeCompare(b.name || '', 'ja');
    });

    if (filtered.length === 0) {
      worldCountryGrid.innerHTML = '<div style="padding:16px; text-align:center; color:var(--text-muted);">該当する国が見つかりませんでした。</div>';
      return;
    }

    const wrapper = document.createElement('div');
    wrapper.className = 'table-wrapper';

    const table = document.createElement('table');
    table.className = 'data-table';
    table.innerHTML = `
      <thead>
        <tr>
          <th>国・地域名</th>
          <th class="hide-mobile">公用語表記</th>
          <th style="width:55px;">コード</th>
          <th style="width:55px;">通行</th>
          <th style="width:70px; text-align:center;">階層</th>
        </tr>
      </thead>
      <tbody></tbody>
    `;

    const tbody = table.querySelector('tbody');

    filtered.forEach(c => {
      const isJapan = c.code === 'JP';
      const flag = getFlagEmoji(c.code);
      const tr = document.createElement('tr');
      tr.className = `clickable-row ${isJapan ? 'japan-row' : ''}`;

      tr.innerHTML = `
        <td>
          <span style="font-size:16px; margin-right:4px; vertical-align:middle;">${flag}</span>
          <span style="font-weight:${isJapan ? '700' : '600'}; color:${isJapan ? 'var(--primary)' : 'inherit'};">${c.name}</span>
          ${isJapan ? '<span class="badge-kind" data-kind="鉄道" style="margin-left:6px;">収録済</span>' : ''}
        </td>
        <td class="hide-mobile" style="color:var(--text-sub); font-size:12px;">${c.en || '-'}</td>
        <td style="font-family:monospace; color:var(--text-sub);">${c.code}</td>
        <td style="color:var(--text-sub); font-size:12px;">${c.side || '-'}</td>
        <td style="text-align:center;">
          <span class="map-link-btn" style="${isJapan ? 'background:var(--primary); color:#fff;' : 'color:var(--text-muted); border-color:var(--border); background:#f8fafc;'}">
            ${isJapan ? '開く ›' : '準備中'}
          </span>
        </td>
      `;

      tr.addEventListener('click', () => {
        if (isJapan) {
          window.showJapanView();
        } else {
          alert(`【${c.name} (${c.code})】\n現在、詳細データ（自治体ツリー・交通拠点）は日本先行で公開中です。順次追加予定です。`);
        }
      });

      tbody.appendChild(tr);
    });

    wrapper.appendChild(table);
    worldCountryGrid.appendChild(wrapper);
  }

  // 日本の多層ツリー構造 (第1階層:地方 ➔ 第2階層:都道府県 ➔ 第3階層:政令市/一般市区町村 ➔ 第4階層:区 ➔ 拠点テーブル)
  function renderMultiLevelTree() {
    if (!treeContainer) return;
    treeContainer.innerHTML = '';

    const regions = toArray(data.regions);
    if (resultStats) {
      resultStats.textContent = `全8地方 / 47都道府県 / 約1.4万拠点`;
    }

    if (regions.length === 0) {
      treeContainer.innerHTML = '<div style="padding:16px; text-align:center;">ツリーデータがありません。</div>';
      return;
    }

    // 一括開閉コントロールバー
    const ctrlBar = document.createElement('div');
    ctrlBar.style.cssText = 'display:flex; gap:6px; margin-bottom:8px;';
    ctrlBar.innerHTML = `
      <button type="button" class="nav-tab-btn" id="btn-expand-regions" style="font-size:11px; padding:3px 8px;">▼ 全地方（47都道府県）を展開</button>
      <button type="button" class="nav-tab-btn" id="btn-collapse-regions" style="font-size:11px; padding:3px 8px;">▶ 全地方を折りたたむ</button>
    `;
    treeContainer.appendChild(ctrlBar);

    const regionBranches = [];

    regions.forEach((region, rIdx) => {
      const prefs = toArray(region.prefectures);
      const regWrap = document.createElement('div');
      regWrap.dataset.regionName = region.name;

      // 第1階層: 地方行
      const regRow = document.createElement('div');
      regRow.className = 'tree-row tree-row-l1';
      regRow.innerHTML = `
        <div class="tree-label">
          <span class="tree-arrow open">▶</span>
          <span>📁 <b>${region.name}</b></span>
        </div>
        <span class="tree-count">${prefs.length} 都道県</span>
      `;

      // 第2階層コンテナ (初期状態で全地方を開いて47都道府県を見えるようにする)
      const regBranch = document.createElement('div');
      regBranch.className = 'tree-branch';
      regBranch.style.display = 'block';

      regRow.addEventListener('click', () => {
        const isOpen = regBranch.style.display !== 'none';
        regBranch.style.display = isOpen ? 'none' : 'block';
        regRow.querySelector('.tree-arrow').classList.toggle('open', !isOpen);
      });

      regionBranches.push({ row: regRow, branch: regBranch });

      // 都道府県の構築
      prefs.forEach(pref => {
        const dCities = toArray(pref.designatedCities);
        const cities = toArray(pref.cities);
        const totalMuniCount = dCities.length + cities.length;

        const prefWrap = document.createElement('div');
        prefWrap.dataset.prefId = pref.id;

        const prefRow = document.createElement('div');
        prefRow.className = 'tree-row tree-row-l2';
        prefRow.innerHTML = `
          <div class="tree-label">
            <span class="tree-arrow">▶</span>
            <span>🏛️ <b>${pref.name}</b></span>
          </div>
          <span class="tree-count">${totalMuniCount} 自治体</span>
        `;

        const prefBranch = document.createElement('div');
        prefBranch.className = 'tree-branch';
        prefBranch.style.display = 'none';
        let prefBuilt = false;

        const openPref = () => {
          if (!prefBuilt) {
            buildPrefectureChildren(pref, prefBranch);
            prefBuilt = true;
          }
          prefBranch.style.display = 'block';
          prefRow.querySelector('.tree-arrow').classList.add('open');
        };

        prefRow.addEventListener('click', () => {
          const isOpen = prefBranch.style.display !== 'none';
          if (isOpen) {
            prefBranch.style.display = 'none';
            prefRow.querySelector('.tree-arrow').classList.remove('open');
          } else {
            openPref();
          }
        });

        prefWrap._openPref = openPref;
        prefWrap.appendChild(prefRow);
        prefWrap.appendChild(prefBranch);
        regBranch.appendChild(prefWrap);
      });

      regWrap.appendChild(regRow);
      regWrap.appendChild(regBranch);
      treeContainer.appendChild(regWrap);
    });

    // 全地方の展開・折りたたみイベント
    ctrlBar.querySelector('#btn-expand-regions').addEventListener('click', () => {
      regionBranches.forEach(item => {
        item.branch.style.display = 'block';
        item.row.querySelector('.tree-arrow').classList.add('open');
      });
    });
    ctrlBar.querySelector('#btn-collapse-regions').addEventListener('click', () => {
      regionBranches.forEach(item => {
        item.branch.style.display = 'none';
        item.row.querySelector('.tree-arrow').classList.remove('open');
      });
    });
  }

  // 都道府県配下（第3階層：政令指定都市 ＆ 一般市区町村）の遅延構築
  function buildPrefectureChildren(pref, prefBranch) {
    const dCities = toArray(pref.designatedCities);
    const cities = toArray(pref.cities);

    // 1. 政令指定都市 (展開すると行政区リスト)
    dCities.forEach(dCity => {
      const wards = toArray(dCity.wards);
      const dWrap = document.createElement('div');
      dWrap.dataset.dCityId = dCity.id;

      const dRow = document.createElement('div');
      dRow.className = 'tree-row tree-row-l3-desig';
      dRow.innerHTML = `
        <div class="tree-label">
          <span class="tree-arrow">▶</span>
          <span>🏙️ <b>${dCity.name}</b> <small style="font-weight:normal;">(政令指定都市)</small></span>
        </div>
        <span class="tree-count">${wards.length} 区</span>
      `;

      const dBranch = document.createElement('div');
      dBranch.className = 'tree-branch';
      dBranch.style.display = 'none';
      let wardsBuilt = false;

      const openDCity = () => {
        if (!wardsBuilt) {
          wards.forEach(ward => {
            const wardEl = createMunicipalityElement(ward, `${dCity.name} ${ward.name}`);
            dBranch.appendChild(wardEl);
          });
          wardsBuilt = true;
        }
        dBranch.style.display = 'block';
        dRow.querySelector('.tree-arrow').classList.add('open');
      };

      dRow.addEventListener('click', () => {
        const isOpen = dBranch.style.display !== 'none';
        if (isOpen) {
          dBranch.style.display = 'none';
          dRow.querySelector('.tree-arrow').classList.remove('open');
        } else {
          openDCity();
        }
      });

      dWrap._openDCity = openDCity;
      dWrap.appendChild(dRow);
      dWrap.appendChild(dBranch);
      prefBranch.appendChild(dWrap);
    });

    // 2. 一般市区町村・特別区
    cities.forEach(city => {
      const cityEl = createMunicipalityElement(city, city.name);
      prefBranch.appendChild(cityEl);
    });
  }

  // 市区町村・行政区要素 ＆ 配下の拠点テーブル作成
  function createMunicipalityElement(unit, fullUnitName) {
    const nodes = toArray(unit.nodes);
    const unitWrap = document.createElement('div');
    unitWrap.dataset.unitId = unit.id;

    const uRow = document.createElement('div');
    uRow.className = 'tree-row tree-row-l3';
    uRow.innerHTML = `
      <div class="tree-label">
        <span class="tree-arrow">▶</span>
        <span>📍 <b>${unit.name}</b></span>
      </div>
      <span class="tree-count">${nodes.length} 拠点</span>
    `;

    const tableBox = document.createElement('div');
    tableBox.className = 'tree-table-box';
    tableBox.style.display = 'none';
    let tableBuilt = false;

    const openUnit = () => {
      if (!tableBuilt) {
        tableBox.appendChild(buildNodesTable(nodes, fullUnitName, false));
        tableBuilt = true;
      }
      tableBox.style.display = 'block';
      uRow.querySelector('.tree-arrow').classList.add('open');
    };

    uRow.addEventListener('click', () => {
      const isOpen = tableBox.style.display !== 'none';
      if (isOpen) {
        tableBox.style.display = 'none';
        uRow.querySelector('.tree-arrow').classList.remove('open');
      } else {
        openUnit();
      }
    });

    unitWrap._openUnit = openUnit;
    unitWrap.appendChild(uRow);
    unitWrap.appendChild(tableBox);
    return unitWrap;
  }

  // 拠点一覧のHTMLテーブル生成 (カード式を廃止しスマホで見やすいテーブル形式に統一)
  function buildNodesTable(nodes, defaultLocationName, showLocationColumn) {
    if (!nodes || nodes.length === 0) {
      const emptyDiv = document.createElement('div');
      emptyDiv.style.cssText = 'padding:8px 12px; color:var(--text-muted); font-size:12px;';
      emptyDiv.textContent = '登録されている交通拠点はありません。';
      return emptyDiv;
    }

    const wrapper = document.createElement('div');
    wrapper.className = 'table-wrapper';

    const table = document.createElement('table');
    table.className = 'data-table';

    if (showLocationColumn) {
      table.innerHTML = `
        <thead>
          <tr>
            <th style="width:75px;">種別</th>
            <th>拠点名称</th>
            <th>所在地</th>
            <th style="width:65px; text-align:center;">地図</th>
          </tr>
        </thead>
        <tbody></tbody>
      `;
    } else {
      table.innerHTML = `
        <thead>
          <tr>
            <th style="width:75px;">種別</th>
            <th>拠点名称</th>
            <th style="width:65px; text-align:center;">地図</th>
          </tr>
        </thead>
        <tbody></tbody>
      `;
    }

    const tbody = table.querySelector('tbody');

    nodes.forEach(node => {
      const tr = document.createElement('tr');
      tr.id = `node-row-${node.id}`;

      let mapBtn = '-';
      if (node.lat && node.lng) {
        const safeName = (node.name || '').replace(/'/g, "\\'");
        const clickHandler = `onclick="window.handleNodeMapJump('${node.id}', ${node.lat}, ${node.lng}, '${safeName}'); return false;"`;
        const targetUrl = window.IS_EMBED ? `#map` : `map.html?lat=${node.lat}&lng=${node.lng}&name=${encodeURIComponent(node.name)}&nodeId=${node.id}`;
        mapBtn = `<a href="${targetUrl}" ${clickHandler} class="map-link-btn" title="地図で場所を表示">🗺️ 地図</a>`;
      }

      if (showLocationColumn) {
        tr.innerHTML = `
          <td><span class="badge-kind" data-kind="${node.kind || ''}">${node.kind || '拠点'}</span></td>
          <td style="font-weight:600;">${node.name || ''}</td>
          <td style="color:var(--text-sub); font-size:12px;">${node.pref || ''} ${node.city || defaultLocationName || ''}</td>
          <td style="text-align:center;">${mapBtn}</td>
        `;
      } else {
        tr.innerHTML = `
          <td><span class="badge-kind" data-kind="${node.kind || ''}">${node.kind || '拠点'}</span></td>
          <td style="font-weight:600;">${node.name || ''}</td>
          <td style="text-align:center;">${mapBtn}</td>
        `;
      }

      tbody.appendChild(tr);
    });

    wrapper.appendChild(table);
    return wrapper;
  }

  // 階層から地図へのジャンプ処理
  window.handleNodeMapJump = function(nodeId, lat, lng, name) {
    if (typeof window.jumpToMap === 'function') {
      window.jumpToMap(lat, lng, name, nodeId);
    } else {
      window.location.href = `map.html?lat=${lat}&lng=${lng}&name=${encodeURIComponent(name)}&nodeId=${nodeId}`;
    }
  };

  // 地図から「階層ツリーでこの場所を見る」で戻ってきた際、該当ツリー階層を自動展開して行をハイライト
  window.highlightNodeInTree = function(nodeId) {
    if (!nodeId) return;
    window.showJapanView();

    // 該当ノードが属する 地方 -> 都道府県 -> (政令市) -> 市区町村 を探索して展開
    const regions = toArray(data.regions);
    for (const reg of regions) {
      for (const pref of toArray(reg.prefectures)) {
        // 政令市の区を検索
        for (const dCity of toArray(pref.designatedCities)) {
          for (const ward of toArray(dCity.wards)) {
            if (toArray(ward.nodes).some(n => n.id === nodeId)) {
              expandPathAndScroll(pref.id, dCity.id, ward.id, nodeId);
              return;
            }
          }
        }
        // 一般市区町村を検索
        for (const city of toArray(pref.cities)) {
          if (toArray(city.nodes).some(n => n.id === nodeId)) {
            expandPathAndScroll(pref.id, null, city.id, nodeId);
            return;
          }
        }
      }
    }
  };

  function expandPathAndScroll(prefId, dCityId, unitId, nodeId) {
    if (!treeContainer) return;
    const prefWrap = treeContainer.querySelector(`[data-pref-id="${prefId}"]`);
    if (prefWrap && prefWrap._openPref) {
      // 親の地方も開く
      const regBranch = prefWrap.parentElement;
      if (regBranch) regBranch.style.display = 'block';
      prefWrap._openPref();

      if (dCityId) {
        const dWrap = prefWrap.querySelector(`[data-d-city-id="${dCityId}"]`);
        if (dWrap && dWrap._openDCity) dWrap._openDCity();
      }

      const unitWrap = prefWrap.querySelector(`[data-unit-id="${unitId}"]`);
      if (unitWrap && unitWrap._openUnit) unitWrap._openUnit();
    }

    setTimeout(() => {
      const rowEl = document.getElementById(`node-row-${nodeId}`);
      if (rowEl) {
        rowEl.scrollIntoView({ behavior: 'smooth', block: 'center' });
        rowEl.classList.add('highlight');
        setTimeout(() => rowEl.classList.remove('highlight'), 3000);
      }
    }, 100);
  }

  // 全国ノード横断検索 (テーブル表示)
  function renderGlobalSearch(query) {
    if (!treeContainer) return;
    treeContainer.innerHTML = '';
    const q = query.trim().toLowerCase();

    if (japanTreeTitle) {
      japanTreeTitle.textContent = `🔍「${query}」の検索結果 (全国テーブル)`;
    }

    const allNodes = toArray(data.nodes);
    const matchedNodes = allNodes.filter(n => {
      return (n.name && n.name.toLowerCase().includes(q)) || 
             (n.city && n.city.toLowerCase().includes(q)) || 
             (n.pref && n.pref.toLowerCase().includes(q)) ||
             (n.kind && n.kind.toLowerCase().includes(q));
    });

    if (resultStats) {
      resultStats.textContent = `全国 ${matchedNodes.length} 件ヒット (上位 150 件表示)`;
    }

    if (matchedNodes.length === 0) {
      treeContainer.innerHTML = '<div style="padding:20px; text-align:center; color:var(--text-muted);">一致する駅名・拠点・自治体は見つかりませんでした。</div>';
      return;
    }

    const tableEl = buildNodesTable(matchedNodes.slice(0, 150), '', true);
    treeContainer.appendChild(tableEl);
  }

  // イベント設定
  function setupEvents() {
    if (worldSearchInput) {
      worldSearchInput.addEventListener('input', (e) => {
        const val = e.target.value;
        if (worldSearchClearBtn) worldSearchClearBtn.style.display = val ? 'block' : 'none';
        renderWorldCountries(val);
      });
      if (worldSearchClearBtn) {
        worldSearchClearBtn.addEventListener('click', () => {
          worldSearchInput.value = '';
          worldSearchClearBtn.style.display = 'none';
          renderWorldCountries();
          worldSearchInput.focus();
        });
      }
    }

    if (searchInput) {
      searchInput.addEventListener('input', (e) => {
        const val = e.target.value.trim();
        if (searchClearBtn) searchClearBtn.style.display = val ? 'block' : 'none';

        if (!val) {
          if (japanTreeTitle) japanTreeTitle.textContent = '🏛️ 日本の行政・交通 多層ツリー (地方 ➔ 都道府県 ➔ 市区町村 ➔ 拠点)';
          renderMultiLevelTree();
          return;
        }

        renderGlobalSearch(val);
      });

      if (searchClearBtn) {
        searchClearBtn.addEventListener('click', () => {
          searchInput.value = '';
          searchClearBtn.style.display = 'none';
          if (japanTreeTitle) japanTreeTitle.textContent = '🏛️ 日本の行政・交通 多層ツリー (地方 ➔ 都道府県 ➔ 市区町村 ➔ 拠点)';
          renderMultiLevelTree();
          searchInput.focus();
        });
      }
    }
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }

})();
