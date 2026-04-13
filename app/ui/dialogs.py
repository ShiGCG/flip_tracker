from __future__ import annotations

import tkinter as tk
from tkinter import ttk, messagebox
from typing import Callable

from .theme import Theme
from ..services import LedgerService


def open_settings_dialog(
    root: tk.Tk,
    service: LedgerService,
    level_color_fn: Callable[[int], str],
    on_after_save: Callable[[], None],
    name_var: tk.StringVar,
    name_combo: ttk.Combobox,
) -> None:
    win = tk.Toplevel(root)
    win.title("设置 - 子弹类型管理")
    win.geometry("700x500")
    win.configure(bg=Theme.BG)

    frame = ttk.Frame(win, style="Main.TFrame")
    frame.pack(fill="both", expand=True, padx=12, pady=12)

    form = ttk.LabelFrame(frame, text="新增 / 更新类型", style="Card.TLabelframe")
    form.pack(fill="x")
    local_name_var = tk.StringVar()
    level_var = tk.StringVar()
    ratio_var = tk.StringVar(value="0.8700")
    tag_var = tk.StringVar(value="长期")
    tag_options = ("日抛", "周抛", "长期", "赛季")
    row = ttk.Frame(form, style="Card.TFrame")
    row.pack(fill="x", padx=10, pady=10)
    ttk.Label(row, text="名称", style="CardLabel.TLabel").pack(side="left")
    ttk.Entry(row, textvariable=local_name_var,
              width=20).pack(side="left", padx=(6, 10))
    ttk.Label(row, text="等级", style="CardLabel.TLabel").pack(side="left")
    ttk.Entry(row, textvariable=level_var, width=8).pack(
        side="left", padx=(6, 10))
    ttk.Label(row, text="回本系数", style="CardLabel.TLabel").pack(side="left")
    ttk.Entry(row, textvariable=ratio_var, width=10).pack(
        side="left", padx=(6, 10))
    ttk.Label(row, text="标签", style="CardLabel.TLabel").pack(side="left")
    ttk.Combobox(row, textvariable=tag_var, values=tag_options, width=8, state="readonly").pack(
        side="left", padx=(6, 10)
    )

    table_card = ttk.LabelFrame(frame, text="现有类型", style="Card.TLabelframe")
    table_card.pack(fill="both", expand=True, pady=(10, 0))
    table = ttk.Treeview(
        table_card, columns=("name", "level", "tag", "ratio", "status"), show="headings", height=14
    )
    table.heading("name", text="名称")
    table.heading("level", text="等级")
    table.heading("tag", text="标签")
    table.heading("ratio", text="回本系数")
    table.heading("status", text="状态")
    table.column("name", width=180, anchor="w")
    table.column("level", width=70, anchor="center")
    table.column("tag", width=80, anchor="center")
    table.column("ratio", width=100, anchor="center")
    table.column("status", width=140, anchor="center")
    table.tag_configure("lv1", foreground=level_color_fn(1))
    table.tag_configure("lv2", foreground=level_color_fn(2))
    table.tag_configure("lv3", foreground=level_color_fn(3))
    table.tag_configure("lv4", foreground=level_color_fn(4))
    table.tag_configure("lv5", foreground=level_color_fn(5))
    table.pack(fill="both", expand=True, padx=10, pady=10)

    def refresh_table() -> None:
        for item in table.get_children():
            table.delete(item)
        for r in service.ammo_type_rows():
            status = "有交易记录" if r["has_records"] else "可删除"
            tag = f"lv{int(r['level'])}"
            table.insert(
                "",
                "end",
                values=(r["name"], r["level"], r.get("tag", "长期"),
                        f"{float(r['break_even_ratio']):.4f}", status),
                tags=(tag,),
            )
        name_combo["values"] = service.ammo_names()
        if name_var.get() not in service.ammo_names():
            names = service.ammo_names()
            name_var.set(names[0] if names else "")

    def on_save() -> None:
        try:
            service.set_ammo_type(
                local_name_var.get().strip(),
                int(level_var.get().strip()),
                float(ratio_var.get().strip()),
                tag_var.get().strip(),
            )
            refresh_table()
            on_after_save()
        except Exception as err:
            messagebox.showerror("错误", str(err), parent=win)

    def on_delete() -> None:
        selected = table.selection()
        if not selected:
            messagebox.showerror("错误", "请先选择要删除的类型", parent=win)
            return
        vals = table.item(selected[0], "values")
        target = str(vals[0])
        try:
            service.delete_ammo_type(target)
            refresh_table()
            on_after_save()
        except Exception as err:
            messagebox.showerror("错误", str(err), parent=win)

    btn_row = ttk.Frame(form, style="Card.TFrame")
    btn_row.pack(fill="x", padx=10, pady=(0, 10))
    ttk.Button(btn_row, text="保存类型", style="Accent.TButton",
               command=on_save).pack(side="left")
    ttk.Button(btn_row, text="删除选中类型", style="Ghost.TButton",
               command=on_delete).pack(side="left", padx=(8, 0))

    def on_pick(_event=None) -> None:
        selected = table.selection()
        if not selected:
            return
        vals = table.item(selected[0], "values")
        local_name_var.set(str(vals[0]))
        level_var.set(str(vals[1]))
        tag_var.set(str(vals[2]))
        ratio_var.set(f"{float(vals[3]):.4f}")

    table.bind("<<TreeviewSelect>>", on_pick)
    refresh_table()


def open_records_manager_dialog(
    root: tk.Tk,
    service: LedgerService,
    refresh_main: Callable[[], None],
    prepare_dropdown_colors: Callable[[ttk.Combobox], None],
    refresh_combo_level_colors: Callable[[ttk.Combobox, str], None],
    clear_combo_selection: Callable[[ttk.Combobox], None],
) -> None:
    win = tk.Toplevel(root)
    win.title("记录管理")
    win.geometry("920x620")
    win.configure(bg=Theme.BG)

    frame = ttk.Frame(win, style="Main.TFrame")
    frame.pack(fill="both", expand=True, padx=12, pady=12)

    notebook = ttk.Notebook(frame)
    notebook.pack(fill="both", expand=True)

    buy_tab = ttk.Frame(notebook, style="Main.TFrame")
    sell_tab = ttk.Frame(notebook, style="Main.TFrame")
    notebook.add(buy_tab, text="买入记录")
    notebook.add(sell_tab, text="卖出记录")

    buy_table = ttk.Treeview(
        buy_tab, columns=("id", "name", "level", "qty", "price", "time"), show="headings", height=16
    )
    for key, title, width, anchor in [
        ("id", "ID", 220, "w"),
        ("name", "名称", 180, "w"),
        ("level", "等级", 70, "center"),
        ("qty", "数量", 90, "center"),
        ("price", "单价", 100, "center"),
        ("time", "时间", 180, "center"),
    ]:
        buy_table.heading(key, text=title)
        buy_table.column(key, width=width, anchor=anchor)
    buy_table.pack(fill="both", expand=True, padx=8, pady=(8, 4))

    buy_edit = ttk.Frame(buy_tab, style="Card.TFrame")
    buy_edit.pack(fill="x", padx=8, pady=(0, 8))
    buy_name_var = tk.StringVar()
    buy_qty_var = tk.StringVar()
    buy_price_var = tk.StringVar()
    buy_id_var = tk.StringVar()

    ttk.Label(buy_edit, text="名称", style="CardLabel.TLabel").pack(side="left")
    buy_name_combo = ttk.Combobox(
        buy_edit, textvariable=buy_name_var, values=service.ammo_names(), width=16
    )
    buy_name_combo.pack(side="left", padx=(6, 8))
    buy_name_combo.configure(
        postcommand=lambda: prepare_dropdown_colors(buy_name_combo))
    buy_name_combo.bind(
        "<<ComboboxSelected>>",
        lambda _e: (
            refresh_combo_level_colors(
                buy_name_combo, buy_name_var.get().strip()),
            clear_combo_selection(buy_name_combo),
        ),
    )
    ttk.Label(buy_edit, text="数量", style="CardLabel.TLabel").pack(side="left")
    ttk.Entry(buy_edit, textvariable=buy_qty_var,
              width=10).pack(side="left", padx=(6, 8))
    ttk.Label(buy_edit, text="单价", style="CardLabel.TLabel").pack(side="left")
    ttk.Entry(buy_edit, textvariable=buy_price_var,
              width=10).pack(side="left", padx=(6, 8))

    sell_table = ttk.Treeview(
        sell_tab, columns=("id", "name", "level", "qty", "price", "time"), show="headings", height=16
    )
    for key, title, width, anchor in [
        ("id", "ID", 220, "w"),
        ("name", "名称", 180, "w"),
        ("level", "等级", 70, "center"),
        ("qty", "数量", 90, "center"),
        ("price", "单价", 100, "center"),
        ("time", "时间", 180, "center"),
    ]:
        sell_table.heading(key, text=title)
        sell_table.column(key, width=width, anchor=anchor)
    sell_table.pack(fill="both", expand=True, padx=8, pady=(8, 4))

    sell_edit = ttk.Frame(sell_tab, style="Card.TFrame")
    sell_edit.pack(fill="x", padx=8, pady=(0, 8))
    sell_name_var = tk.StringVar()
    sell_qty_var = tk.StringVar()
    sell_price_var = tk.StringVar()
    sell_id_var = tk.StringVar()

    ttk.Label(sell_edit, text="名称", style="CardLabel.TLabel").pack(side="left")
    sell_name_combo = ttk.Combobox(
        sell_edit, textvariable=sell_name_var, values=service.ammo_names(), width=16
    )
    sell_name_combo.pack(side="left", padx=(6, 8))
    sell_name_combo.configure(
        postcommand=lambda: prepare_dropdown_colors(sell_name_combo))
    sell_name_combo.bind(
        "<<ComboboxSelected>>",
        lambda _e: (
            refresh_combo_level_colors(
                sell_name_combo, sell_name_var.get().strip()),
            clear_combo_selection(sell_name_combo),
        ),
    )
    ttk.Label(sell_edit, text="数量", style="CardLabel.TLabel").pack(side="left")
    ttk.Entry(sell_edit, textvariable=sell_qty_var,
              width=10).pack(side="left", padx=(6, 8))
    ttk.Label(sell_edit, text="单价", style="CardLabel.TLabel").pack(side="left")
    ttk.Entry(sell_edit, textvariable=sell_price_var,
              width=10).pack(side="left", padx=(6, 8))

    def refresh_records() -> None:
        buy_name_combo["values"] = service.ammo_names()
        sell_name_combo["values"] = service.ammo_names()
        refresh_combo_level_colors(buy_name_combo, buy_name_var.get().strip())
        refresh_combo_level_colors(
            sell_name_combo, sell_name_var.get().strip())

        for item in buy_table.get_children():
            buy_table.delete(item)
        for r in service.buy_record_rows():
            buy_table.insert(
                "",
                "end",
                values=(r["record_id"], r["ammo_name"], r["level"], int(
                    r["quantity"]), int(round(float(r["unit_price"]))), r["created_at"]),
            )

        for item in sell_table.get_children():
            sell_table.delete(item)
        for r in service.sell_record_rows():
            sell_table.insert(
                "",
                "end",
                values=(r["record_id"], r["ammo_name"], r["level"], int(
                    r["quantity"]), int(round(float(r["unit_price"]))), r["created_at"]),
            )

    def on_pick_buy(_event=None) -> None:
        selected = buy_table.selection()
        if not selected:
            return
        vals = buy_table.item(selected[0], "values")
        buy_id_var.set(str(vals[0]))
        buy_name_var.set(str(vals[1]))
        buy_qty_var.set(str(vals[3]))
        buy_price_var.set(str(vals[4]))
        refresh_combo_level_colors(buy_name_combo, buy_name_var.get().strip())

    def on_pick_sell(_event=None) -> None:
        selected = sell_table.selection()
        if not selected:
            return
        vals = sell_table.item(selected[0], "values")
        sell_id_var.set(str(vals[0]))
        sell_name_var.set(str(vals[1]))
        sell_qty_var.set(str(vals[3]))
        sell_price_var.set(str(vals[4]))
        refresh_combo_level_colors(
            sell_name_combo, sell_name_var.get().strip())

    def save_buy_edit() -> None:
        if not buy_id_var.get():
            messagebox.showerror("错误", "请先选择一条买入记录", parent=win)
            return
        try:
            service.update_buy_record(
                buy_id_var.get(),
                buy_name_var.get().strip(),
                int(buy_qty_var.get().strip()),
                float(buy_price_var.get().strip()),
            )
            refresh_records()
            refresh_main()
        except Exception as err:
            messagebox.showerror("错误", str(err), parent=win)

    def save_sell_edit() -> None:
        if not sell_id_var.get():
            messagebox.showerror("错误", "请先选择一条卖出记录", parent=win)
            return
        try:
            service.update_sell_record(
                sell_id_var.get(),
                sell_name_var.get().strip(),
                int(sell_qty_var.get().strip()),
                float(sell_price_var.get().strip()),
            )
            refresh_records()
            refresh_main()
        except Exception as err:
            messagebox.showerror("错误", str(err), parent=win)

    buy_btn_row = ttk.Frame(buy_tab, style="Card.TFrame")
    buy_btn_row.pack(fill="x", padx=8, pady=(0, 10))
    ttk.Button(buy_btn_row, text="保存买入修改", style="Accent.TButton",
               command=save_buy_edit).pack(side="left")

    sell_btn_row = ttk.Frame(sell_tab, style="Card.TFrame")
    sell_btn_row.pack(fill="x", padx=8, pady=(0, 10))
    ttk.Button(sell_btn_row, text="保存卖出修改", style="Accent.TButton",
               command=save_sell_edit).pack(side="left")

    buy_table.bind("<<TreeviewSelect>>", on_pick_buy)
    sell_table.bind("<<TreeviewSelect>>", on_pick_sell)

    refresh_records()


def open_profit_summary_dialog(
    root: tk.Tk,
    service: LedgerService,
    format_compact_number: Callable[[float], str],
    format_full_number: Callable[[float], str],
) -> None:
    win = tk.Toplevel(root)
    win.title("收益概览")
    win.geometry("760x520")
    win.configure(bg=Theme.BG)

    frame = ttk.Frame(win, style="Main.TFrame")
    frame.pack(fill="both", expand=True, padx=12, pady=12)

    table_card = ttk.LabelFrame(frame, text="每种子弹收益", style="Card.TLabelframe")
    table_card.pack(fill="both", expand=True)
    table = ttk.Treeview(
        table_card,
        columns=("name", "level", "tag", "inventory", "avg_buy", "avg_sell", "profit"),
        show="headings",
        height=16,
    )
    table.heading("name", text="名称")
    table.heading("level", text="等级")
    table.heading("tag", text="标签")
    table.heading("inventory", text="库存")
    table.heading("avg_buy", text="平均买入")
    table.heading("avg_sell", text="平均卖出")
    table.heading("profit", text="收益")
    table.column("name", width=190, anchor="w")
    table.column("level", width=60, anchor="center")
    table.column("tag", width=70, anchor="center")
    table.column("inventory", width=70, anchor="center")
    table.column("avg_buy", width=100, anchor="e")
    table.column("avg_sell", width=100, anchor="e")
    table.column("profit", width=120, anchor="e")
    table.pack(fill="both", expand=True, padx=10, pady=10)

    groups = service.grouped_buy_groups(include_zero_inventory=True)
    total_profit = 0.0
    for g in groups:
        profit = float(g["realized_profit"])
        total_profit += profit
        table.insert(
            "",
            "end",
            values=(
                g["name"],
                g["level"],
                g.get("tag", "长期"),
                int(g["inventory"]),
                format_compact_number(float(g["avg_buy"])),
                format_compact_number(float(g["avg_sell"])),
                format_compact_number(profit),
            ),
        )

    summary = ttk.Frame(frame, style="Main.TFrame")
    summary.pack(fill="x", pady=(8, 0))
    total_lbl = ttk.Label(
        summary,
        text=f"总收益: {format_compact_number(total_profit)}",
        style="ValueStrong.TLabel",
    )
    total_lbl.pack(side="left")
    total_lbl_full = ttk.Label(
        summary,
        text=f"（完整: {format_full_number(total_profit)}）",
        style="Sub.TLabel",
    )
    total_lbl_full.pack(side="left", padx=(8, 0))
