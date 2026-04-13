let state = loadState();

function refreshTypeList() {
  const box = document.getElementById("type-list");
  box.innerHTML = "";
  for (const t of sortedAmmoTypes(state)) {
    const row = document.createElement("div");
    row.className = "type-row";
    row.innerHTML = `
      <strong class="${levelClass(t.level)}">${t.name}</strong>
      <span class="meta">Lv.${t.level}</span>
      <span class="meta">${t.tag}</span>
      <span class="meta">${fmtNum(t.breakEvenRatio)}</span>
      <button class="btn" data-del="${t.name}">删除</button>
    `;
    row.querySelector("button").addEventListener("click", () => {
      const hasRecord = state.buyRecords.some((r) => r.ammoName === t.name) || state.sellRecords.some((r) => r.ammoName === t.name);
      if (hasRecord) return setMsg("该名称已有交易记录，不能删除", true);
      state.ammoTypes = state.ammoTypes.filter((x) => x.name !== t.name);
      saveState(state);
      refreshTypeList();
      setMsg(`已删除类型：${t.name}`);
    });
    box.appendChild(row);
  }
}

document.getElementById("type-form").addEventListener("submit", (e) => {
  e.preventDefault();
  const name = document.getElementById("type-name").value.trim();
  const level = Number(document.getElementById("type-level").value);
  const ratio = Number(document.getElementById("type-ratio").value);
  const tag = document.getElementById("type-tag").value;
  if (!name) return setMsg("名称不能为空", true);
  if (level <= 0) return setMsg("等级必须大于 0", true);
  if (!(ratio > 0 && ratio <= 1)) return setMsg("回本系数必须在 0 到 1 之间", true);
  if (!VALID_TAGS.includes(tag)) return setMsg("标签不合法", true);

  const old = state.ammoTypes.find((x) => x.name === name);
  if (old) {
    const hasRecords = state.buyRecords.some((r) => r.ammoName === name) || state.sellRecords.some((r) => r.ammoName === name);
    if (hasRecords && old.level !== level) return setMsg("该名称已有交易记录，不能修改等级", true);
    old.level = level;
    old.breakEvenRatio = ratio;
    old.tag = tag;
    setMsg(`已更新类型：${name}`);
  } else {
    state.ammoTypes.push({ name, level, breakEvenRatio: ratio, tag });
    setMsg(`已新增类型：${name}`);
  }
  saveState(state);
  refreshTypeList();
  e.target.reset();
});

document.body.insertAdjacentHTML("afterbegin", headerTemplate("子弹类型管理"));
bindImportExport(state, (s) => {
  state = s;
  refreshTypeList();
});
refreshTypeList();
