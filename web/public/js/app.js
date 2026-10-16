/**
 * 世界交通網・地域データ基盤 公開Webサイト
 * メインアプリケーション制御スクリプト
 */

const App = {
  summaryData: null,
  activeCountryCode: "JP",
  countryDataCache: {},
  currentCountryData: null,
  activeTab: "routes",
  searchQuery: "",

  init: async function () {
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
    // テーマ切替ボタン
    document.getElementById("theme-toggle-btn").addEventListener("click", () => this.toggleTheme());

    // 検索入力
    const searchInput = document.getElementById("search-input");
    const clearBtn = document.getElementById("search-clear-btn");

    searchInput.addEventListener("input", (e) => {
      this.searchQuery = e.target.value.trim().toLowerCase();
      clearBtn.style.display = this.searchQuery ? "block" : "none";
      this.renderCurrentTab();
    });

    clearBtn.addEventListener("click", () => {
      searchInput.value = "";
      this.searchQuery = "";
      clearBtn.style.display = "none";
      this.renderCurrentTab();
    });

    // タブ切替
    document.querySelectorAll(".tab-btn").forEach((btn) => {
      btn.addEventListener("click", (e) => {
        const tabKey = btn.getAttribute("data-tab");
        this.switchTab(tabKey);
      });
    });

    // 地図リセットボタン
    document.getElementById("map-reset-btn").addEventListener("click", () => {
      PublicMap.resetView();
    });
  },

  // サマリーデータ取得
  loadSummary: async function () {
    try {
      const res = await fetch("data/summary.json");
      if (!res.ok) throw new Error("summary.json の読み込みに失敗しました");
      this.summaryData = await res.json();
      this.renderHeaderStats();
      this.renderCountrySelector();
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
  },

  // 国セレクター描画
  renderCountrySelector: function () {
    const container = document.getElementById("country-selector-container");
    container.innerHTML = "";

    // データが存在する国を優先配置
    const countries = this.summaryData.countries || [];
    
    // 主要国（JP, AT）を先頭に、データ件数が多い順でソート
    countries.sort((a, b) => {
      if (a.code === "JP") return -1;
      if (b.code === "JP") return 1;
      if (a.code === "AT") return -1;
      if (b.code === "AT") return 1;
      return (b.counts.routes + b.counts.nodes) - (a.counts.routes + a.counts.nodes);
    });

    // 上位15カ国程度をピルとして表示
    const topCountries = countries.slice(0, 15);

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

    // ピルのアクティブ表示を更新
    document.querySelectorAll(".country-pill").forEach((pill) => {
      pill.classList.toggle("active", pill.getAttribute("data-cc") === countryCode);
    });

    const contentEl = document.getElementById("tab-content");
    contentEl.innerHTML = `
      <div class="loading-box">
        <div class="spinner"></div>
        <div>${countryCode} のデータを読み込み中...</div>
      </div>
    `;

    // キャッシュまたは新規フェッチ
    if (this.countryDataCache[countryCode]) {
      this.currentCountryData = this.countryDataCache[countryCode];
    } else {
      try {
        const res = await fetch(`data/${countryCode.toLowerCase()}.json`);
        if (!res.ok) throw new Error(`${countryCode}.json が見つかりません`);
        this.currentCountryData = await res.json();
        this.countryDataCache[countryCode] = this.currentCountryData;
      } catch (err) {
        console.error(err);
        contentEl.innerHTML = `
          <div class="empty-box">
            ⚠️ 選択された国 (${countryCode}) のデータは現在準備中です。
          </div>
        `;
        return;
      }
    }

    // 地図の視点を国の中心へ移動
    PublicMap.setCountryView(this.currentCountryData.map_meta);

    // タブの件数バッジを更新
    this.updateTabCounts();

    // 現在のタブを描画
    this.renderCurrentTab();
  },

  // タブの件数バッジ更新
  updateTabCounts: function () {
    if (!this.currentCountryData) return;
    const c = this.currentCountryData.counts;
    document.getElementById("tab-count-routes").innerText = c.routes.toLocaleString();
    document.getElementById("tab-count-muni").innerText = c.municipalities.toLocaleString();
    document.getElementById("tab-count-nodes").innerText = c.nodes.toLocaleString();
  },

  // タブの切り替え
  switchTab: function (tabKey) {
    this.activeTab = tabKey;
    document.querySelectorAll(".tab-btn").forEach((btn) => {
      btn.classList.toggle("active", btn.getAttribute("data-tab") === tabKey);
    });
    this.renderCurrentTab();
  },

  // 現在のタブの内容を描画
  renderCurrentTab: function () {
    if (!this.currentCountryData) return;

    if (this.activeTab === "routes") {
      this.renderRoutesTab();
    } else if (this.activeTab === "muni") {
      this.renderMuniTab();
    } else if (this.activeTab === "nodes") {
      this.renderNodesTab();
    }
  },

  // 1. 路線・交通タブ
  renderRoutesTab: function () {
    const container = document.getElementById("tab-content");
    let routes = this.currentCountryData.routes || [];

    // 検索フィルタ
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
      container.innerHTML = `<div class="empty-box">該当する路線は見つかりませんでした。</div>`;
      return;
    }

    let html = "";
    // 上位50件を表示（パフォーマンス保護）
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
            ${hasSeq ? '<span class="seq-role junction" style="font-size:11px;">駅順序データあり 🔗</span>' : ""}
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

    // 路線カードのクリックイベント（アコーディオン展開）
    container.querySelectorAll(".route-card").forEach((card) => {
      card.addEventListener("click", (e) => {
        // 地図ボタン等のクリックは伝播させない
        if (e.target.closest(".btn-show-map")) return;

        const rid = card.getAttribute("data-rid");
        this.toggleRouteSequence(rid, card);
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

    // 他のカードを閉じる
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
          ${node.lat ? '<button class="btn-show-map" title="地図で見る">📍</button>' : ""}
        </div>
      `;
    });

    seqHtml += `</div>`;
    seqContainer.innerHTML = seqHtml;

    // 「地図上に全駅を結んで表示」ボタン
    document.getElementById(`btn-plot-all-${routeId}`).addEventListener("click", (e) => {
      e.stopPropagation();
      PublicMap.plotSequence(seqNodes);
    });

    // 個別駅クリックでズーム
    seqContainer.querySelectorAll(".seq-item").forEach((item) => {
      item.addEventListener("click", (e) => {
        e.stopPropagation();
        const lat = parseFloat(item.getAttribute("data-lat"));
        const lon = parseFloat(item.getAttribute("data-lon"));
        const name = item.querySelector(".seq-name").innerText;
        if (!isNaN(lat) && !isNaN(lon)) {
          PublicMap.flyToLocation(lat, lon, 15, `<b>${name}</b><br>経度: ${lat}, 緯度: ${lon}`);
        }
      });
    });

    // デフォルトで全駅シーケンスを地図にプロット
    PublicMap.plotSequence(seqNodes);
  },

  // 2. 行政区画・自治体タブ
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
      container.innerHTML = `<div class="empty-box">該当する自治体は見つかりませんでした。</div>`;
      return;
    }

    let html = "";
    const displayMunis = munis.slice(0, 100);

    displayMunis.forEach((m) => {
      html += `
        <div class="data-list-item" data-lat="${m.lat}" data-lon="${m.lon}">
          <div class="item-main">
            <div class="item-name">
              <span>${m.name}</span>
              ${m.name_official ? `<span class="item-sub">(${m.name_official})</span>` : ""}
              <span class="item-badge">${m.category || "行政区域"}</span>
            </div>
            <div class="item-sub">
              ${m.code ? `コード: ${m.code}` : ""}
              ${m.lat ? ` | 政庁座標: [${m.lat}, ${m.lon}]` : ""}
            </div>
          </div>
          ${m.lat ? '<button class="btn-icon" style="padding:4px 8px; font-size:12px;">📍 地図へ</button>' : ""}
        </div>
      `;
    });

    if (munis.length > 100) {
      html += `<div style="text-align:center; padding:12px; font-size:12px; color:var(--text-muted);">
        全 ${munis.length} 件中 100 件を表示しています。
      </div>`;
    }

    container.innerHTML = html;

    // クリックで地図ジャンプ
    container.querySelectorAll(".data-list-item").forEach((item) => {
      item.addEventListener("click", () => {
        const lat = parseFloat(item.getAttribute("data-lat"));
        const lon = parseFloat(item.getAttribute("data-lon"));
        const name = item.querySelector(".item-name span").innerText;
        if (!isNaN(lat) && !isNaN(lon)) {
          PublicMap.flyToLocation(lat, lon, 12, `<b>${name} (政庁)</b>`);
        }
      });
    });
  },

  // 3. 拠点（駅・IC・空港・港湾）タブ
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
      container.innerHTML = `<div class="empty-box">該当する拠点は見つかりませんでした。</div>`;
      return;
    }

    // 地図上にもこれらの拠点をプロット
    PublicMap.plotNodes(nodes, 400);

    let html = "";
    const displayNodes = nodes.slice(0, 100);

    displayNodes.forEach((n) => {
      html += `
        <div class="data-list-item" data-lat="${n.lat}" data-lon="${n.lon}">
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
            ${n.lat ? '<button class="btn-icon" style="padding:4px 8px; font-size:12px;">📍 ズーム</button>' : ""}
            <a href="https://www.google.com/maps/search/?api=1&query=${n.lat},${n.lon}" target="_blank" rel="noopener" class="btn-icon" style="padding:4px 8px; font-size:12px; text-decoration:none;" onclick="event.stopPropagation();">
              🔗 Google
            </a>
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

    // クリックで地図ジャンプ
    container.querySelectorAll(".data-list-item").forEach((item) => {
      item.addEventListener("click", () => {
        const lat = parseFloat(item.getAttribute("data-lat"));
        const lon = parseFloat(item.getAttribute("data-lon"));
        const name = item.querySelector(".item-name span").innerText;
        if (!isNaN(lat) && !isNaN(lon)) {
          PublicMap.flyToLocation(lat, lon, 15, `<b>${name}</b>`);
        }
      });
    });
  },
};

// ページロード時に起動
window.addEventListener("DOMContentLoaded", () => {
  App.init();
});
