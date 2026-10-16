/**
 * 探索ログ記録 & SNS下書きモジュール (records.js)
 */

let appRoutes = [];
let appNodes = [];
let appMunicipalities = [];
let appLogs = [];

function initRecordPanel() {
  const panel = document.getElementById("record-panel");
  const toggleBtn = document.getElementById("btn-toggle-record");
  const closeBtn = document.getElementById("btn-close-record");

  toggleBtn.addEventListener("click", () => {
    panel.classList.toggle("open");
    toggleBtn.classList.toggle("active");
  });

  closeBtn.addEventListener("click", () => {
    panel.classList.remove("open");
    toggleBtn.classList.remove("active");
  });

  // タブ切替
  const tabs = document.querySelectorAll(".panel-tab");
  tabs.forEach(tab => {
    tab.addEventListener("click", (e) => {
      tabs.forEach(t => t.classList.remove("active"));
      document.querySelectorAll(".tab-content").forEach(c => c.style.display = "none");

      const targetId = e.target.getAttribute("data-target");
      e.target.classList.add("active");
      document.getElementById(targetId).style.display = "block";

      if (targetId === "tab-logs") {
        renderLogsList();
      } else if (targetId === "tab-sns") {
        updateSnsDrafts();
      }
    });
  });

  // 初期データ読み込み
  loadMasterOptions("JP");

  // 国変更リスナー
  document.getElementById("log-country").addEventListener("change", (e) => {
    loadMasterOptions(e.target.value);
  });

  // フォーム送信
  const form = document.getElementById("exploration-form");
  form.addEventListener("submit", async (e) => {
    e.preventDefault();
    await handleFormSubmit();
  });

  // コピー用ボタン
  document.getElementById("btn-copy-x").addEventListener("click", () => {
    const text = document.getElementById("draft-x").value;
    navigator.clipboard.writeText(text);
    showToast("X用下書きをコピーしました！");
  });

  document.getElementById("btn-copy-note").addEventListener("click", () => {
    const text = document.getElementById("draft-note").value;
    navigator.clipboard.writeText(text);
    showToast("note用下書きをコピーしました！");
  });

  // フォーム入力時の下書きリアルタイム連動
  document.getElementById("log-title").addEventListener("input", updateSnsDrafts);
  document.getElementById("log-memo").addEventListener("input", updateSnsDrafts);
  document.getElementById("log-tags").addEventListener("input", updateSnsDrafts);
}

async function loadMasterOptions(countryCode) {
  try {
    const [rData, nData, mData, lData] = await Promise.all([
      apiFetchRoutes(countryCode),
      apiFetchNodes(countryCode, 41.7737, 140.7264, 50),
      apiFetchMunicipalities(countryCode),
      apiFetchLogs()
    ]);
    appRoutes = rData.routes || [];
    appNodes = nData.nodes || [];
    appMunicipalities = mData.municipalities || [];
    appLogs = lData.logs || [];

    // バッジ更新
    document.getElementById("badge-points").innerText = `${appNodes.length} 拠点(周辺)`;
    document.getElementById("badge-routes").innerText = `${appRoutes.length} ルート`;

    // セレクトボックスへの流し込み
    const selRoute = document.getElementById("log-route");
    selRoute.innerHTML = '<option value="">(未選択)</option>';
    appRoutes.slice(0, 300).forEach(r => {
      const name = r["日本語名"] || r["公用語名"];
      selRoute.innerHTML += `<option value="${r["route_id"]}">${name} (${r["route_id"]})</option>`;
    });

    const selNode = document.getElementById("log-node");
    selNode.innerHTML = '<option value="">(未選択)</option>';
    appNodes.forEach(n => {
      const name = n["日本語名"] || n["公用語名"];
      selNode.innerHTML += `<option value="${n["node_id"]}">${name} (${n["種別"]})</option>`;
    });

    const selMun = document.getElementById("log-municipality");
    selMun.innerHTML = '<option value="">(未選択)</option>';
    appMunicipalities.slice(0, 200).forEach(m => {
      const name = m["日本語名"] || m["公用語名"];
      selMun.innerHTML += `<option value="${m["municipality_id_tmp"]}">${name}</option>`;
    });

    renderLogsList();
  } catch (err) {
    console.error("Failed to load options", err);
  }
}

function setClickedCoordinate(lat, lon) {
  const roundedLat = lat.toFixed(6);
  const roundedLon = lon.toFixed(6);
  const input = document.getElementById("log-coords");
  if (input) {
    input.value = `${roundedLat}, ${roundedLon}`;
  }
  const ind = document.getElementById("coord-display");
  if (ind) {
    ind.innerText = `[選択座標: ${roundedLat}, ${roundedLon}]`;
  }
  updateSnsDrafts();
}

async function handleFormSubmit() {
  const cc = document.getElementById("log-country").value;
  const title = document.getElementById("log-title").value.trim();
  const routeId = document.getElementById("log-route").value;
  const nodeId = document.getElementById("log-node").value;
  const munId = document.getElementById("log-municipality").value;
  const coords = document.getElementById("log-coords").value.trim();
  const tags = document.getElementById("log-tags").value.trim();
  const memo = document.getElementById("log-memo").value.trim();
  const url = document.getElementById("log-url").value.trim();

  if (!title) {
    alert("タイトルを入力してください。");
    return;
  }

  let lat = "", lon = "";
  if (coords.includes(",")) {
    const parts = coords.split(",");
    lat = parts[0].trim();
    lon = parts[1].trim();
  }

  const payload = {
    country_code: cc,
    タイトル: title,
    対象路線_ids: routeId,
    対象拠点_ids: nodeId,
    対象自治体_ids: munId,
    緯度: lat,
    経度: lon,
    タグ: tags,
    本文: memo,
    Webリンク: url,
    公開ステータス: "記録中"
  };

  try {
    const res = await apiSaveLog(payload);
    if (res.success) {
      showToast(`探索ログを保存しました (${res.log.log_id})`);
      document.getElementById("log-title").value = "";
      document.getElementById("log-memo").value = "";
      // ログ一覧を再読み込み
      const lData = await apiFetchLogs();
      appLogs = lData.logs || [];
      renderLogsList();
    }
  } catch (err) {
    alert("保存に失敗しました: " + err.message);
  }
}

function updateSnsDrafts() {
  const title = document.getElementById("log-title").value.trim() || "探索ログ";
  const memo = document.getElementById("log-memo").value.trim();
  const tags = document.getElementById("log-tags").value.trim();
  const coords = document.getElementById("log-coords").value.trim();
  const url = document.getElementById("log-url").value.trim();

  // X用
  const tagList = tags.split(",").map(t => t.trim()).filter(t => t).map(t => `#${t}`).join(" ");
  const memoSnippet = memo.length > 80 ? memo.substring(0, 80) + "..." : memo;
  const xText = `【机上探索: ${title}】\n${memoSnippet}\n${tagList}`;
  document.getElementById("draft-x").value = xText;

  // note用
  const noteText = `# ${title}\n\n## 探索概要\n- 座標: ${coords}\n- タグ: ${tags}\n\n## 沿線記録と考察\n${memo}\n\n---\n*参考: ${url}*`;
  document.getElementById("draft-note").value = noteText;
}

function renderLogsList() {
  const listEl = document.getElementById("logs-list-container");
  if (!listEl) return;
  if (!appLogs || appLogs.length === 0) {
    listEl.innerHTML = '<p style="color:var(--text-sub); font-size:12px;">探索ログはまだありません。</p>';
    return;
  }

  listEl.innerHTML = appLogs.slice().reverse().map(l => {
    return `
      <div class="log-card" style="border:1px solid var(--border-color); background:var(--bg-toolbar); padding:8px; border-radius:6px; margin-bottom:8px; font-size:12px;">
        <div style="display:flex; justify-content:space-between; margin-bottom:4px;">
          <strong style="color:var(--primary-color);">${l["log_id"]}</strong>
          <span style="color:var(--text-sub); font-size:10px;">${l["探索日"]}</span>
        </div>
        <div style="font-weight:600; margin-bottom:4px;">${l["タイトル"]}</div>
        <div style="color:var(--text-sub); font-size:11px; margin-bottom:6px;">${l["本文"] ? l["本文"].substring(0, 60) + '...' : ''}</div>
        ${l["緯度"] && l["経度"] ? `<button onclick="jumpToCoord(${l["緯度"]}, ${l["経度"]})" style="background:none; border:1px solid var(--border-color); color:var(--text-main); padding:2px 6px; border-radius:4px; font-size:10px; cursor:pointer;">📍 地図で見る</button>` : ''}
      </div>
    `;
  }).join("");
}

function showToast(message) {
  const toast = document.getElementById("toast");
  toast.innerText = message;
  toast.classList.add("show");
  setTimeout(() => {
    toast.classList.remove("show");
  }, 3000);
}
