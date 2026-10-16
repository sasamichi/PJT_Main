/**
 * 世界交通網・地域データ基盤 公開Webサイト
 * メインアプリケーション制御スクリプト
 * - 全251カ国のクイック検索・選択
 * - 地図ビュー vs 階層ディレクトリビュー（地図なし）の切替
 * - ナレッジパネル（詳細情報表示枠）の実装
 */

const App = {
  summaryData: null,
  activeCountryCode: "JP",
  countryDataCache: {},
  currentCountryData: null,
  activeTab: "routes",
  searchQuery: "",
  viewMode: "map", // 'map' | 'tree'
  treeState: {
    level: "country", // 'world' | 'country' | 'genre' | 'detail'
    countryCode: "JP",
    genre: null,      // 'routes' | 'muni' | 'nodes'
    item: null,
    itemType: null,
  },

  init: async function () {
    window.App = this; // map.js からの参照用

    // テーマ初期化
    this.initTheme();

    // 地図の初期化
    PublicMap.init("map");

    // イベントリスナーの設定
    this.setupEventListeners();

    // サマリーデータの読み込み
    await this.loadSummary();

    // 初期の国（日本 JP）の読み込み
    await this.selectCountry("JP");
  },

  // テーマ切替
  initTheme: function () {
    const savedTheme = localStorage.getItem("gtta_theme") || "light";
    if (savedTheme === "dark") {
      document.body.classList.add("dark-theme");
      document.getElementById("theme-toggle-btn").innerText = "☀️ 白背景";
    } else {
      document.body.classList.remove("dark-theme");
      document.getElementById("theme-toggle-btn").innerText = "🌙 黒背景";
    }
  },

  toggleTheme: function () {
    const isDark = document.body.classList.toggle("dark-theme");
    localStorage.setItem("gtta_theme", isDark ? "dark" : "light");
    document.getElementById("theme-toggle-btn").innerText = isDark ? "☀️ 白背景" : "🌙 黒背景";
  },

  // イベントリスナー設定
  setupEventListeners: function () {
    // テーマ切替
    document.getElementById("theme-toggle-btn").addEventListener("click", () => this.toggleTheme());

    // 表示モード切替 (地図ビュー vs 階層ビュー)
    document.getElementById("btn-mode-map").addEventListener("click", () => this.switchViewMode("map"));
    document.getElementById("btn-mode-tree").addEventListener("click", () => this.switchViewMode("tree"));

    // 検索入力
    const searchInput = document.getElementById("search-input");
    const clearBtn = document.getElementById("search-clear-btn");

    searchInput.addEventListener("input", (e) => {
      this.searchQuery = e.target.value.trim().toLowerCase();
      clearBtn.style.display = this.searchQuery ? "block" : "none";
      if (this.viewMode === "map") {
        this.renderCurrentTab();
      } else {
        this.renderTreeCurrent();
      }
    });

    clearBtn.addEventListener("click", () => {
      searchInput.value = "";
      this.searchQuery = "";
      clearBtn.style.display = "none";
      if (this.viewMode === "map") {
        this.renderCurrentTab();
      } else {
        this.renderTreeCurrent();
      }
    });

    // タブ切替
    document.querySelectorAll(".tab-btn").forEach((btn) => {
      btn.addEventListener("click", () => {
        const tabKey = btn.getAttribute("data-tab");
        this.switchTab(tabKey);
      });
    });

    // 全251カ国クイックセレクト
    const countrySelect = document.getElementById("country-quick-select");
    countrySelect.addEventListener("change", (e) => {
      const cc = e.target.value;
      if (cc) {
        this.selectCountry(cc);
      }
    });

    // 地図リセットボタン
    document.getElementById("map-reset-btn").addEventListener("click", () => {
      PublicMap.resetView();
    });

    // ナレッジパネル（ドロワー）閉じるボタン
    document.getElementById("kp-close-btn").addEventListener("click", () => {
      this.closeKnowledgeDrawer();
    });

    // パンくずリストクリック
    document.getElementById("tree-breadcrumb").addEventListener("click", (e) => {
      const item = e.target.closest(".breadcrumb-item");
      if (!item) return;
      const level = item.getAttribute("data-level");
      if (level === "world") {
        this.navTreeWorld();
      } else if (level === "country") {
        this.navTreeCountry(this.treeState.countryCode);
      } else if (level === "genre") {
        this.navTreeGenre(this.treeState.countryCode, this.treeState.genre);
      }
    });
  },

  // 表示モード切替
  switchViewMode: function (mode) {
    this.viewMode = mode;
    document.getElementById("btn-mode-map").classList.toggle("active", mode === "map");
    document.getElementById("btn-mode-tree").classList.toggle("active", mode === "tree");

    if (mode === "tree") {
      document.body.classList.add("tree-mode-active");
      document.getElementById("map-mode-header").style.display = "none";
      document.getElementById("tree-mode-header").style.display = "block";
      this.closeKnowledgeDrawer();
      this.navTreeCountry(this.activeCountryCode);
    } else {
      document.body.classList.remove("tree-mode-active");
      document.getElementById("map-mode-header").style.display = "block";
      document.getElementById("tree-mode-header").style.display = "none";
      this.renderCurrentTab();
      PublicMap.map.invalidateSize();
    }
  },

  // サマリーデータ取得
  loadSummary: async function () {
    try {
      const res = await fetch("data/summary.json");
      if (!res.ok) throw new Error("summary.json の読み込みに失敗しました");
      this.summaryData = await res.json();
      this.renderHeaderStats();
      this.populateCountryDropdown();
      this.renderCountryPills();
    } catch (err) {
      console.error(err);
      document.getElementById("stats-pill").innerText = "データ読み込みエラー";
    }
  },

  // ヘッダー統計描画
  renderHeaderStats: function () {
    if (!this.summaryData || !this.summaryData.total_stats) return;
    const s = this.summaryData.total_stats;
    const pill = document.getElementById("stats-pill");
    pill.innerText = `登録国: ${s.registered_countries} | 路線: ${s.routes.toLocaleString()} | 拠点: ${s.nodes.toLocaleString()}`;
    document.getElementById("tab-count-countries").innerText = s.registered_countries;
  },

  // 全251カ国セレクトボックスの構築
  populateCountryDropdown: function () {
    const select = document.getElementById("country-quick-select");
    const countries = this.summaryData.countries || [];

    // 地域別にグループ化
    const regions = {};
    countries.forEach((c) => {
      const r = c.region || "その他";
      if (!regions[r]) regions[r] = [];
      regions[r].push(c);
    });

    select.innerHTML = '<option value="">🔍 全251カ国から選ぶ...</option>';

    // 地域順に optgroup を追加
    Object.keys(regions).sort().forEach((regionName) => {
      const group = document.createElement("optgroup");
      group.label = `── ${regionName} ──`;
      
      regions[regionName].sort((a, b) => a.name.localeCompare(b.name, "ja")).forEach((c) => {
        const opt = document.createElement("option");
        opt.value = c.code;
        const countTxt = c.counts.routes > 0 ? ` (${c.counts.routes}路線)` : (c.counts.municipalities > 0 ? ` (${c.counts.municipalities}地域)` : "");
        opt.innerText = `${c.flag} ${c.name} [${c.code}]${countTxt}`;
        group.appendChild(opt);
      });

      select.appendChild(group);
    });
  },

  // 主要国ピル群の描画
  renderCountryPills: function () {
    const container = document.getElementById("country-selector-container");
    container.innerHTML = "";

    const countries = [...(this.summaryData.countries || [])];
    
    // データ件数が多い順でソート（主要国）
    countries.sort((a, b) => {
      if (a.code === "JP") return -1;
      if (b.code === "JP") return 1;
      if (a.code === "AT") return -1;
      if (b.code === "AT") return 1;
      return (b.counts.routes + b.counts.nodes + b.counts.municipalities) - (a.counts.routes + a.counts.nodes + a.counts.municipalities);
    });

    const topCountries = countries.slice(0, 10);

    topCountries.forEach((c) => {
      const pill = document.createElement("div");
      pill.className = `country-pill ${c.code === this.activeCountryCode ? "active" : ""}`;
      pill.setAttribute("data-cc", c.code);
      
      const countLabel = c.counts.routes > 0 ? `${c.counts.routes}路線` : `${c.counts.municipalities}地域`;
      pill.innerHTML = `
        <span>${c.flag} ${c.name}</span>
        <span class="pill-count">${countLabel}</span>
      `;

      pill.addEventListener("click", () => {
        this.selectCountry(c.code);
      });

      container.appendChild(pill);
    });
  },

  // 国の選択
  selectCountry: async function (countryCode) {
    this.activeCountryCode = countryCode;
    this.treeState.countryCode = countryCode;

    // ドロップダウンとピルの選択状態を同期
    const select = document.getElementById("country-quick-select");
    if (select) select.value = countryCode;

    document.querySelectorAll(".country-pill").forEach((pill) => {
      pill.classList.toggle("active", pill.getAttribute("data-cc") === countryCode);
    });

    // 読み込み中表示
    const contentEl = document.getElementById("tab-content");
    contentEl.innerHTML = `
      <div class="loading-box">
        <div class="spinner"></div>
        <div>${countryCode} のデータを読み込み中...</div>
      </div>
    `;

    // キャッシュまたは新規取得
    if (this.countryDataCache[countryCode]) {
      this.currentCountryData = this.countryDataCache[countryCode];
    } else {
      try {
        const res = await fetch(`data/${countryCode.toLowerCase()}.json`);
        if (!res.ok) throw new Error(`${countryCode}.json が見つかりません`);
        this.currentCountryData = await res.json();
        this.countryDataCache[countryCode] = this.currentCountryData;
      } catch (err) {
        // データがまだない国の場合のフォールバック
        const cMeta = this.summaryData.countries.find((c) => c.code === countryCode) || {};
        this.currentCountryData = {
          country_code: countryCode,
          name: cMeta.name || countryCode,
          region: cMeta.region || "",
          flag: cMeta.flag || "🌐",
          map_meta: cMeta.map_meta || { center: [0, 0], zoom: 3 },
          info: { official_lang: cMeta.official_lang, currency: cMeta.currency, drive_side: cMeta.drive_side },
          counts: { municipalities: 0, operators: 0, routes: 0, nodes: 0, sequenced_routes: 0 },
          municipalities: [],
          operators: [],
          routes: [],
          nodes: [],
          route_nodes: {},
        };
      }
    }

    // 地図の視点移動
    PublicMap.setCountryView(this.currentCountryData.map_meta);

    // タブ件数バッジ更新
    this.updateTabCounts();

    // 画面再描画
    if (this.viewMode === "map") {
      this.renderCurrentTab();
    } else {
      this.navTreeCountry(countryCode);
    }
  },

  // タブの件数バッジ更新
  updateTabCounts: function () {
    if (!this.currentCountryData) return;
    const c = this.currentCountryData.counts;
    document.getElementById("tab-count-routes").innerText = c.routes.toLocaleString();
    document.getElementById("tab-count-muni").innerText = c.municipalities.toLocaleString();
    document.getElementById("tab-count-nodes").innerText = c.nodes.toLocaleString();
  },

  // タブ切り替え
  switchTab: function (tabKey) {
    this.activeTab = tabKey;
    document.querySelectorAll(".tab-btn").forEach((btn) => {
      btn.classList.toggle("active", btn.getAttribute("data-tab") === tabKey);
    });
    this.renderCurrentTab();
  },

  // 現在のタブの内容を描画
  renderCurrentTab: function () {
    if (this.activeTab === "countries") {
      this.renderCountriesTab();
    } else if (this.activeTab === "routes") {
      this.renderRoutesTab();
    } else if (this.activeTab === "muni") {
      this.renderMuniTab();
    } else if (this.activeTab === "nodes") {
      this.renderNodesTab();
    }
  },

  // =========================================================================
  // タブ1: 🌍 国・地域一覧 (全251カ国)
  // =========================================================================
  renderCountriesTab: function () {
    const container = document.getElementById("tab-content");
    let countries = this.summaryData.countries || [];

    if (this.searchQuery) {
      countries = countries.filter((c) => {
        return (
          c.name.toLowerCase().includes(this.searchQuery) ||
          c.code.toLowerCase().includes(this.searchQuery) ||
          c.region.toLowerCase().includes(this.searchQuery)
        );
      });
    }

    if (countries.length === 0) {
      container.innerHTML = '<div class="empty-box">該当する国は見つかりませんでした。</div>';
      return;
    }

    let html = `
      <div style="font-size:12px; color:var(--text-muted); margin-bottom:12px;">
        全 ${this.summaryData.countries.length} カ国・地域中 ${countries.length} 件を表示中。国カードをクリックするとその国に切り替わります。
      </div>
      <div class="country-grid">
    `;

    countries.forEach((c) => {
      const isSelected = c.code === this.activeCountryCode;
      html += `
        <div class="country-card ${isSelected ? "active" : ""}" data-cc="${c.code}">
          <div class="country-card-header">
            <span class="country-card-title">${c.flag} ${c.name}</span>
            <span class="country-card-region">${c.region}</span>
          </div>
          <div class="country-card-stats">
            <span>🚆 路線: <b>${c.counts.routes}</b></span>
            <span>📍 拠点: <b>${c.counts.nodes}</b></span>
            <span>🏛️ 地域: <b>${c.counts.municipalities}</b></span>
          </div>
        </div>
      `;
    });

    html += `</div>`;
    container.innerHTML = html;

    container.querySelectorAll(".country-card").forEach((card) => {
      card.addEventListener("click", () => {
        const cc = card.getAttribute("data-cc");
        this.selectCountry(cc);
        this.switchTab("routes"); // 路線タブに切り替えて見せる
      });
    });
  },

  // =========================================================================
  // タブ2: 🚆 路線・交通タブ
  // =========================================================================
  renderRoutesTab: function () {
    const container = document.getElementById("tab-content");
    let routes = this.currentCountryData.routes || [];

    if (this.searchQuery) {
      routes = routes.filter((r) => {
        return (
          r.name.toLowerCase().includes(this.searchQuery) ||
          r.name_official.toLowerCase().includes(this.searchQuery) ||
          r.operator_name.toLowerCase().includes(this.searchQuery) ||
          r.mode.toLowerCase().includes(this.searchQuery)
        );
      });
    }

    if (routes.length === 0) {
      container.innerHTML = `
        <div class="empty-box">
          <p>該当する路線は見つかりませんでした。</p>
          ${this.currentCountryData.counts.routes === 0 ? '<p style="margin-top:6px; color:var(--text-muted);">※ この国の路線データは現在収集中です。</p>' : ''}
        </div>
      `;
      return;
    }

    let html = "";
    const displayRoutes = routes.slice(0, 50);

    displayRoutes.forEach((route) => {
      const hasSeq = route.has_sequence;
      html += `
        <div class="route-card" data-rid="${route.id}">
          <div class="route-header">
            <div class="route-name-group">
              <span class="route-badge">${route.mode || "交通"}</span>
              <span class="route-title">${route.name}</span>
            </div>
            <div style="display:flex; gap:6px; align-items:center;">
              ${hasSeq ? '<span class="seq-role junction" style="font-size:11px;">駅順序あり 🔗</span>' : ""}
              <button class="btn-icon btn-kp-open" data-rid="${route.id}" style="padding:2px 6px; font-size:11px;" title="詳細ナレッジを開く">📋 詳細</button>
            </div>
          </div>
          <div class="route-meta">
            <span class="route-operator">${route.operator_name || "事業者未登録"}</span>
            ${route.start || route.end ? `<span>区間: ${route.start} 〜 ${route.end}</span>` : ""}
            ${route.status ? `<span>状態: ${route.status}</span>` : ""}
          </div>
          <div class="sequence-container" id="seq-container-${route.id}" style="display: none;"></div>
        </div>
      `;
    });

    if (routes.length > 50) {
      html += `<div style="text-align:center; padding:12px; font-size:12px; color:var(--text-muted);">
        全 ${routes.length} 件中 50 件を表示しています。検索ワードで絞り込んでください。
      </div>`;
    }

    container.innerHTML = html;

    // カードクリックでアコーディオン展開
    container.querySelectorAll(".route-card").forEach((card) => {
      card.addEventListener("click", (e) => {
        if (e.target.closest(".btn-kp-open")) return;
        const rid = card.getAttribute("data-rid");
        this.toggleRouteSequence(rid, card);
      });
    });

    // 詳細ナレッジボタン
    container.querySelectorAll(".btn-kp-open").forEach((btn) => {
      btn.addEventListener("click", (e) => {
        e.stopPropagation();
        const rid = btn.getAttribute("data-rid");
        const route = routes.find((r) => r.id === rid);
        if (route) this.openKnowledgeDrawer(route, "route");
      });
    });
  },

  // 路線シーケンスの展開・折りたたみ
  toggleRouteSequence: function (routeId, cardElement) {
    const seqContainer = document.getElementById(`seq-container-${routeId}`);
    const isExpanded = cardElement.classList.contains("expanded");

    if (isExpanded) {
      cardElement.classList.remove("expanded");
      seqContainer.style.display = "none";
      return;
    }

    document.querySelectorAll(".route-card.expanded").forEach((c) => {
      c.classList.remove("expanded");
      const sc = c.querySelector(".sequence-container");
      if (sc) sc.style.display = "none";
    });

    cardElement.classList.add("expanded");
    seqContainer.style.display = "block";

    const seqNodes = (this.currentCountryData.route_nodes && this.currentCountryData.route_nodes[routeId]) || [];

    if (seqNodes.length === 0) {
      seqContainer.innerHTML = `
        <div style="font-size:12px; color:var(--text-muted); padding:6px 0;">
          ※ この路線の詳細な駅順序（繋がり）データは今後追加予定です。
        </div>
      `;
      return;
    }

    let seqHtml = `
      <div class="sequence-title">
        <span>路線繋がりシーケンス (${seqNodes.length} 駅)</span>
        <button class="btn-icon" id="btn-plot-all-${routeId}" style="font-size:11px; padding:3px 8px;">
          🗺️ 地図上に全駅を結んで表示
        </button>
      </div>
      <div class="sequence-list">
    `;

    seqNodes.forEach((node) => {
      let roleClass = "";
      if (node.role === "起点") roleClass = "origin";
      else if (node.role === "終点") roleClass = "terminal";
      else if (node.role === "分岐駅") roleClass = "junction";

      seqHtml += `
        <div class="seq-item" data-nid="${node.node_id}" data-lat="${node.lat}" data-lon="${node.lon}">
          <span class="seq-num">${node.seq}</span>
          ${node.role ? `<span class="seq-role ${roleClass}">${node.role}</span>` : ""}
          <span class="seq-name">${node.node_name}</span>
          ${node.station_number ? `<span class="seq-station-num">${node.station_number}</span>` : ""}
          <button class="btn-icon btn-node-kp" style="padding:1px 5px; font-size:10px;">📋</button>
        </div>
      `;
    });

    seqHtml += `</div>`;
    seqContainer.innerHTML = seqHtml;

    document.getElementById(`btn-plot-all-${routeId}`).addEventListener("click", (e) => {
      e.stopPropagation();
      PublicMap.plotSequence(seqNodes);
    });

    seqContainer.querySelectorAll(".seq-item").forEach((item) => {
      item.addEventListener("click", (e) => {
        e.stopPropagation();
        const nid = item.getAttribute("data-nid");
        const node = (this.currentCountryData.nodes || []).find((n) => n.id === nid) || {
          name: item.querySelector(".seq-name").innerText,
          lat: parseFloat(item.getAttribute("data-lat")),
          lon: parseFloat(item.getAttribute("data-lon")),
        };

        if (e.target.closest(".btn-node-kp")) {
          this.openKnowledgeDrawer(node, "node");
        } else {
          if (node.lat && node.lon) {
            PublicMap.flyToLocation(node.lat, node.lon, 15, `<b>${node.name}</b>`);
          }
          this.openKnowledgeDrawer(node, "node");
        }
      });
    });

    PublicMap.plotSequence(seqNodes);
  },

  // =========================================================================
  // タブ3: 🏛️ 行政区画・自治体タブ
  // =========================================================================
  renderMuniTab: function () {
    const container = document.getElementById("tab-content");
    let munis = this.currentCountryData.municipalities || [];

    if (this.searchQuery) {
      munis = munis.filter((m) => {
        return (
          m.name.toLowerCase().includes(this.searchQuery) ||
          m.name_official.toLowerCase().includes(this.searchQuery) ||
          m.category.toLowerCase().includes(this.searchQuery) ||
          m.code.toLowerCase().includes(this.searchQuery)
        );
      });
    }

    if (munis.length === 0) {
      container.innerHTML = '<div class="empty-box">該当する自治体は見つかりませんでした。</div>';
      return;
    }

    let html = "";
    const displayMunis = munis.slice(0, 100);

    displayMunis.forEach((m) => {
      html += `
        <div class="data-list-item" data-mid="${m.id}" data-lat="${m.lat}" data-lon="${m.lon}">
          <div class="item-main">
            <div class="item-name">
              <span>${m.name}</span>
              ${m.name_official ? `<span class="item-sub">(${m.name_official})</span>` : ""}
              <span class="item-badge">${m.category || "行政区域"}</span>
            </div>
            <div class="item-sub">
              ${m.code ? `コード: ${m.code}` : ""}
              ${m.parent_name ? ` | 上位: ${m.parent_name}` : ""}
            </div>
          </div>
          <div style="display:flex; gap:6px;">
            <button class="btn-icon btn-muni-kp" style="padding:4px 8px; font-size:12px;">📋 詳細</button>
            ${m.lat ? '<button class="btn-icon btn-muni-map" style="padding:4px 8px; font-size:12px;">📍 地図</button>' : ""}
          </div>
        </div>
      `;
    });

    if (munis.length > 100) {
      html += `<div style="text-align:center; padding:12px; font-size:12px; color:var(--text-muted);">
        全 ${munis.length} 件中 100 件を表示しています。
      </div>`;
    }

    container.innerHTML = html;

    container.querySelectorAll(".data-list-item").forEach((item) => {
      item.addEventListener("click", (e) => {
        const mid = item.getAttribute("data-mid");
        const muni = munis.find((m) => m.id === mid);
        if (!muni) return;

        if (e.target.closest(".btn-muni-map")) {
          if (muni.lat && muni.lon) PublicMap.flyToLocation(muni.lat, muni.lon, 12, `<b>${muni.name}</b>`);
        } else {
          this.openKnowledgeDrawer(muni, "muni");
          if (muni.lat && muni.lon) PublicMap.flyToLocation(muni.lat, muni.lon, 12);
        }
      });
    });
  },

  // =========================================================================
  // タブ4: 📍 交通拠点タブ
  // =========================================================================
  renderNodesTab: function () {
    const container = document.getElementById("tab-content");
    let nodes = this.currentCountryData.nodes || [];

    if (this.searchQuery) {
      nodes = nodes.filter((n) => {
        return (
          n.name.toLowerCase().includes(this.searchQuery) ||
          n.name_official.toLowerCase().includes(this.searchQuery) ||
          n.category.toLowerCase().includes(this.searchQuery) ||
          n.municipality_name.toLowerCase().includes(this.searchQuery)
        );
      });
    }

    if (nodes.length === 0) {
      container.innerHTML = '<div class="empty-box">該当する拠点は見つかりませんでした。</div>';
      return;
    }

    PublicMap.plotNodes(nodes, 400);

    let html = "";
    const displayNodes = nodes.slice(0, 100);

    displayNodes.forEach((n) => {
      html += `
        <div class="data-list-item" data-nid="${n.id}" data-lat="${n.lat}" data-lon="${n.lon}">
          <div class="item-main">
            <div class="item-name">
              <span>${n.name}</span>
              ${n.name_official ? `<span class="item-sub">(${n.name_official})</span>` : ""}
              <span class="item-badge">${n.category || "拠点"}</span>
            </div>
            <div class="item-sub">
              ${n.municipality_name ? `所在地: ${n.municipality_name}` : ""}
              ${n.status ? ` | 状態: ${n.status}` : ""}
            </div>
          </div>
          <div style="display:flex; gap:6px;">
            <button class="btn-icon btn-node-kp" style="padding:4px 8px; font-size:12px;">📋 詳細</button>
            ${n.lat ? '<button class="btn-icon btn-node-map" style="padding:4px 8px; font-size:12px;">📍 ズーム</button>' : ""}
          </div>
        </div>
      `;
    });

    if (nodes.length > 100) {
      html += `<div style="text-align:center; padding:12px; font-size:12px; color:var(--text-muted);">
        全 ${nodes.length} 件中 100 件を表示しています。地図上には上位400件のピンを表示中です。
      </div>`;
    }

    container.innerHTML = html;

    container.querySelectorAll(".data-list-item").forEach((item) => {
      item.addEventListener("click", (e) => {
        const nid = item.getAttribute("data-nid");
        const node = nodes.find((n) => n.id === nid);
        if (!node) return;

        if (e.target.closest(".btn-node-map")) {
          if (node.lat && node.lon) PublicMap.flyToLocation(node.lat, node.lon, 15, `<b>${node.name}</b>`);
        } else {
          this.openKnowledgeDrawer(node, "node");
          if (node.lat && node.lon) PublicMap.flyToLocation(node.lat, node.lon, 15);
        }
      });
    });
  },

  // =========================================================================
  // ナレッジパネル（詳細ドロワー／全幅カード）の制御
  // =========================================================================
  openKnowledgeDrawer: function (item, type) {
    if (this.viewMode === "tree") {
      this.navTreeDetail(item, type);
      return;
    }

    const drawer = document.getElementById("knowledge-drawer");
    const body = document.getElementById("knowledge-body");
    body.innerHTML = this.buildKnowledgeHTML(item, type);
    drawer.classList.add("open");
  },

  closeKnowledgeDrawer: function () {
    const drawer = document.getElementById("knowledge-drawer");
    if (drawer) drawer.classList.remove("open");
  },

  // ナレッジパネルHTML生成
  buildKnowledgeHTML: function (item, type) {
    if (!item) return '<div class="empty-box">詳細データがありません</div>';

    let title = item.name || item.title || "名称未登録";
    let official = item.name_official || "";
    let alias = item.alias || "";
    let category = item.category || item.mode || item.type || (type === "country" ? "国・地域" : "項目");
    let status = item.status || "運用中";

    let rows = [];

    // タイプごとの諸元テーブル作成
    if (type === "node") {
      if (item.id) rows.push(["拠点ID", item.id]);
      if (item.category) rows.push(["種別", item.category]);
      if (item.status) rows.push(["状態", item.status]);
      if (item.era) rows.push(["時代区分", item.era]);
      if (item.municipality_name) rows.push(["所在自治体", item.municipality_name]);
      if (item.lat != null && item.lon != null) rows.push(["世界測地系座標", `緯度: ${item.lat}, 経度: ${item.lon}`]);
    } else if (type === "route") {
      if (item.id) rows.push(["路線ID", item.id]);
      if (item.operator_name) rows.push(["運行事業者", item.operator_name]);
      if (item.mode) rows.push(["交通モード", item.mode]);
      if (item.number) rows.push(["路線記号・番号", item.number]);
      if (item.start || item.end) rows.push(["区間", `${item.start || "不明"} 〜 ${item.end || "不明"}`]);
      if (item.status) rows.push(["状態", item.status]);
      if (item.era) rows.push(["時代区分", item.era]);
    } else if (type === "muni") {
      if (item.id) rows.push(["自治体ID", item.id]);
      if (item.code) rows.push(["公的地域コード", item.code]);
      if (item.category) rows.push(["行政種別", item.category]);
      if (item.parent_name) rows.push(["親自治体", item.parent_name]);
      if (item.lat != null && item.lon != null) rows.push(["政庁所在地座標", `緯度: ${item.lat}, 経度: ${item.lon}`]);
      if (item.status) rows.push(["状態", item.status]);
    } else if (type === "country") {
      if (item.code) rows.push(["国コード", item.code]);
      if (item.region) rows.push(["国連地域区分", item.region]);
      if (item.official_lang) rows.push(["公用語", item.official_lang]);
      if (item.currency) rows.push(["通貨", item.currency]);
      if (item.drive_side) rows.push(["車両通行側", item.drive_side]);
    }

    // 外部リンクアクションボタン
    let actionButtons = [];
    if (item.gmap) {
      actionButtons.push(`<a href="${item.gmap}" target="_blank" rel="noopener" class="kp-btn">🗺️ Google Maps</a>`);
    } else if (item.lat != null && item.lon != null) {
      actionButtons.push(`<a href="https://www.google.com/maps/search/?api=1&query=${item.lat},${item.lon}" target="_blank" rel="noopener" class="kp-btn">🗺️ Google Maps</a>`);
    }
    if (item.wiki_ja) {
      actionButtons.push(`<a href="${item.wiki_ja}" target="_blank" rel="noopener" class="kp-btn">🌐 Wikipedia (日本語)</a>`);
    }
    if (item.wiki_en) {
      actionButtons.push(`<a href="${item.wiki_en}" target="_blank" rel="noopener" class="kp-btn">🌐 Wikipedia (英語)</a>`);
    }
    if (item.wikidata) {
      actionButtons.push(`<a href="${item.wikidata}" target="_blank" rel="noopener" class="kp-btn">🏛️ Wikidata</a>`);
    }
    if (item.osm) {
      actionButtons.push(`<a href="${item.osm}" target="_blank" rel="noopener" class="kp-btn">🗺️ OpenStreetMap</a>`);
    }
    if (item.website) {
      actionButtons.push(`<a href="${item.website}" target="_blank" rel="noopener" class="kp-btn">🔗 公式サイト</a>`);
    }

    // 諸元テーブルHTML
    let tableHtml = rows.map(([k, v]) => `<tr><th>${k}</th><td>${v}</td></tr>`).join("");

    // 路線の場合の駅順序シーケンス埋め込み
    let seqSection = "";
    if (type === "route" && this.currentCountryData.route_nodes && this.currentCountryData.route_nodes[item.id]) {
      const seqNodes = this.currentCountryData.route_nodes[item.id];
      seqSection = `
        <div style="margin-top:16px; border-top:1px solid var(--border-color); padding-top:12px;">
          <div style="font-size:13px; font-weight:700; margin-bottom:8px;">🔗 駅順シーケンス (${seqNodes.length} 駅)</div>
          <div class="sequence-list">
            ${seqNodes.map((n) => `
              <div class="seq-item" onclick="App.openKnowledgeDrawerById('${n.node_id}', 'node')">
                <span class="seq-num">${n.seq}</span>
                <span class="seq-name">${n.node_name}</span>
                <span class="seq-role">${n.role || ""}</span>
              </div>
            `).join("")}
          </div>
        </div>
      `;
    }

    return `
      <div class="kp-title-area">
        <div class="kp-title">${title}</div>
        ${official ? `<div class="kp-official-name">${official}</div>` : ""}
        ${alias ? `<div class="kp-official-name">別称: ${alias}</div>` : ""}
        <div class="kp-badges">
          <span class="route-badge">${category}</span>
          <span class="seq-role">${status}</span>
        </div>
      </div>

      <table class="kp-table">
        ${tableHtml}
      </table>

      ${actionButtons.length > 0 ? `
        <div class="kp-actions">
          ${actionButtons.join("")}
        </div>
      ` : ""}

      ${seqSection}
    `;
  },

  openKnowledgeDrawerById: function (id, type) {
    if (type === "node") {
      const node = (this.currentCountryData.nodes || []).find((n) => n.id === id);
      if (node) this.openKnowledgeDrawer(node, "node");
    }
  },

  // =========================================================================
  // 階層ディレクトリ閲覧ビュー（地図なし）の画面遷移ロジック
  // =========================================================================
  navTreeWorld: function () {
    this.treeState.level = "world";
    this.updateBreadcrumb([
      { label: "🌍 世界 (251カ国)", level: "world", current: true }
    ]);
    this.renderTreeLevelWorld();
  },

  navTreeCountry: function (countryCode) {
    this.treeState.level = "country";
    this.treeState.countryCode = countryCode;
    const cMeta = this.summaryData.countries.find((c) => c.code === countryCode) || {};
    this.updateBreadcrumb([
      { label: "🌍 世界", level: "world" },
      { label: `${cMeta.flag || ""} ${cMeta.name || countryCode}`, level: "country", current: true }
    ]);
    this.renderTreeLevelCountry();
  },

  navTreeGenre: function (countryCode, genre) {
    this.treeState.level = "genre";
    this.treeState.genre = genre;
    const cMeta = this.summaryData.countries.find((c) => c.code === countryCode) || {};
    const genreNames = { routes: "🚆 交通路線", muni: "🏛️ 行政区画・自治体", nodes: "📍 交通拠点" };

    this.updateBreadcrumb([
      { label: "🌍 世界", level: "world" },
      { label: `${cMeta.flag || ""} ${cMeta.name || countryCode}`, level: "country" },
      { label: genreNames[genre] || genre, level: "genre", current: true }
    ]);
    this.renderTreeLevelGenre();
  },

  navTreeDetail: function (item, type) {
    this.treeState.level = "detail";
    this.treeState.item = item;
    this.treeState.itemType = type;
    const cMeta = this.summaryData.countries.find((c) => c.code === this.activeCountryCode) || {};
    const genreKeys = { route: "routes", muni: "muni", node: "nodes" };
    const genreNames = { route: "🚆 交通路線", muni: "🏛️ 行政区画・自治体", node: "📍 交通拠点" };

    this.updateBreadcrumb([
      { label: "🌍 世界", level: "world" },
      { label: `${cMeta.flag || ""} ${cMeta.name || this.activeCountryCode}`, level: "country" },
      { label: genreNames[type] || "ジャンル", level: "genre", onclick: () => this.navTreeGenre(this.activeCountryCode, genreKeys[type]) },
      { label: item.name || "詳細", current: true }
    ]);

    const container = document.getElementById("tab-content");
    container.innerHTML = `
      <div class="tree-knowledge-card">
        ${this.buildKnowledgeHTML(item, type)}
        <div style="margin-top:20px; text-align:center;">
          <button class="btn-icon" onclick="App.navTreeGenre('${this.activeCountryCode}', '${genreKeys[type]}')">
            &laquo; 一覧へ戻る
          </button>
        </div>
      </div>
    `;
  },

  updateBreadcrumb: function (items) {
    const nav = document.getElementById("tree-breadcrumb");
    let html = "";
    items.forEach((it, idx) => {
      if (idx > 0) html += '<span class="breadcrumb-separator">›</span>';
      if (it.current) {
        html += `<span class="breadcrumb-current">${it.label}</span>`;
      } else {
        html += `<span class="breadcrumb-item" data-level="${it.level}">${it.label}</span>`;
      }
    });
    nav.innerHTML = html;
  },

  renderTreeCurrent: function () {
    if (this.treeState.level === "world") this.renderTreeLevelWorld();
    else if (this.treeState.level === "country") this.renderTreeLevelCountry();
    else if (this.treeState.level === "genre") this.renderTreeLevelGenre();
  },

  // 階層レベル0: 世界の全251カ国一覧
  renderTreeLevelWorld: function () {
    const container = document.getElementById("tab-content");
    let countries = this.summaryData.countries || [];

    if (this.searchQuery) {
      countries = countries.filter((c) => c.name.toLowerCase().includes(this.searchQuery) || c.code.toLowerCase().includes(this.searchQuery));
    }

    let html = `
      <div class="tree-view-container">
        <h2 style="font-size:18px; margin-bottom:12px;">🌍 世界の国・地域を選択</h2>
        <div class="country-grid">
    `;

    countries.forEach((c) => {
      html += `
        <div class="country-card" onclick="App.selectCountry('${c.code}'); App.navTreeCountry('${c.code}');">
          <div class="country-card-header">
            <span class="country-card-title">${c.flag} ${c.name}</span>
            <span class="country-card-region">${c.region}</span>
          </div>
          <div class="country-card-stats">
            <span>🚆 ${c.counts.routes} 路線</span>
            <span>📍 ${c.counts.nodes} 拠点</span>
            <span>🏛️ ${c.counts.municipalities} 自治体</span>
          </div>
        </div>
      `;
    });

    html += `</div></div>`;
    container.innerHTML = html;
  },

  // 階層レベル1: 選択国の3大ジャンルカード
  renderTreeLevelCountry: function () {
    const container = document.getElementById("tab-content");
    const d = this.currentCountryData;
    if (!d) return;

    let html = `
      <div class="tree-view-container">
        <div style="margin-bottom:20px; padding:16px; background:var(--bg-surface); border:1px solid var(--border-color); border-radius:8px;">
          <h1 style="font-size:22px; display:flex; align-items:center; gap:10px;">
            ${d.flag} ${d.name}
            <span style="font-size:14px; color:var(--text-muted); font-weight:400;">(${d.country_code})</span>
          </h1>
          <div style="font-size:13px; color:var(--text-secondary); margin-top:8px; display:flex; gap:16px; flex-wrap:wrap;">
            ${d.region ? `<span>国連地域: <b>${d.region}</b></span>` : ""}
            ${d.info && d.info.official_lang ? `<span>公用語: <b>${d.info.official_lang}</b></span>` : ""}
            ${d.info && d.info.currency ? `<span>通貨: <b>${d.info.currency}</b></span>` : ""}
          </div>
        </div>

        <h3 style="font-size:16px; margin-bottom:12px; color:var(--text-secondary);">閲覧するジャンルを選択してください</h3>

        <div class="tree-genre-cards">
          <div class="tree-genre-card" onclick="App.navTreeGenre('${d.country_code}', 'routes')">
            <div class="tree-genre-icon">🚆</div>
            <div class="tree-genre-title">交通路線</div>
            <div class="tree-genre-desc">鉄道・地下鉄・路面電車・高速道路・主要道路など</div>
            <div style="margin-top:10px; font-size:13px; font-weight:700; color:var(--primary-color);">
              登録件数: ${d.counts.routes.toLocaleString()} 路線
            </div>
          </div>

          <div class="tree-genre-card" onclick="App.navTreeGenre('${d.country_code}', 'muni')">
            <div class="tree-genre-icon">🏛️</div>
            <div class="tree-genre-title">行政区画・地域</div>
            <div class="tree-genre-desc">都道府県・連邦州・郡・市区町村・政庁所在地</div>
            <div style="margin-top:10px; font-size:13px; font-weight:700; color:var(--primary-color);">
              登録件数: ${d.counts.municipalities.toLocaleString()} 地域
            </div>
          </div>

          <div class="tree-genre-card" onclick="App.navTreeGenre('${d.country_code}', 'nodes')">
            <div class="tree-genre-icon">📍</div>
            <div class="tree-genre-title">交通拠点</div>
            <div class="tree-genre-desc">駅・インターチェンジ・空港・港湾・ターミナル</div>
            <div style="margin-top:10px; font-size:13px; font-weight:700; color:var(--primary-color);">
              登録件数: ${d.counts.nodes.toLocaleString()} 拠点
            </div>
          </div>
        </div>
      </div>
    `;

    container.innerHTML = html;
  },

  // 階層レベル2: ジャンル内の名称一覧
  renderTreeLevelGenre: function () {
    const container = document.getElementById("tab-content");
    const d = this.currentCountryData;
    const genre = this.treeState.genre;

    let items = [];
    let itemType = "";
    if (genre === "routes") {
      items = d.routes || [];
      itemType = "route";
    } else if (genre === "muni") {
      items = d.municipalities || [];
      itemType = "muni";
    } else if (genre === "nodes") {
      items = d.nodes || [];
      itemType = "node";
    }

    if (this.searchQuery) {
      items = items.filter((it) => (it.name || "").toLowerCase().includes(this.searchQuery) || (it.name_official || "").toLowerCase().includes(this.searchQuery));
    }

    let html = `
      <div class="tree-view-container">
        <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:12px;">
          <h2 style="font-size:18px;">一覧 (${items.length.toLocaleString()} 件)</h2>
          <button class="btn-icon" onclick="App.navTreeCountry('${d.country_code}')">&laquo; ジャンル選択へ</button>
        </div>
        <div style="max-height: calc(100vh - 220px); overflow-y: auto;">
    `;

    if (items.length === 0) {
      html += '<div class="empty-box">登録データがありません</div>';
    } else {
      const displayItems = items.slice(0, 100);
      displayItems.forEach((it) => {
        html += `
          <div class="data-list-item" onclick="App.navTreeDetail(App.findItemById('${it.id}', '${itemType}'), '${itemType}')">
            <div class="item-main">
              <div class="item-name">
                <span>${it.name}</span>
                ${it.name_official ? `<span class="item-sub">(${it.name_official})</span>` : ""}
                <span class="item-badge">${it.mode || it.category || ""}</span>
              </div>
              <div class="item-sub">
                ${it.operator_name ? `事業者: ${it.operator_name}` : ""}
                ${it.parent_name ? `親自治体: ${it.parent_name}` : ""}
                ${it.status ? ` | 状態: ${it.status}` : ""}
              </div>
            </div>
            <button class="btn-icon" style="padding:4px 8px; font-size:12px;">詳細を見る &raquo;</button>
          </div>
        `;
      });
      if (items.length > 100) {
        html += `<div style="text-align:center; padding:12px; font-size:12px; color:var(--text-muted);">
          全 ${items.length} 件中 100 件を表示しています。
        </div>`;
      }
    }

    html += `</div></div>`;
    container.innerHTML = html;
  },

  findItemById: function (id, type) {
    if (!this.currentCountryData) return null;
    if (type === "route") return (this.currentCountryData.routes || []).find((r) => r.id === id);
    if (type === "muni") return (this.currentCountryData.municipalities || []).find((m) => m.id === id);
    if (type === "node") return (this.currentCountryData.nodes || []).find((n) => n.id === id);
    return null;
  },
};

// 起動
window.addEventListener("DOMContentLoaded", () => {
  App.init();
});
