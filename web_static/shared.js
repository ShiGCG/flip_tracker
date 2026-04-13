const STORAGE_KEY = "flipTrackerWeb.v1";
const TAG_PRIORITY = { "日抛": 0, "周抛": 1, "长期": 2, "赛季": 3 };
const VALID_TAGS = ["日抛", "周抛", "长期", "赛季"];

const DEFAULT_STATE = {
  ammoTypes: [
    { name: "7.62 BP", level: 4, breakEvenRatio: 0.87, tag: "长期" },
    { name: "5.45 PS", level: 2, breakEvenRatio: 0.87, tag: "长期" },
    { name: "9mm FMJ", level: 1, breakEvenRatio: 0.87, tag: "长期" }
  ],
  buyRecords: [],
  sellRecords: []
};

function deepClone(x) {
  return JSON.parse(JSON.stringify(x));
}

function loadState() {
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    if (!raw) return deepClone(DEFAULT_STATE);
    const parsed = JSON.parse(raw);
    parsed.ammoTypes ??= [];
    parsed.buyRecords ??= [];
    parsed.sellRecords ??= [];
    return parsed;
  } catch {
    return deepClone(DEFAULT_STATE);
  }
}

function saveState(state) {
  localStorage.setItem(STORAGE_KEY, JSON.stringify(state));
}

function nowStr() {
  const d = new Date();
  const p = (n) => String(n).padStart(2, "0");
  return `${d.getFullYear()}-${p(d.getMonth() + 1)}-${p(d.getDate())} ${p(d.getHours())}:${p(d.getMinutes())}:${p(d.getSeconds())}`;
}

function fmtNum(v) {
  if (!Number.isFinite(v)) return "0";
  return String(Math.round(v * 10000) / 10000);
}

function levelClass(level) {
  return `lv${Math.max(1, Math.min(5, Number(level) || 1))}`;
}

function typeMap(state) {
  const m = new Map();
  for (const t of state.ammoTypes) m.set(t.name, t);
  return m;
}

function sortedAmmoTypes(state) {
  return [...state.ammoTypes].sort((a, b) => {
    if (b.level !== a.level) return b.level - a.level;
    return a.name.localeCompare(b.name, "zh-CN");
  });
}

function groupedData(state) {
  const tMap = typeMap(state);
  const byName = new Map();

  for (const r of state.buyRecords) {
    const arr = byName.get(r.ammoName) || [];
    arr.push(r);
    byName.set(r.ammoName, arr);
  }

  const list = [];
  for (const [name, rows] of byName.entries()) {
    const type = tMap.get(name);
    if (!type) continue;

    const totalQty = rows.reduce((s, r) => s + r.quantity, 0);
    const totalCost = rows.reduce((s, r) => s + r.quantity * r.unitPrice, 0);
    const avgBuy = totalQty > 0 ? totalCost / totalQty : 0;
    const ratio = type.breakEvenRatio > 0 ? type.breakEvenRatio : 0.87;
    const breakEven = Math.ceil(avgBuy / ratio);
    const sells = state.sellRecords.filter((s) => s.ammoName === name);
    const soldQty = sells.reduce((s, r) => s + r.quantity, 0);
    const soldTotal = sells.reduce((s, r) => s + r.total, 0);
    const avgSell = soldQty > 0 ? soldTotal / soldQty : 0;
    const inventory = totalQty - soldQty;
    const realizedProfit = soldTotal - soldQty * breakEven;
    const inventoryCost = Math.max(0, inventory) * avgBuy;
    const latestBuy = rows.reduce((max, r) => Math.max(max, Date.parse(r.createdAt) || 0), 0);

    list.push({
      name,
      level: type.level,
      tag: type.tag || "长期",
      avgBuy,
      breakEven,
      soldQty,
      avgSell,
      inventory,
      realizedProfit,
      inventoryCost,
      latestBuy
    });
  }

  list.sort((a, b) => {
    const ta = TAG_PRIORITY[a.tag] ?? 99;
    const tb = TAG_PRIORITY[b.tag] ?? 99;
    if (ta !== tb) return ta - tb;
    if (b.latestBuy !== a.latestBuy) return b.latestBuy - a.latestBuy;
    return a.name.localeCompare(b.name, "zh-CN");
  });
  return list;
}

function allRecords(state) {
  const rows = [];
  for (const b of state.buyRecords) {
    rows.push({
      recordId: b.recordId,
      action: "buy",
      actionText: "买入",
      time: b.createdAt,
      ammoName: b.ammoName,
      level: b.level,
      quantity: b.quantity,
      unitPrice: b.unitPrice,
      total: b.quantity * b.unitPrice
    });
  }
  for (const s of state.sellRecords) {
    rows.push({
      recordId: s.recordId,
      action: "sell",
      actionText: "卖出",
      time: s.createdAt,
      ammoName: s.ammoName,
      level: s.level,
      quantity: s.quantity,
      unitPrice: s.unitPrice,
      total: s.total
    });
  }
  rows.sort((a, b) => (Date.parse(b.time) || 0) - (Date.parse(a.time) || 0));
  return rows;
}

function headerTemplate(title) {
  return `
    <header class="topbar">
      <div>
        <h1>${title}</h1>
        <p>离线可用，数据保存在浏览器本地（localStorage）</p>
      </div>
      <div class="topbar-actions">
        <button id="export-btn" class="btn">导出数据</button>
        <label class="btn btn-file">
          导入数据
          <input id="import-input" type="file" accept="application/json">
        </label>
      </div>
    </header>
    <nav class="nav">
      <a href="./index.html">主页</a>
      <a href="./types.html">子弹类型管理</a>
      <a href="./records.html">买卖记录管理</a>
      <a href="./profit.html">收益统计</a>
    </nav>
    <p id="msg" class="msg"></p>
  `;
}

function bindImportExport(state, onImported) {
  const exportBtn = document.getElementById("export-btn");
  if (exportBtn) {
    exportBtn.addEventListener("click", () => {
      const blob = new Blob([JSON.stringify(state, null, 2)], { type: "application/json;charset=utf-8" });
      const a = document.createElement("a");
      a.href = URL.createObjectURL(blob);
      a.download = `flip-tracker-web-${Date.now()}.json`;
      a.click();
      URL.revokeObjectURL(a.href);
      setMsg("已导出数据");
    });
  }

  const importInput = document.getElementById("import-input");
  if (importInput) {
    importInput.addEventListener("change", async (e) => {
      const f = e.target.files?.[0];
      if (!f) return;
      try {
        const text = await f.text();
        const obj = JSON.parse(text);
        if (!obj || !Array.isArray(obj.ammoTypes) || !Array.isArray(obj.buyRecords) || !Array.isArray(obj.sellRecords)) {
          return setMsg("导入失败：格式不正确", true);
        }
        saveState(obj);
        setMsg("导入成功");
        onImported(obj);
      } catch {
        setMsg("导入失败：无法解析 JSON", true);
      } finally {
        e.target.value = "";
      }
    });
  }
}

function setMsg(text, danger = false) {
  const el = document.getElementById("msg");
  if (!el) return;
  el.textContent = text;
  el.classList.toggle("danger", danger);
}
