let state = loadState();

function refreshSelectors() {
  const buySel = document.getElementById("buy-name");
  const sellSel = document.getElementById("sell-name");
  buySel.innerHTML = "";
  sellSel.innerHTML = "";

  for (const t of sortedAmmoTypes(state)) {
    const op = document.createElement("option");
    op.value = t.name;
    op.textContent = `${t.name} (Lv.${t.level})`;
    buySel.appendChild(op);
  }

  for (const row of groupedData(state).filter((x) => x.inventory > 0)) {
    const op = document.createElement("option");
    op.value = row.name;
    op.textContent = `${row.name} (库存 ${row.inventory})`;
    sellSel.appendChild(op);
  }
}

function refreshSummaryAndCards() {
  const groups = groupedData(state);
  const totalProfit = groups.reduce((s, x) => s + x.realizedProfit, 0);
  const totalInventoryCost = groups.reduce((s, x) => s + x.inventoryCost, 0);
  const totalInventory = groups.reduce((s, x) => s + Math.max(0, x.inventory), 0);

  document.getElementById("sum-profit").textContent = fmtNum(totalProfit);
  document.getElementById("sum-inventory-cost").textContent = fmtNum(totalInventoryCost);
  document.getElementById("sum-inventory").textContent = String(totalInventory);

  const holdings = document.getElementById("holdings");
  holdings.innerHTML = "";
  for (const g of groups.filter((x) => x.inventory > 0)) {
    const card = document.createElement("article");
    card.className = "card";
    card.innerHTML = `
      <div class="title">
        <strong class="${levelClass(g.level)}">${g.name} (Lv.${g.level})</strong>
        <span class="tag">${g.tag}</span>
      </div>
      <div class="kv"><span class="k">平均买入</span><span>${fmtNum(g.avgBuy)}</span></div>
      <div class="kv"><span class="k">回本价</span><span>${fmtNum(g.breakEven)}</span></div>
      <div class="kv"><span class="k">库存</span><span>${g.inventory}</span></div>
      <div class="kv"><span class="k">平均卖出</span><span>${fmtNum(g.avgSell)}</span></div>
      <div class="kv"><span class="k">收益</span><span>${fmtNum(g.realizedProfit)}</span></div>
      <div class="kv"><span class="k">库存花费</span><span>${fmtNum(g.inventoryCost)}</span></div>
    `;
    holdings.appendChild(card);
  }
}

function render() {
  refreshSelectors();
  refreshSummaryAndCards();
}

document.getElementById("buy-form").addEventListener("submit", (e) => {
  e.preventDefault();
  const ammoName = document.getElementById("buy-name").value;
  const unitPrice = Number(document.getElementById("buy-price").value);
  const quantity = Number(document.getElementById("buy-qty").value);
  const t = typeMap(state).get(ammoName);
  if (!t) return setMsg("名称不存在，请先新增类型", true);
  if (quantity <= 0 || unitPrice < 0) return setMsg("买入参数不合法", true);

  state.buyRecords.push({
    recordId: crypto.randomUUID(),
    ammoName,
    level: t.level,
    quantity,
    unitPrice,
    createdAt: nowStr()
  });
  saveState(state);
  render();
  e.target.reset();
  setMsg(`买入成功：${ammoName} x${quantity}`);
});

document.getElementById("sell-form").addEventListener("submit", (e) => {
  e.preventDefault();
  const ammoName = document.getElementById("sell-name").value;
  const unitPrice = Number(document.getElementById("sell-price").value);
  let quantity = Number(document.getElementById("sell-qty").value);
  if (!ammoName) return setMsg("当前没有可卖出的库存", true);
  if (quantity <= 0 || unitPrice < 0) return setMsg("卖出参数不合法", true);

  const t = typeMap(state).get(ammoName);
  if (!t) return setMsg("名称不存在", true);
  const g = groupedData(state).find((x) => x.name === ammoName);
  const inv = g ? g.inventory : 0;
  if (inv <= 0) return setMsg("库存为 0，无法卖出", true);
  quantity = Math.min(quantity, inv);

  state.sellRecords.push({
    recordId: crypto.randomUUID(),
    ammoName,
    level: t.level,
    quantity,
    unitPrice,
    total: quantity * unitPrice,
    createdAt: nowStr()
  });
  saveState(state);
  render();
  e.target.reset();
  setMsg(`卖出成功：${ammoName} x${quantity}`);
});

document.body.insertAdjacentHTML("afterbegin", headerTemplate("子弹倒卖助手（主页）"));
bindImportExport(state, (s) => {
  state = s;
  render();
});
render();
