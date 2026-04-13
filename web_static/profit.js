let state = loadState();

function renderProfit() {
  const groups = groupedData(state);
  const totalProfit = groups.reduce((s, x) => s + x.realizedProfit, 0);
  document.getElementById("sum-profit").textContent = fmtNum(totalProfit);

  const tbody = document.querySelector("#profit-table tbody");
  tbody.innerHTML = "";
  for (const g of groups) {
    const tr = document.createElement("tr");
    tr.innerHTML = `
      <td class="${levelClass(g.level)}">${g.name}</td>
      <td>${g.level}</td>
      <td>${g.tag}</td>
      <td class="num">${g.inventory}</td>
      <td class="num">${fmtNum(g.avgBuy)}</td>
      <td class="num">${fmtNum(g.avgSell)}</td>
      <td class="num">${fmtNum(g.realizedProfit)}</td>
    `;
    tbody.appendChild(tr);
  }
}

document.body.insertAdjacentHTML("afterbegin", headerTemplate("收益统计"));
bindImportExport(state, (s) => {
  state = s;
  renderProfit();
});
renderProfit();
