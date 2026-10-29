/**
 * 世界交通網・地域データ基盤 公開Webサイト
 * メインアプリケーション制御スクリプト (app.js)
 * -------------------------------------------------------------
 * 【新仕様: 地図ビューと階層ビューの完全分離】:
 * 1. 地図ビュー (map):
 *    - 左側リストなし・100%フルスクリーン表示
 *    - 地図上レイヤ切替バー（鉄道・航空・行政・気象・道路・路線ライン）
 *    - ピン・エッジクリックで右サイドからフロート詳細ナレッジパネルがスライドイン
 * 2. 階層ビュー (tree):
 *    - 地図なし・100%全幅の独立した閲覧画面
 *    - 階層遷移: 🌍 世界 (251カ国) ➔ 🇯🇵 国選択 ➔ 5大ジャンル選択 ➔ 詳細一覧
 *    - 各アイテムクリックで詳細ナレッジパネルを開いて閲覧可能
 */

const App = {
  summaryData: null,
  activeCountryCode: "JP",
  countryDataCache: {},
  currentCountryData: null,
  viewMode: "home", // 'home' | 'map' | 'tree'
  treeSearchQuery: "",
  treeState: {
    level: "country", // 'world' | 'country' | 'genre'
    countryCode: "JP",
    genre: null,      // 'routes' | 'muni' | 'nodes' | 'weather' | 'operators'
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

    // 初回表示はオープニング画面（ホーム）を明示的に維持
    this.switchViewMode("home");
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

    // 表示モード切替 (ホーム vs 地図ビュー vs 階層ビュー)
    const btnHome = document.getElementById("btn-mode-home");
    if (btnHome) btnHome.addEventListener("click", () => this.switchViewMode("home"));
    document.getElementById("btn-mode-map").addEventListener("click", () => this.switchViewMode("map"));
    document.getElementById("btn-mode-tree").addEventListener("click", () => this.switchViewMode("tree"));

    // 階層ビュー用検索入力
    const treeSearchInput = document.getElementById("tree-search-input");
    const treeClearBtn = document.getElementById("tree-search-clear-btn");

    if (treeSearchInput) {
      treeSearchInput.addEventListener("input", (e) => {
        this.treeSearchQuery = e.target.value.trim().toLowerCase();
        if (treeClearBtn) treeClearBtn.style.display = this.treeSearchQuery ? "block" : "none";
        this.renderTreeCurrent();
      });
    }

    if (treeClearBtn) {
      treeClearBtn.addEventListener("click", () => {
        if (treeSearchInput) treeSearchInput.value = "";
        this.treeSearchQuery = "";
        treeClearBtn.style.display = "none";
        this.renderTreeCurrent();
      });
    }

    // 全251カ国セレクトボックス
    document.getElementById("country-quick-select").addEventListener("change", (e) => {
      const code = e.target.value;
      if (code) this.selectCountry(code);
    });

    // 地図リセットボタン
    document.getElementById("map-reset-btn").addEventListener("click", () => {
      PublicMap.resetView();
    });

    // 地図ビュー上の制度解説ボタン
    const mapGuideBtn = document.getElementById("map-guide-btn");
    if (mapGuideBtn) {
      mapGuideBtn.addEventListener("click", () => {
        this.switchViewMode("tree");
        this.navTreeCountry(this.activeCountryCode);
        setTimeout(() => {
          const el = document.getElementById("country-guide-section");
          if (el) el.scrollIntoView({ behavior: "smooth" });
        }, 100);
      });
    }

    // ナレッジパネルの閉じるボタン
    document.getElementById("kp-close-btn").addEventListener("click", () => {
      this.closeKnowledgeDrawer();
    });
  },

  // 表示モード切り替え（ホーム vs 地図ビュー vs 階層ビュー）
  switchViewMode: function (mode) {
    this.viewMode = mode;
    const btnHome = document.getElementById("btn-mode-home");
    const btnMap = document.getElementById("btn-mode-map");
    const btnTree = document.getElementById("btn-mode-tree");

    if (btnHome) btnHome.classList.toggle("active", mode === "home");
    if (btnMap) btnMap.classList.toggle("active", mode === "map");
    if (btnTree) btnTree.classList.toggle("active", mode === "tree");

    const homePanel = document.getElementById("home-panel");
    const mapPanel = document.getElementById("map-panel");
    const treePanel = document.getElementById("tree-panel");

    this.closeKnowledgeDrawer();

    if (mode === "home") {
      document.body.classList.remove("tree-mode-active");
      if (homePanel) homePanel.style.display = "block";
      if (mapPanel) mapPanel.style.display = "none";
      if (treePanel) treePanel.style.display = "none";
    } else if (mode === "tree") {
      document.body.classList.add("tree-mode-active");
      if (homePanel) homePanel.style.display = "none";
      if (mapPanel) mapPanel.style.display = "none";
      if (treePanel) treePanel.style.display = "flex";
      this.navTreeCountry(this.activeCountryCode);
    } else { // mode === "map"
      document.body.classList.remove("tree-mode-active");
      if (homePanel) homePanel.style.display = "none";
      if (treePanel) treePanel.style.display = "none";
      if (mapPanel) mapPanel.style.display = "block";
      setTimeout(() => {
        if (PublicMap.map) PublicMap.map.invalidateSize();
      }, 50);
    }
  },

  // =========================================================================
  // サマリーデータの読み込みと国セレクター初期化
  // =========================================================================
  loadSummary: async function () {
    try {
      const res = await fetch("data/summary.json");
      if (!res.ok) throw new Error("summary.json の読み込みに失敗しました");
      this.summaryData = await res.json();

      // ヘッダーの統計ピル更新
      const stats = this.summaryData.total_stats || {};
      const statsEl = document.getElementById("stats-pill");
      if (statsEl) {
        statsEl.innerText = `全${stats.registered_countries || 251}カ国 | 路線 ${(stats.routes || 0).toLocaleString()} | 自治体 ${(stats.municipalities || 0).toLocaleString()} | 拠点 ${(stats.nodes || 0).toLocaleString()}`;
      }

      // 国セレクターバーの構築
      this.buildCountryBar();
    } catch (e) {
      console.error("サマリー読み込みエラー:", e);
    }
  },

  // 国セレクターバーの構築
  buildCountryBar: function () {
    const selectEl = document.getElementById("country-quick-select");
    const container = document.getElementById("country-selector-container");
    if (!this.summaryData || !this.summaryData.countries) return;

    selectEl.innerHTML = '<option value="">🔍 全251カ国から選ぶ...</option>';
    container.innerHTML = "";

    // 地域別にグループ化してセレクトボックスに分類表示
    const regions = {};
    this.summaryData.countries.forEach((c) => {
      const r = c.region || "その他";
      if (!regions[r]) regions[r] = [];
      regions[r].push(c);
    });

    Object.keys(regions).sort().forEach((reg) => {
      const optgroup = document.createElement("optgroup");
      optgroup.label = `── ${reg} ──`;
      regions[reg].forEach((c) => {
        const opt = document.createElement("option");
        opt.value = c.code;
        const countTxt = c.counts.routes > 0 ? ` (${c.counts.routes}路線)` : (c.counts.municipalities > 0 ? ` (${c.counts.municipalities}地域)` : "");
        const guideMark = (c.has_guide || ["JP","AT","TW","KR","CH","IT"].includes(c.code)) ? " 📘解説" : "";
        opt.innerText = `${c.flag || "🌐"} ${c.name} [${c.code}]${countTxt}${guideMark}`;
        if (c.code === this.activeCountryCode) opt.selected = true;
        optgroup.appendChild(opt);
      });
      selectEl.appendChild(optgroup);
    });

    // 主要国ピル群（登録データ件数の多い上位12カ国を優先表示）
    const sortedCountries = [...this.summaryData.countries].sort((a, b) => {
      return (b.counts.routes + b.counts.nodes + b.counts.municipalities) - (a.counts.routes + a.counts.nodes + a.counts.municipalities);
    });

    const topCountries = sortedCountries.slice(0, 12);
    topCountries.forEach((c) => {
      const pill = document.createElement("div");
      pill.className = `country-pill ${c.code === this.activeCountryCode ? "active" : ""}`;
      pill.setAttribute("data-cc", c.code);
      const countLabel = c.counts.routes > 0 ? `${c.counts.routes}路線` : `${c.counts.municipalities}地域`;
      pill.innerHTML = `
        <span>${c.flag || "🌐"}</span>
        <span>${c.name}</span>
        <span class="pill-count">${countLabel}</span>
      `;
      pill.addEventListener("click", () => this.selectCountry(c.code));
      container.appendChild(pill);
    });
  },

  // 国の選択
  selectCountry: async function (countryCode) {
    if (!countryCode) return;
    this.activeCountryCode = countryCode;
    // ホーム表示中に国が選ばれた場合は地図ビューへ遷移
    if (this.viewMode === "home") {
      this.switchViewMode("map");
    }

    // セレクトボックスとピルの選択状態更新
    const selectEl = document.getElementById("country-quick-select");
    if (selectEl) selectEl.value = countryCode;

    document.querySelectorAll(".country-pill").forEach((p) => {
      p.classList.toggle("active", p.getAttribute("data-cc") === countryCode);
    });

    // 国データ読み込み
    await this.loadCountryData(countryCode);
  },

  // 国データの取得
  loadCountryData: async function (countryCode) {
    if (this.countryDataCache[countryCode]) {
      this.currentCountryData = this.countryDataCache[countryCode];
      this.onCountryDataReady();
      return;
    }

    try {
      const url = `data/${countryCode.toLowerCase()}.json`;
      const res = await fetch(url);
      if (!res.ok) throw new Error(`${countryCode}.json の取得に失敗しました (status: ${res.status})`);
      const data = await res.json();
      this.countryDataCache[countryCode] = data;
      this.currentCountryData = data;
      this.onCountryDataReady();
    } catch (e) {
      console.warn(`国データ取得失敗: ${countryCode}`, e);
      // 空データフォールバック
      const cMeta = (this.summaryData && this.summaryData.countries.find((c) => c.code === countryCode)) || {};
      this.currentCountryData = {
        country_code: countryCode,
        name: cMeta.name || countryCode,
        flag: cMeta.flag || "🌐",
        counts: { municipalities: 0, operators: 0, routes: 0, nodes: 0, edges: 0, weather_zones: 0, sequenced_routes: 0 },
        municipalities: [],
        operators: [],
        routes: [],
        nodes: [],
        edges: [],
        route_sequences: {},
        weather_zones: [],
      };
      this.onCountryDataReady();
    }
  },

  // 国データ取得完了後の処理
  onCountryDataReady: function () {
    const d = this.currentCountryData;
    if (!d) return;

    // 1. 地図ビューの描画更新
    if (PublicMap && PublicMap.map) {
      PublicMap.setCountryView(d.map_meta, d.country_code);
      PublicMap.clearAllOverlays();

      const edgeCount = PublicMap.plotEdges(d.edges || []);
      const nodeCount = PublicMap.plotNodesCategorized(d.nodes || []);
      const muniCount = PublicMap.plotMunicipalities(d.municipalities || []);

      const countEl = document.getElementById("map-marker-count");
      if (countEl) {
        countEl.innerText = `${d.name}: 路線区間 ${edgeCount}件 | 拠点 ${nodeCount}件 | 自治体 ${muniCount}件`;
      }
    }

    // 2. 階層ビューの描画更新（階層モードがアクティブな場合）
    if (this.viewMode === "tree") {
      this.navTreeCountry(d.country_code);
    }
  },

  // =========================================================================
  // ナレッジパネル (フロート詳細ドロワー)
  // =========================================================================
  openKnowledgeDrawer: function (item, type, fromMapClick = false) {
    if (!item) return;

    const drawer = document.getElementById("knowledge-drawer");
    const body = document.getElementById("knowledge-body");
    if (!drawer || !body) return;

    body.innerHTML = this.buildKnowledgeHTML(item, type);
    this.bindRouteTemplates(body);
    drawer.classList.add("open");

    // 地図ビュー時かつ外部UI（一覧・検索・階層ツリー等）からの起動時のみ対象座標へ緩やかに移動
    // 地図マーカークリック時は既にその位置が表示されているため自動ジャンプを抑止しポップアップの即時消滅を防止
    if (!fromMapClick && this.viewMode === "map" && item.lat != null && item.lon != null && PublicMap.map) {
      PublicMap.flyToLocation(item.lat, item.lon, 13);
    }
  },

  closeKnowledgeDrawer: function () {
    const drawer = document.getElementById("knowledge-drawer");
    if (drawer) drawer.classList.remove("open");
  },

  openKnowledgeDrawerById: function (id, type) {
    const item = this.findItemById(id, type);
    if (item) this.openKnowledgeDrawer(item, type);
  },

  findItemById: function (id, type) {
    if (!this.currentCountryData) return null;
    if (type === "route") {
      return (this.currentCountryData.routes || []).find((r) => r.id === id);
    } else if (type === "muni") {
      return (this.currentCountryData.municipalities || []).find((m) => m.id === id);
    } else if (type === "node") {
      return (this.currentCountryData.nodes || []).find((n) => n.id === id);
    } else if (type === "weather") {
      return (this.currentCountryData.weather_zones || []).find((w) => w.id === id);
    } else if (type === "operator") {
      return (this.currentCountryData.operators || []).find((o) => o.id === id);
    }
    return null;
  },

  // ナレッジパネルHTML生成 (全7分野対応)
  buildKnowledgeHTML: function (item, type) {
    if (!item) return '<div class="empty-box">詳細データがありません</div>';

    let title = item.name || item.title || "名称未登録";
    let official = item.name_official || "";
    let alias = item.alias || item.short_name || "";
    let category = item.category || item.mode || item.type || (type === "country" ? "国・地域" : "項目");
    let status = item.status || "運用中";

    let rows = [];
    let customSections = "";

    // 1. 自治体・行政区画 (muni)
    if (type === "muni") {
      if (item.id) rows.push(["自治体ID", item.id]);
      if (item.code) rows.push(["公的地域コード", item.code]);
      if (item.category) rows.push(["行政種別", item.category]);
      if (item.parent_name) rows.push(["親区画", item.parent_name]);
      if (item.pop) rows.push(["人口", `${item.pop.toLocaleString()} 人`]);
      if (item.area_km2) rows.push(["面積", `${item.area_km2} km²`]);
      if (item.lat != null && item.lon != null) rows.push(["政庁座標", `緯度: ${item.lat}, 経度: ${item.lon}`]);
      if (item.status) rows.push(["状態", item.status]);

      // 🌤️ 外部天気予報リンク4社
      if (item.weather_urls && Object.keys(item.weather_urls).length > 0) {
        const wu = item.weather_urls;
        customSections += `
          <div class="kp-section-title">🌤️ 外部天気予報リンク（公式・大手4社）</div>
          <div class="weather-forecast-grid">
            <a href="${wu.jma}" target="_blank" rel="noopener" class="weather-card-link">
              <span>🌦️ 気象庁公式</span>
            </a>
            <a href="${wu.tenki}" target="_blank" rel="noopener" class="weather-card-link">
              <span>☀️ tenki.jp</span>
            </a>
            <a href="${wu.weathernews}" target="_blank" rel="noopener" class="weather-card-link">
              <span>☔ ウェザーニュース</span>
            </a>
            <a href="${wu.yahoo}" target="_blank" rel="noopener" class="weather-card-link">
              <span>⛅ Yahoo!天気</span>
            </a>
          </div>
        `;
      }

      // 🌡️ 管内アメダス実況リンク
      if (item.amedas && item.amedas.length > 0) {
        customSections += `
          <div class="kp-section-title">🌡️ 管内アメダス観測所 (${item.amedas.length} 地点)</div>
          <div class="kp-pill-list">
            ${item.amedas.map((a) => `
              <a href="${a.obs_url}" target="_blank" rel="noopener" class="kp-pill-item" style="text-decoration:none; color:var(--text-primary);">
                🌡️ <b>${a.name}</b> ${a.elevation != null ? `(${a.elevation}m)` : ''} &raquo;
              </a>
            `).join("")}
          </div>
        `;
      }

      // 🚆 通過路線一覧
      if (item.passed_routes && item.passed_routes.length > 0) {
        customSections += `
          <div class="kp-section-title">🚆 域内を通過する路線 (${item.passed_routes.length} 路線)</div>
          <div class="kp-pill-list">
            ${item.passed_routes.map((r) => `
              <span class="kp-pill-item" onclick="App.openKnowledgeDrawerById('${r.id}', 'route')">
                🚆 ${r.name}
              </span>
            `).join("")}
          </div>
        `;
      }

      // 担当気象台
      if (item.weather_zones && item.weather_zones.length > 0) {
        customSections += `
          <div class="kp-section-title">🏢 管轄気象予報区・気象台</div>
          <div style="font-size:12px; color:var(--text-secondary); line-height:1.6;">
            ${item.weather_zones.map((w) => `・${w.name} (${w.type || '予報区'}) / 担当: ${w.office || '気象台'}`).join("<br>")}
          </div>
        `;
      }
    }

    // 2. 交通拠点 (node)
    else if (type === "node") {
      if (item.id) rows.push(["拠点ID", item.id]);
      if (item.sub_category || item.category) rows.push(["種別", item.sub_category || item.category]);
      if (item.code) rows.push(["拠点コード", item.code]);
      if (item.track_type) rows.push(["配線種別", item.track_type]);
      if (item.elevation != null) rows.push(["標高", `${item.elevation} m`]);
      if (item.length != null) rows.push(["延長", `${item.length} m`]);
      if (item.muni_name) rows.push(["所在自治体", item.muni_name]);
      if (item.lat != null && item.lon != null) rows.push(["座標", `緯度: ${item.lat}, 経度: ${item.lon}`]);
      if (item.status) rows.push(["状態", item.status]);

      // 前後駅ナビゲーション
      if (item.adjacent && item.adjacent.length > 0) {
        const prevList = item.adjacent.filter((a) => a.direction === "prev");
        const nextList = item.adjacent.filter((a) => a.direction === "next");

        customSections += `
          <div class="kp-section-title">🔗 所属路線の前後の隣接拠点</div>
          <div class="kp-adjacent-box">
            <div>
              ${prevList.length > 0 ? prevList.map((p) => `
                <div class="kp-adj-link" onclick="App.openKnowledgeDrawerById('${p.neighbor_id}', 'node')">
                  ◀ ${p.neighbor_name}
                  <div style="font-size:10px; color:var(--text-muted);">${p.route_name} (${p.dist_km}km)</div>
                </div>
              `).join("") : '<span style="font-size:11px; color:var(--text-muted);">［起点端］</span>'}
            </div>
            <div class="kp-adj-curr">
              ${item.name}
            </div>
            <div>
              ${nextList.length > 0 ? nextList.map((n) => `
                <div class="kp-adj-link" onclick="App.openKnowledgeDrawerById('${n.neighbor_id}', 'node')">
                  ${n.neighbor_name} ▶
                  <div style="font-size:10px; color:var(--text-muted);">${n.route_name} (${n.dist_km}km)</div>
                </div>
              `).join("") : '<span style="font-size:11px; color:var(--text-muted);">［終点端］</span>'}
            </div>
          </div>
        `;
      }

      // 乗換路線
      if (item.transfers && item.transfers.length > 0) {
        customSections += `
          <div class="kp-section-title">🚆 乗換可能路線 (${item.transfers.length} 路線)</div>
          <div class="kp-pill-list">
            ${item.transfers.map((t) => `
              <span class="kp-pill-item" onclick="App.openKnowledgeDrawerById('${t.id}', 'route')">
                🚆 ${t.name}
              </span>
            `).join("")}
          </div>
        `;
      }
    }

    // 3. 交通路線 (route)
    else if (type === "route") {
      if (item.id) rows.push(["路線ID", item.id]);
      if (item.operator_name) rows.push(["運行事業者", item.operator_name]);
      if (item.mode) rows.push(["交通モード", item.mode]);
      if (item.number) rows.push(["路線番号・記号", item.number]);
      if (item.km != null) rows.push(["営業キロ", `${item.km} km`]);
      if (item.gauge) rows.push(["軌間", item.gauge]);
      if (item.electrified) rows.push(["電化方式", item.electrified]);
      if (item.start || item.end) rows.push(["区間", `${item.start || "不明"} 〜 ${item.end || "不明"}`]);
      if (item.status) rows.push(["状態", item.status]);

      // Wikipedia風テンプレート埋め込み（停車場一覧表）
      const rawNodes = (this.currentCountryData.route_sequences && this.currentCountryData.route_sequences[item.id]) || [];
      if (rawNodes.length > 0) {
        customSections += `<div class="wiki-embed" data-rid="${item.id}"></div>`;
      }
    }

    // 4. 気象予報区 (weather)
    else if (type === "weather") {
      if (item.id) rows.push(["予報区ID", item.id]);
      if (item.code) rows.push(["予報区コード", item.code]);
      if (item.type) rows.push(["種別", item.type]);
      if (item.office) rows.push(["担当気象台", item.office]);
      if (item.muni_count) rows.push(["管轄自治体数", `${item.muni_count} 自治体`]);
    }

    // 5. 事業者 (operator)
    else if (type === "operator") {
      if (item.id) rows.push(["事業者ID", item.id]);
      if (item.type) rows.push(["業種別", item.type]);
      if (item.status) rows.push(["状態", item.status]);

      if (item.routes && item.routes.length > 0) {
        customSections += `
          <div class="kp-section-title">🚆 運行・管轄路線 (${item.routes.length} 路線)</div>
          <div class="kp-pill-list">
            ${item.routes.map((r) => `
              <span class="kp-pill-item" onclick="App.openKnowledgeDrawerById('${r.id}', 'route')">
                🚆 ${r.name} (${r.mode || '路線'})
              </span>
            `).join("")}
          </div>
        `;
      }
    }

    // 外部リンクアクションボタン
    let actionButtons = [];
    if (item.sv_url) {
      actionButtons.push(`<a href="${item.sv_url}" target="_blank" rel="noopener" class="kp-btn" style="background:#e0f2fe; color:#0369a1; border-color:#bae6fd;">👀 ストリートビュー起動</a>`);
    }
    if (item.obs_url) {
      actionButtons.push(`<a href="${item.obs_url}" target="_blank" rel="noopener" class="kp-btn" style="background:#fee2e2; color:#991b1b; border-color:#fecaca;">🌡️ 気象庁公式実況データ</a>`);
    }
    if (item.gmap) {
      actionButtons.push(`<a href="${item.gmap}" target="_blank" rel="noopener" class="kp-btn">🗺️ Google Maps</a>`);
    } else if (item.lat != null && item.lon != null) {
      actionButtons.push(`<a href="https://www.google.com/maps/search/?api=1&query=${item.lat},${item.lon}" target="_blank" rel="noopener" class="kp-btn">🗺️ Google Maps</a>`);
    }
    if (item.wiki_ja) {
      actionButtons.push(`<a href="${item.wiki_ja}" target="_blank" rel="noopener" class="kp-btn">🌐 Wikipedia (日本語)</a>`);
    }
    if (item.website) {
      actionButtons.push(`<a href="${item.website}" target="_blank" rel="noopener" class="kp-btn">🔗 公式サイト</a>`);
    }

    return `
      <div class="kp-title-area">
        <div class="kp-title">
          <span>${title}</span>
          <span class="item-badge" style="font-size:11px;">${category}</span>
        </div>
        ${official ? `<div class="kp-official-name">正式・公用語: ${official}</div>` : ""}
        ${alias ? `<div class="kp-official-name">別称・略称: ${alias}</div>` : ""}
      </div>

      <div class="kp-meta-table">
        ${rows.map(([label, val]) => `
          <div class="kp-meta-row">
            <div class="kp-meta-label">${label}</div>
            <div class="kp-meta-val">${val}</div>
          </div>
        `).join("")}
      </div>

      ${actionButtons.length > 0 ? `
        <div class="kp-actions">
          ${actionButtons.join("")}
        </div>
      ` : ""}

      ${customSections}
    `;
  },

  // ナレッジパネル内のWikipedia風停車場一覧表描画
  bindRouteTemplates: function (root) {
    if (!root || !this.currentCountryData) return;
    root.querySelectorAll(".wiki-embed[data-rid]").forEach((el) => {
      const rid = el.getAttribute("data-rid");
      const route = (this.currentCountryData.routes || []).find((r) => r.id === rid) || { id: rid, name: "路線" };
      const raw = (this.currentCountryData.route_sequences && this.currentCountryData.route_sequences[rid]) || [];
      if (raw.length) this.renderRouteSequenceContent(route, raw, el);
    });
  },

  renderRouteSequenceContent: function (route, rawNodes, container) {
    const tableNodes = rawNodes;

    let html = `
      <div class="kp-section-title" style="margin-top:16px;">
        <span>🚆 駅一覧表 (${tableNodes.length} 駅)</span>
      </div>
      <div class="wiki-table-wrapper" style="max-height:360px; overflow-y:auto; border:1px solid var(--border-color); border-radius:6px; margin-top:8px;">
        <table class="wiki-station-table" style="width:100%; border-collapse:collapse; font-size:12px;">
          <thead>
            <tr style="background:var(--bg-surface-alt); border-bottom:1px solid var(--border-color); text-align:left;">
              <th style="padding:6px 8px;">駅名</th>
              <th style="padding:6px 8px;">駅間</th>
              <th style="padding:6px 8px;">累計</th>
              <th style="padding:6px 8px;">配線</th>
              <th style="padding:6px 8px;">所在地</th>
            </tr>
          </thead>
          <tbody>
            ${tableNodes.map((n) => `
              <tr style="border-bottom:1px solid var(--border-color); cursor:pointer;" onclick="App.openKnowledgeDrawerById('${n.node_id}', 'node')">
                <td style="padding:6px 8px; font-weight:600; color:var(--primary-color);">
                  ${n.station_number ? `<span style="display:inline-block; background:var(--primary-light); color:var(--primary-color); padding:1px 4px; border-radius:3px; font-size:10px; margin-right:4px;">${n.station_number}</span>` : ""}
                  ${n.node_name}
                </td>
                <td style="padding:6px 8px; color:var(--text-muted);">${n.km != null ? `${n.km}km` : '-'}</td>
                <td style="padding:6px 8px; color:var(--text-muted);">${n.total_km != null ? `${n.total_km}km` : '-'}</td>
                <td style="padding:6px 8px;">${n.track_type ? `<span style="font-size:10px; background:var(--border-color); padding:1px 4px; border-radius:3px;">${n.track_type}</span>` : '-'}</td>
                <td style="padding:6px 8px; color:var(--text-secondary); font-size:11px;">${n.muni_name || '-'}</td>
              </tr>
            `).join("")}
          </tbody>
        </table>
      </div>
    `;

    container.innerHTML = html;
  },

  // =========================================================================
  // 階層ディレクトリビュー (全幅・独立探索モード)
  // =========================================================================
  updateBreadcrumb: function (items) {
    const nav = document.getElementById("tree-breadcrumb");
    if (!nav) return;
    nav.innerHTML = "";

    items.forEach((it, idx) => {
      if (idx > 0) {
        const sep = document.createElement("span");
        sep.className = "breadcrumb-separator";
        sep.innerText = "›";
        nav.appendChild(sep);
      }

      const span = document.createElement("span");
      if (it.current) {
        span.className = "breadcrumb-current";
        span.innerText = it.label;
      } else {
        span.className = "breadcrumb-item";
        span.innerText = it.label;
        span.addEventListener("click", () => {
          if (it.level === "world") this.navTreeWorld();
          else if (it.level === "country") this.navTreeCountry(this.treeState.countryCode);
          else if (it.level === "genre") this.navTreeGenre(this.treeState.countryCode, this.treeState.genre);
        });
      }
      nav.appendChild(span);
    });
  },

  navTreeWorld: function () {
    this.treeState.level = "world";
    this.updateBreadcrumb([
      { label: "🌍 世界 (251カ国・地域)", level: "world", current: true }
    ]);
    this.renderTreeLevelWorld();
  },

  navTreeCountry: function (countryCode) {
    this.treeState.level = "country";
    this.treeState.countryCode = countryCode;
    const cMeta = (this.summaryData && this.summaryData.countries.find((c) => c.code === countryCode)) || {};
    this.updateBreadcrumb([
      { label: "🌍 世界", level: "world" },
      { label: `${cMeta.flag || "🌐"} ${cMeta.name || countryCode}`, level: "country", current: true }
    ]);
    this.renderTreeLevelCountry();
  },

  navTreeGenre: function (countryCode, genre) {
    this.treeState.level = "genre";
    this.treeState.genre = genre;
    const cMeta = (this.summaryData && this.summaryData.countries.find((c) => c.code === countryCode)) || {};
    const genreNames = {
      routes: "🚆 交通路線",
      muni: "🏛️ 行政区画・自治体",
      nodes: "📍 交通拠点",
      weather: "🌡️ 気象予報区",
      operators: "🏢 運行事業者",
    };

    this.updateBreadcrumb([
      { label: "🌍 世界", level: "world" },
      { label: `${cMeta.flag || "🌐"} ${cMeta.name || countryCode}`, level: "country" },
      { label: genreNames[genre] || genre, level: "genre", current: true }
    ]);
    this.renderTreeLevelGenre();
  },

  renderTreeCurrent: function () {
    if (this.treeState.level === "world") this.renderTreeLevelWorld();
    else if (this.treeState.level === "country") this.renderTreeLevelCountry();
    else if (this.treeState.level === "genre") this.renderTreeLevelGenre();
  },

  // 1. 世界レベル（全251カ国カード一覧）
  renderTreeLevelWorld: function () {
    const container = document.getElementById("tree-content");
    if (!container) return;
    let countries = (this.summaryData && this.summaryData.countries) || [];

    if (this.treeSearchQuery) {
      countries = countries.filter((c) => (c.name || "").toLowerCase().includes(this.treeSearchQuery) || (c.code || "").toLowerCase().includes(this.treeSearchQuery));
    }

    let html = `
      <div class="tree-view-container" style="max-width:1200px; margin:0 auto;">
        <div style="margin-bottom:16px;">
          <h2 style="font-size:20px; font-weight:700;">🌍 世界251カ国・地域 ディレクトリ</h2>
          <p style="font-size:13px; color:var(--text-muted); margin-top:4px;">国を選択すると、その国の行政区画・交通網・気象予報区の階層を閲覧できます。</p>
        </div>
        <div style="display:grid; grid-template-columns: repeat(auto-fill, minmax(260px, 1fr)); gap:14px;">
    `;

    countries.forEach((c) => {
      html += `
        <div class="tree-country-card" onclick="App.selectCountry('${c.code}'); App.navTreeCountry('${c.code}')" style="background:var(--bg-surface); border:1px solid var(--border-color); border-radius:8px; padding:14px; cursor:pointer; transition:all 0.15s ease;">
          <div style="font-size:28px; margin-bottom:6px;">${c.flag || "🌐"}</div>
          <div style="font-weight:700; font-size:15px; color:var(--text-primary);">${c.name} [${c.code}]</div>
          <div style="font-size:12px; color:var(--text-muted); margin-top:2px;">地域: ${c.region || "その他"}</div>
          <div style="margin-top:10px; font-size:12px; color:var(--text-secondary); border-top:1px dashed var(--border-color); padding-top:8px; display:flex; gap:8px; flex-wrap:wrap;">
            ${c.counts.routes > 0 ? `<span class="stat-pill">🚆 ${c.counts.routes} 路線</span>` : ""}
            ${c.counts.municipalities > 0 ? `<span class="stat-pill">🏛️ ${c.counts.municipalities} 地域</span>` : ""}
            ${c.counts.nodes > 0 ? `<span class="stat-pill">📍 ${c.counts.nodes} 拠点</span>` : ""}
          </div>
        </div>
      `;
    });

    html += `</div></div>`;
    container.innerHTML = html;
  },

  // 2. 国レベル（国概要 ＆ 5大ジャンル選択カード）
  renderTreeLevelCountry: function () {
    const container = document.getElementById("tree-content");
    const d = this.currentCountryData;
    if (!container || !d) return;

    let html = `
      <div class="tree-view-container" style="max-width:1200px; margin:0 auto;">
        <div style="background:var(--bg-surface); border:1px solid var(--border-color); border-radius:10px; padding:20px; margin-bottom:20px; box-shadow:var(--shadow-sm);">
          <div style="display:flex; justify-content:space-between; align-items:flex-start; flex-wrap:wrap; gap:12px;">
            <div>
              <h2 style="font-size:24px; font-weight:700; display:flex; align-items:center; gap:10px;">
                <span>${d.flag || "🌐"}</span>
                <span>${d.name}</span>
                <span style="font-size:14px; color:var(--text-muted); font-weight:400;">(${d.country_code})</span>
              </h2>
              ${d.name_official ? `<div style="font-size:13px; color:var(--text-secondary); margin-top:4px;">正式名: ${d.name_official}</div>` : ""}
            </div>
            <button class="btn-icon" onclick="App.navTreeWorld()" style="font-size:12px;">🌍 世界一覧に戻る</button>
          </div>

          <div style="margin-top:12px; font-size:13px; color:var(--text-secondary); display:flex; gap:16px; flex-wrap:wrap; border-top:1px solid var(--border-color); padding-top:12px;">
            ${d.info && d.info.official_lang ? `<span>公用語: <b>${d.info.official_lang}</b></span>` : ""}
            ${d.info && d.info.currency ? `<span>通貨: <b>${d.info.currency}</b></span>` : ""}
            ${d.info && d.info.drive_side ? `<span>車両通行側: <b>${d.info.drive_side}</b></span>` : ""}
            ${d.info && d.info.pop ? `<span>推計人口: <b>${d.info.pop.toLocaleString()} 人</b></span>` : ""}
          </div>
        </div>

        <!-- 📘 国・制度インフラ解説ガイド -->
        ${this.buildCountryGuideHTML(d.guide, d.country_code, d.name, d.flag)}

        <h3 style="font-size:17px; font-weight:700; margin-bottom:14px; color:var(--text-primary);">探索するジャンルを選択してください</h3>

        <div class="tree-genre-cards" style="display:grid; grid-template-columns:repeat(auto-fit, minmax(280px, 1fr)); gap:16px;">
          <div class="tree-genre-card" onclick="App.navTreeGenre('${d.country_code}', 'muni')" style="background:var(--bg-surface); border:1px solid var(--border-color); border-radius:8px; padding:20px; cursor:pointer; transition:all 0.15s ease;">
            <div class="tree-genre-icon" style="font-size:36px; margin-bottom:8px;">🏛️</div>
            <div class="tree-genre-title" style="font-size:17px; font-weight:700;">行政区画・自治体</div>
            <div class="tree-genre-desc" style="font-size:12px; color:var(--text-muted); margin-top:4px;">都道府県・市町村・政庁代表点・天気予報4社リンク</div>
            <div style="margin-top:12px; font-size:13px; font-weight:700; color:var(--primary-color);">
              登録件数: ${(d.counts.municipalities || 0).toLocaleString()} 地域
            </div>
          </div>

          <div class="tree-genre-card" onclick="App.navTreeGenre('${d.country_code}', 'routes')" style="background:var(--bg-surface); border:1px solid var(--border-color); border-radius:8px; padding:20px; cursor:pointer; transition:all 0.15s ease;">
            <div class="tree-genre-icon" style="font-size:36px; margin-bottom:8px;">🚆</div>
            <div class="tree-genre-title" style="font-size:17px; font-weight:700;">交通路線</div>
            <div class="tree-genre-desc" style="font-size:12px; color:var(--text-muted); margin-top:4px;">新幹線・在来線・地下鉄・国内航空路・高速道路</div>
            <div style="margin-top:12px; font-size:13px; font-weight:700; color:var(--primary-color);">
              登録件数: ${(d.counts.routes || 0).toLocaleString()} 路線
            </div>
          </div>

          <div class="tree-genre-card" onclick="App.navTreeGenre('${d.country_code}', 'nodes')" style="background:var(--bg-surface); border:1px solid var(--border-color); border-radius:8px; padding:20px; cursor:pointer; transition:all 0.15s ease;">
            <div class="tree-genre-icon" style="font-size:36px; margin-bottom:8px;">📍</div>
            <div class="tree-genre-title" style="font-size:17px; font-weight:700;">交通拠点・施設</div>
            <div class="tree-genre-desc" style="font-size:12px; color:var(--text-muted); margin-top:4px;">鉄道駅・空港・港湾・高速IC・道の駅・トンネル/橋</div>
            <div style="margin-top:12px; font-size:13px; font-weight:700; color:var(--primary-color);">
              登録件数: ${(d.counts.nodes || 0).toLocaleString()} 拠点
            </div>
          </div>

          <div class="tree-genre-card" onclick="App.navTreeGenre('${d.country_code}', 'weather')" style="background:var(--bg-surface); border:1px solid var(--border-color); border-radius:8px; padding:20px; cursor:pointer; transition:all 0.15s ease;">
            <div class="tree-genre-icon" style="font-size:36px; margin-bottom:8px;">🌡️</div>
            <div class="tree-genre-title" style="font-size:17px; font-weight:700;">気象予報区</div>
            <div class="tree-genre-desc" style="font-size:12px; color:var(--text-muted); margin-top:4px;">気象庁地方予報区・府県予報区・一次細分区域・担当気象台</div>
            <div style="margin-top:12px; font-size:13px; font-weight:700; color:var(--primary-color);">
              登録件数: ${(d.counts.weather_zones || 0).toLocaleString()} 予報区
            </div>
          </div>

          <div class="tree-genre-card" onclick="App.navTreeGenre('${d.country_code}', 'operators')" style="background:var(--bg-surface); border:1px solid var(--border-color); border-radius:8px; padding:20px; cursor:pointer; transition:all 0.15s ease;">
            <div class="tree-genre-icon" style="font-size:36px; margin-bottom:8px;">🏢</div>
            <div class="tree-genre-title" style="font-size:17px; font-weight:700;">運行事業者・管理者</div>
            <div class="tree-genre-desc" style="font-size:12px; color:var(--text-muted); margin-top:4px;">JR各社・大手私鉄・地下鉄公営・航空海運各社</div>
            <div style="margin-top:12px; font-size:13px; font-weight:700; color:var(--primary-color);">
              登録件数: ${(d.counts.operators || 0).toLocaleString()} 社
            </div>
          </div>
        </div>
      </div>
    `;

    container.innerHTML = html;
  },

  // 3. ジャンルレベル（詳細一覧・検索フィルター）
  renderTreeLevelGenre: function () {
    const container = document.getElementById("tree-content");
    const d = this.currentCountryData;
    const genre = this.treeState.genre;
    if (!container || !d) return;

    let items = [];
    let itemType = "";
    let genreTitle = "";

    if (genre === "routes") {
      items = d.routes || [];
      itemType = "route";
      genreTitle = "交通路線";
    } else if (genre === "muni") {
      items = d.municipalities || [];
      itemType = "muni";
      genreTitle = "行政区画・自治体";
    } else if (genre === "nodes") {
      items = d.nodes || [];
      itemType = "node";
      genreTitle = "交通拠点・施設";
    } else if (genre === "weather") {
      items = d.weather_zones || [];
      itemType = "weather";
      genreTitle = "気象予報区";
    } else if (genre === "operators") {
      items = d.operators || [];
      itemType = "operator";
      genreTitle = "運行事業者";
    }

    if (this.treeSearchQuery) {
      items = items.filter((it) => (it.name || "").toLowerCase().includes(this.treeSearchQuery) || (it.name_official || "").toLowerCase().includes(this.treeSearchQuery) || (it.code || "").toLowerCase().includes(this.treeSearchQuery) || (it.category || "").toLowerCase().includes(this.treeSearchQuery));
    }

    let html = `
      <div class="tree-view-container" style="max-width:1200px; margin:0 auto;">
        <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:16px; flex-wrap:wrap; gap:12px;">
          <div>
            <h2 style="font-size:20px; font-weight:700;">${genreTitle} 一覧 (${items.length.toLocaleString()} 件)</h2>
            <div style="font-size:12px; color:var(--text-muted); margin-top:2px;">項目をクリックすると、右サイドに詳細ナレッジパネルが表示されます。</div>
          </div>
          <button class="btn-icon" onclick="App.navTreeCountry('${d.country_code}')">&laquo; ジャンル選択に戻る</button>
        </div>

        <div style="display:grid; grid-template-columns:repeat(auto-fill, minmax(320px, 1fr)); gap:12px;">
    `;

    if (items.length === 0) {
      html += '<div class="empty-box" style="grid-column:1/-1;">該当するデータが見つかりませんでした</div>';
    } else {
      const displayItems = items.slice(0, 200);
      displayItems.forEach((it) => {
        html += `
          <div class="data-list-item" onclick="App.openKnowledgeDrawerById('${it.id}', '${itemType}')" style="background:var(--bg-surface); border:1px solid var(--border-color); border-radius:8px; padding:12px; cursor:pointer; transition:all 0.15s ease;">
            <div class="item-main">
              <div class="item-name" style="font-weight:700; font-size:14px; display:flex; align-items:center; gap:6px;">
                <span>${it.name}</span>
                ${it.name_official ? `<span class="item-sub" style="font-size:11px; color:var(--text-muted);">(${it.name_official})</span>` : ""}
                <span class="item-badge" style="font-size:10px;">${it.mode || it.category || it.type || ""}</span>
              </div>
              <div class="item-sub" style="font-size:12px; color:var(--text-secondary); margin-top:4px;">
                ${it.operator_name ? `<span>事業者: ${it.operator_name}</span> | ` : ""}
                ${it.parent_name ? `<span>親区画: ${it.parent_name}</span> | ` : ""}
                ${it.office ? `<span>担当: ${it.office}</span> | ` : ""}
                ${it.km != null ? `<span>${it.km} km</span> | ` : ""}
                ${it.code ? `<span>コード: ${it.code}</span>` : ""}
              </div>
            </div>
          </div>
        `;
      });
    }

    if (items.length > 200) {
      html += `
        <div style="grid-column:1/-1; text-align:center; padding:16px; font-size:12px; color:var(--text-muted);">
          全 ${items.length.toLocaleString()} 件中 200 件を表示しています。上部の検索バーで絞り込んでください。
        </div>
      `;
    }

    html += `</div></div>`;
    container.innerHTML = html;
  },

  // =========================================================================
  // 📘 国・制度インフラ解説ガイド (Country & Infrastructure Guide)
  // =========================================================================
  buildCountryGuideHTML: function (guide, cc, name, flag) {
    if (!guide) {
      // 事前調査未実施国向け案内
      return `
        <div class="country-guide-container pending" id="country-guide-section">
          <div class="guide-header">
            <div class="guide-header-top">
              <div class="guide-header-title">
                <span>📘</span>
                <span>制度・インフラ解説</span>
              </div>
            </div>
          </div>
          <div class="guide-pending-box">
            <div class="guide-pending-icon">📝</div>
            <div class="guide-pending-title">※現在、制度・インフラの事前調査を準備中です。</div>
            <div class="guide-pending-sub">
              本プロジェクトでは各国の現行地方行政区画・気象観測網・交通インフラ体系を事前調査しています。<br>
              以下の国で制度・インフラ解説ガイドを公開しています。
            </div>
            <div class="guide-pending-countries">
              <button class="guide-country-link-btn" onclick="App.selectCountry('JP')">🇯🇵 日本</button>
              <button class="guide-country-link-btn" onclick="App.selectCountry('AT')">🇦🇹 オーストリア</button>
              <button class="guide-country-link-btn" onclick="App.selectCountry('TW')">🇹🇼 台湾</button>
              <button class="guide-country-link-btn" onclick="App.selectCountry('KR')">🇰🇷 韓国</button>
              <button class="guide-country-link-btn" onclick="App.selectCountry('CH')">🇨🇭 スイス</button>
              <button class="guide-country-link-btn" onclick="App.selectCountry('IT')">🇮🇹 イタリア</button>
            </div>
          </div>
        </div>
      `;
    }

    const bi = guide.basic_info || {};
    const ah = guide.admin_hierarchy || {};
    const ws = guide.weather_system || {};
    const ts = guide.transit_system || {};
        const portals = guide.official_portals || [];

    // 1. 基本情報・行政タブ
    let basicHtml = `
      <div class="guide-section-block">
        <div class="guide-block-title">🌐 国の基本情報・地理的範囲</div>
        <div class="guide-info-grid">
          <div class="guide-info-card">
            <div class="guide-info-card-label">国家体制</div>
            <div class="guide-info-card-value">${bi.government_type || "-"}</div>
          </div>
          <div class="guide-info-card">
            <div class="guide-info-card-label">公用語</div>
            <div class="guide-info-card-value">${bi.official_languages || "-"}</div>
          </div>
          <div class="guide-info-card" style="grid-column: 1 / -1;">
            <div class="guide-info-card-label">領土・地理的特徴</div>
            <div class="guide-info-card-value">${bi.territory_bbox || "-"}</div>
          </div>
          ${bi.special_regions ? `
          <div class="guide-info-card" style="grid-column: 1 / -1;">
            <div class="guide-info-card-label">飛び地・特殊行政区域</div>
            <div class="guide-info-card-value">${bi.special_regions}</div>
          </div>` : ""}
        </div>
      </div>

      <div class="guide-section-block">
        <div class="guide-block-title">🏛️ 行政区画の制度階層</div>
        ${ah.summary ? `<div class="guide-text-summary">${ah.summary}</div>` : ""}
        <div class="guide-table-wrapper">
          <table class="guide-table">
            <thead>
              <tr>
                <th style="width:70px;">階層</th>
                <th>種別名（日本語）</th>
                <th>公用語 / 原語名</th>
                <th style="width:110px;">規模目安</th>
                <th>制度上の位置づけ・自治権の有無・役割</th>
              </tr>
            </thead>
            <tbody>
              ${(ah.levels || []).map(l => `
                <tr>
                  <td><span class="guide-level-badge">第${l.level}級</span></td>
                  <td style="font-weight:700; color:var(--text-primary);">${l.name_ja}</td>
                  <td>${l.name_local || "-"}</td>
                  <td><b>${l.scale || "-"}</b></td>
                  <td>${l.description || "-"}</td>
                </tr>
              `).join("")}
            </tbody>
          </table>
        </div>
      </div>
    `;

    // 2. 気象予報・観測タブ
    let weatherHtml = `
      <div class="guide-section-block">
        <div class="guide-block-title">🌦️ 国家気象機関</div>
        <div class="guide-info-card" style="margin-bottom:14px;">
          <div style="display:flex; justify-content:space-between; align-items:center; flex-wrap:wrap; gap:8px;">
            <div>
              <div style="font-size:16px; font-weight:700; color:var(--text-primary);">${ws.agency_name || "-"}</div>
              <div style="font-size:12px; color:var(--text-muted); margin-top:2px;">${ws.agency_desc || ""}</div>
            </div>
            ${ws.agency_url ? `
              <a href="${ws.agency_url}" target="_blank" rel="noopener" class="guide-country-link-btn" style="color:var(--primary-color); border-color:var(--primary-color); text-decoration:none;">
                🌐 公式気象サイト ↗
              </a>
            ` : ""}
          </div>
        </div>
      </div>

      <div class="guide-section-block">
        <div class="guide-block-title">🗺️ 気象予報区・警報区域の階層構造</div>
        <div class="guide-table-wrapper">
          <table class="guide-table">
            <thead>
              <tr>
                <th>予報区・区域区分</th>
                <th style="width:120px;">規模目安</th>
                <th>区域の定義・運用仕様</th>
              </tr>
            </thead>
            <tbody>
              ${(ws.forecast_zones || []).map(fz => `
                <tr>
                  <td style="font-weight:700; color:var(--text-primary);">${fz.level_name}</td>
                  <td><b>${fz.scale}</b></td>
                  <td>${fz.description}</td>
                </tr>
              `).join("")}
            </tbody>
          </table>
        </div>
        ${ws.marine_zones ? `
          <div class="guide-info-card" style="margin-top:10px;">
            <div class="guide-info-card-label">海上予報区・沿岸警報区</div>
            <div class="guide-info-card-value">${ws.marine_zones}</div>
          </div>
        ` : ""}
      </div>

      ${ws.observation_network ? `
      <div class="guide-section-block">
        <div class="guide-block-title">🌡️ 地上気象観測網</div>
        <div class="guide-info-grid">
          <div class="guide-info-card">
            <div class="guide-info-card-label">観測ネットワーク名称</div>
            <div class="guide-info-card-value">${ws.observation_network.network_name || "-"}</div>
          </div>
          <div class="guide-info-card">
            <div class="guide-info-card-label">観測所ネットワーク規模</div>
            <div class="guide-info-card-value">${ws.observation_network.stations_scale || "-"}</div>
          </div>
          <div class="guide-info-card" style="grid-column: 1 / -1;">
            <div class="guide-info-card-label">観測要素・配信仕様</div>
            <div class="guide-info-card-value">${ws.observation_network.description || "-"}</div>
          </div>
        </div>
      </div>
      ` : ""}
    `;

    // 3. 交通インフラ体系タブ
    const road = ts.road || {};
    const rail = ts.railway || {};
    let transitHtml = `
      <div class="guide-section-block">
        <div class="guide-block-title">🛣️ 道路網制度</div>
        ${road.summary ? `<div class="guide-text-summary">${road.summary}</div>` : ""}
        <div class="guide-table-wrapper">
          <table class="guide-table">
            <thead>
              <tr>
                <th>分類</th>
                <th>種別名（日本語）</th>
                <th>原語・法的名称</th>
                <th>根拠法律</th>
                <th>管理主体</th>
                <th style="width:110px;">規模</th>
              </tr>
            </thead>
            <tbody>
              ${(road.classifications || []).map(rc => `
                <tr>
                  <td><span class="guide-level-badge" style="background:#475569;">${rc.category}</span></td>
                  <td style="font-weight:700; color:var(--text-primary);">${rc.name_ja}</td>
                  <td>${rc.name_local || "-"}</td>
                  <td>${rc.law || "-"}</td>
                  <td>${rc.manager || "-"}</td>
                  <td><b>${rc.scale || "-"}</b></td>
                </tr>
              `).join("")}
            </tbody>
          </table>
        </div>
        ${road.numbering_rules ? `
          <div class="guide-info-card" style="margin-bottom:10px;">
            <div class="guide-info-card-label">路線ナンバリング規則・付番体系</div>
            <div class="guide-info-card-value">${road.numbering_rules}</div>
          </div>
        ` : ""}
        ${road.management_notes ? `
          <div class="guide-info-card">
            <div class="guide-info-card-label">直轄管理と地方自治体の分担</div>
            <div class="guide-info-card-value">${road.management_notes}</div>
          </div>
        ` : ""}
      </div>

      <div class="guide-section-block">
        <div class="guide-block-title">🚆 鉄軌道・都市交通・索道制度</div>
        ${rail.summary ? `<div class="guide-text-summary">${rail.summary}</div>` : ""}
        <div class="guide-table-wrapper">
          <table class="guide-table">
            <thead>
              <tr>
                <th>大分類</th>
                <th>技術分類（日本語）</th>
                <th>法的種別（原語）</th>
                <th>根拠法律</th>
                <th>運行都市・対象路線例</th>
              </tr>
            </thead>
            <tbody>
              ${(rail.classifications || []).map(rc => `
                <tr>
                  <td><span class="guide-level-badge" style="background:#2563eb;">${rc.category}</span></td>
                  <td style="font-weight:700; color:var(--text-primary);">${rc.name_ja}</td>
                  <td>${rc.name_local || "-"}</td>
                  <td>${rc.law || "-"}</td>
                  <td>${rc.lines_or_cities || "-"}</td>
                </tr>
              `).join("")}
            </tbody>
          </table>
        </div>
        ${rail.special_transit_notes ? `
          <div class="guide-info-card" style="margin-bottom:10px;">
            <div class="guide-info-card-label">索道・モノレール・新交通等の制度的位置づけ</div>
            <div class="guide-info-card-value">${rail.special_transit_notes}</div>
          </div>
        ` : ""}
        ${rail.major_operators && rail.major_operators.length > 0 ? `
          <div class="guide-info-card">
            <div class="guide-info-card-label">主要運行事業者</div>
            <div style="display:flex; flex-direction:column; gap:6px; margin-top:4px;">
              ${rail.major_operators.map(op => `
                <div style="font-size:12px; display:flex; gap:8px; flex-wrap:wrap;">
                  <span style="font-weight:700; color:var(--text-primary); min-width:160px;">${op.name}</span>
                  <span style="color:var(--text-muted); min-width:100px;">[${op.role}]</span>
                  <span style="color:var(--text-secondary);">${op.lines}</span>
                </div>
              `).join("")}
            </div>
          </div>
        ` : ""}
      </div>

      <div class="guide-section-block">
        <div class="guide-block-title">🚌 バス・🚢 航路・✈️ 航空路体系</div>
        <div class="guide-info-grid">
          ${ts.bus && ts.bus.summary ? `
          <div class="guide-info-card">
            <div class="guide-info-card-label">🚌 バス事業制度</div>
            <div class="guide-info-card-value">${ts.bus.summary}</div>
          </div>` : ""}
          ${ts.maritime && ts.maritime.summary ? `
          <div class="guide-info-card">
            <div class="guide-info-card-label">🚢 航路（旅客船・フェリー）</div>
            <div class="guide-info-card-value">${ts.maritime.summary}</div>
          </div>` : ""}
          ${ts.aviation && ts.aviation.summary ? `
          <div class="guide-info-card" style="grid-column: 1 / -1;">
            <div class="guide-info-card-label">✈️ 航空路・空港体系</div>
            <div class="guide-info-card-value">${ts.aviation.summary}</div>
          </div>` : ""}
        </div>
      </div>
    `;



    // 5. 公式ポータル・公的地図タブ
    let portalsHtml = `
      <div class="guide-section-block">
        <div class="guide-block-title">🔗 公式ポータル・公的地図オープンデータ</div>
        <div class="guide-portals-grid">
          ${portals.map(p => `
            <a href="${p.url}" target="_blank" rel="noopener" class="guide-portal-card">
              <div>
                <div class="guide-portal-category">${p.category}</div>
                <div class="guide-portal-name">${p.name}</div>
                ${p.description ? `<div class="guide-portal-desc">${p.description}</div>` : ""}
              </div>
              <div class="guide-portal-link-label">
                <span>公式サイト・データを開く</span>
                <span>↗</span>
              </div>
            </a>
          `).join("")}
        </div>
      </div>
    `;

    return `
      <div class="country-guide-container" id="country-guide-section">
        <div class="guide-header">
          <div class="guide-header-top">
            <div class="guide-header-title">
              <span>📘</span>
              <span>${flag || "🌐"} ${name} 制度・インフラ解説ガイド</span>
              <span class="guide-badge">公式制度準拠</span>
            </div>
            <div style="font-size:12px; color:var(--text-muted);">
              法体系・行政階層・気象観測・交通インフラ公式リファレンス
            </div>
          </div>
          <div class="guide-tabs">
            <button class="guide-tab-btn active" data-tab="basic" onclick="App.switchGuideTab('basic')">🏛️ 基本情報・行政</button>
            <button class="guide-tab-btn" data-tab="weather" onclick="App.switchGuideTab('weather')">🌡️ 気象予報・観測</button>
            <button class="guide-tab-btn" data-tab="transit" onclick="App.switchGuideTab('transit')">🚆 交通インフラ体系</button>
            <button class="guide-tab-btn" data-tab="portals" onclick="App.switchGuideTab('portals')">🔗 公式ポータル・地図</button>
          </div>
        </div>
        <div class="guide-body">
          <!-- ⚠️ 生成AI注記・免責文バナー -->
          <div class="guide-disclaimer-banner">
            ⚠️ 本解説は公的資料および事前調査に基づき生成AIが要約・作成したものであり、実際の制度や運行状況と異なる可能性があります。正確な情報は各公式機関の一次情報をご確認ください。
          </div>
          <div class="guide-tab-pane active" id="guide-pane-basic">${basicHtml}</div>
          <div class="guide-tab-pane" id="guide-pane-weather">${weatherHtml}</div>
          <div class="guide-tab-pane" id="guide-pane-transit">${transitHtml}</div>
          <div class="guide-tab-pane" id="guide-pane-portals">${portalsHtml}</div>
        </div>
      </div>
    `;
  },

  // ガイドタブ切り替え
  switchGuideTab: function (tabKey) {
    document.querySelectorAll(".guide-tab-btn").forEach(btn => {
      btn.classList.toggle("active", btn.getAttribute("data-tab") === tabKey);
    });
    document.querySelectorAll(".guide-tab-pane").forEach(pane => {
      pane.classList.remove("active");
    });
    const target = document.getElementById(`guide-pane-${tabKey}`);
    if (target) target.classList.add("active");
  },
};

// 起動
document.addEventListener("DOMContentLoaded", () => {
  App.init();
});
