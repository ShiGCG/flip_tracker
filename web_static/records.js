let state = loadState();

function renderRecords() {
  const tbody = document.querySelector("#records-table tbody");
  tbody.innerHTML = "";
  for (const r of allRecords(state)) {
    const tr = document.createElement("tr");
    tr.innerHTML = `
      <td>${r.time}</td>
      <td>${r.actionText}</td>
      <td class="${levelClass(r.level)}">${r.ammoName}</td>
      <td>${r.level}</td>
      <td class="num">${r.quantity}</td>
      <td class="num">${fmtNum(r.unitPrice)}</td>
      <td class="num">${fmtNum(r.total)}</td>
    `;
    tbody.appendChild(tr);
  }
}

document.body.insertAdjacentHTML("afterbegin", headerTemplate("买卖记录管理"));
bindImportExport(state, (s) => {
  state = s;
  renderRecords();
});
renderRecords();
