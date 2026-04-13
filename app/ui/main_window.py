from __future__ import annotations

import tkinter as tk
from tkinter import ttk, messagebox

from ..services import LedgerService
from .dialogs import open_records_manager_dialog, open_settings_dialog, open_profit_summary_dialog
from .theme import Theme, setup_style
from .widgets import Tooltip


class App:
    def __init__(self, root: tk.Tk) -> None:
        self.root = root
        self.root.title("子弹倒卖助手 - 聚焦平均买入价、回本价、收益和卖出")
        self.root.geometry("900x700")
        self.root.configure(bg=Theme.BG)
        self._center_window(900, 700)

        self.service = LedgerService()
        names = self.service.ammo_names()

        self.name_var = tk.StringVar(value=(names[0] if names else ""))
        self.buy_qty_var = tk.StringVar()
        self.buy_price_var = tk.StringVar()
        self.sell_name_var = tk.StringVar(value=(names[0] if names else ""))
        self.sell_qty_var = tk.StringVar()
        self.sell_price_var = tk.StringVar()
        # 本次运行内，刚卖到 0 的卡片也先保留；下次启动再按库存过滤
        self.session_keep_names: set[str] = set()

        self._setup_style()
        self._build_menu()
        self._build_ui()
        self._bind_events()
        self._refresh_all()

    def _center_window(self, width: int, height: int) -> None:
        screen_w = self.root.winfo_screenwidth()
        screen_h = self.root.winfo_screenheight()
        x = max((screen_w - width) // 2, 0)
        y = max((screen_h - height) // 2, 0)
        self.root.geometry(f"{width}x{height}+{x}+{y}")

    def _setup_style(self) -> None:
        setup_style(self._level_color)

    def _level_color(self, level: int) -> str:
        return {
            1: "#FFFFFF",  # 白色
            2: "#16A34A",  # 绿色
            3: "#2563EB",  # 蓝色
            4: "#7C3AED",  # 紫色
            5: "#EAB308",  # 黄色
        }.get(level, Theme.TEXT)

    def _format_compact_number(self, value: float) -> str:
        value_i = int(round(value))
        abs_v = abs(value_i)
        if abs_v >= 1_000_000:
            return f"{value_i / 1_000_000:.2f}".rstrip("0").rstrip(".") + "M"
        if abs_v >= 1_000:
            return f"{value_i / 1_000:.2f}".rstrip("0").rstrip(".") + "K"
        return str(value_i)

    def _format_full_number(self, value: float) -> str:
        return f"{int(round(value)):,}"

    def _attach_tooltip(self, widget: tk.Widget, text: str) -> None:
        tip = getattr(widget, "_tooltip", None)
        if tip is None:
            setattr(widget, "_tooltip", Tooltip(widget, text))
        else:
            tip.set_text(text)

    def _combobox_level_color(self, ammo_name: str) -> str:
        ammo = self.service.ammo_types.get(ammo_name)
        if ammo is None:
            return Theme.TEXT
        return self._level_color(int(ammo.level))

    def _apply_combobox_text_color(self, combo: ttk.Combobox, ammo_name: str) -> None:
        try:
            combo.configure(foreground=self._combobox_level_color(ammo_name))
        except tk.TclError:
            return

    def _apply_combobox_dropdown_colors(self, combo: ttk.Combobox) -> None:
        try:
            popdown = combo.tk.call("ttk::combobox::PopdownWindow", str(combo))
            listbox = f"{popdown}.f.l"
            values = list(combo.cget("values"))
            for idx, name in enumerate(values):
                combo.tk.call(
                    listbox,
                    "itemconfigure",
                    idx,
                    "-foreground",
                    self._combobox_level_color(str(name)),
                )
        except tk.TclError:
            return

    def _refresh_combo_level_colors(self, combo: ttk.Combobox, selected_name: str) -> None:
        self._apply_combobox_text_color(combo, selected_name)
        self._apply_combobox_dropdown_colors(combo)

    def _prepare_combobox_dropdown_colors(self, combo: ttk.Combobox) -> None:
        # 某些 Tk 主题下第一次展开时 listbox 延迟创建，补一次 after_idle 可确保首开也生效
        self._apply_combobox_dropdown_colors(combo)
        self.root.after_idle(lambda c=combo: self._apply_combobox_dropdown_colors(c))

    def _clear_combo_selection(self, combo: ttk.Combobox) -> None:
        try:
            combo.selection_clear()
            combo.icursor("end")
        except tk.TclError:
            return

    def _build_ui(self) -> None:
        outer = ttk.Frame(self.root, style="Main.TFrame")
        outer.pack(fill="both", expand=True, padx=12, pady=10)

        header = ttk.Frame(outer, style="Main.TFrame")
        header.pack(fill="x", pady=(0, 4))

        metric_line = ttk.Frame(header, style="Main.TFrame")
        metric_line.pack(fill="x")
        self.total_profit_label = ttk.Label(
            metric_line, text="总收益: 0", style="Metric.TLabel")
        self.total_profit_label.pack(side="left")
        self.total_inventory_cost_label = ttk.Label(
            metric_line, text="总库存花费: 0", style="Metric.TLabel")
        self.total_inventory_cost_label.pack(side="left", padx=(8, 0))
        self.total_inventory_qty_label = ttk.Label(
            metric_line, text="总子弹数量: 0", style="Metric.TLabel")
        self.total_inventory_qty_label.pack(side="left", padx=(8, 0))

        top = ttk.Frame(outer, style="Main.TFrame")
        top.pack(fill="x")
        self._build_buy_card(top)
        self._build_sell_card(top)

        card_area = ttk.LabelFrame(
            outer, text="交易卡片", style="Card.TLabelframe")
        card_area.pack(fill="both", expand=True, pady=(8, 0))

        self.cards_canvas = tk.Canvas(
            card_area, bg=Theme.CARD, highlightthickness=0)
        self.cards_canvas.pack(side="left", fill="both",
                               expand=True, padx=(6, 0), pady=6)
        self.cards_scrollbar = ttk.Scrollbar(
            card_area, orient="vertical", command=self.cards_canvas.yview, style="Slim.Vertical.TScrollbar")
        self.cards_canvas.configure(yscrollcommand=self.cards_scrollbar.set)

        self.cards_container = ttk.Frame(
            self.cards_canvas, style="Card.TFrame")
        self.cards_window = self.cards_canvas.create_window(
            (0, 0), window=self.cards_container, anchor="nw")
        self.cards_container.bind("<Configure>", self._on_cards_configure)
        self.cards_canvas.bind("<Configure>", self._on_canvas_configure)

    def _build_menu(self) -> None:
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)

        record_menu = tk.Menu(menubar, tearoff=0)
        record_menu.add_command(
            label="买卖记录管理", command=self.open_records_manager)
        record_menu.add_command(
            label="收益概览", command=self.open_profit_summary)
        menubar.add_cascade(label="记录", menu=record_menu)

        settings_menu = tk.Menu(menubar, tearoff=0)
        settings_menu.add_command(label="子弹类型管理", command=self.open_settings)
        menubar.add_cascade(label="设置", menu=settings_menu)

    def _build_buy_card(self, parent: ttk.Frame) -> None:
        card = ttk.Frame(parent, style="Card.TFrame")
        card.pack(fill="x", padx=(0, 0), pady=(0, 6))
        row = ttk.Frame(card, style="Card.TFrame")
        row.pack(fill="x", padx=6, pady=6)

        ttk.Label(row, text="买入", style="CardLabel.TLabel").pack(side="left", padx=(0, 8))
        ttk.Label(row, text="名称", style="CardLabel.TLabel").pack(side="left")
        self.name_combo = ttk.Combobox(
            row, textvariable=self.name_var, values=self.service.ammo_names(), width=14)
        self.name_combo.pack(side="left", padx=(6, 8))
        self.name_combo.configure(
            postcommand=lambda: self._prepare_combobox_dropdown_colors(self.name_combo)
        )
        self.name_combo.bind(
            "<<ComboboxSelected>>",
            lambda _e: (
                self._refresh_combo_level_colors(self.name_combo, self.name_var.get().strip()),
                self._clear_combo_selection(self.name_combo),
            ),
        )
        ttk.Label(row, text="买入单价", style="CardLabel.TLabel").pack(side="left")
        ttk.Entry(row, textvariable=self.buy_price_var,
                  width=9).pack(side="left", padx=(6, 8))
        ttk.Label(row, text="买入数量", style="CardLabel.TLabel").pack(side="left")
        ttk.Entry(row, textvariable=self.buy_qty_var,
                  width=8).pack(side="left", padx=(6, 8))
        ttk.Button(row, text="保存买入", style="Accent.TButton",
                   command=self.on_add_buy).pack(side="left")

    def _build_sell_card(self, parent: ttk.Frame) -> None:
        card = ttk.Frame(parent, style="Card.TFrame")
        card.pack(fill="x", padx=(0, 0), pady=(0, 0))
        row = ttk.Frame(card, style="Card.TFrame")
        row.pack(fill="x", padx=6, pady=6)

        ttk.Label(row, text="卖出", style="CardLabel.TLabel").pack(side="left", padx=(0, 8))
        ttk.Label(row, text="名称", style="CardLabel.TLabel").pack(side="left")
        self.sell_name_combo = ttk.Combobox(
            row, textvariable=self.sell_name_var, values=self.service.ammo_names(), width=14
        )
        self.sell_name_combo.pack(side="left", padx=(6, 8))
        self.sell_name_combo.configure(
            postcommand=lambda: self._prepare_combobox_dropdown_colors(self.sell_name_combo)
        )
        self.sell_name_combo.bind(
            "<<ComboboxSelected>>",
            lambda _e: (
                self._refresh_combo_level_colors(self.sell_name_combo, self.sell_name_var.get().strip()),
                self._clear_combo_selection(self.sell_name_combo),
            ),
        )
        ttk.Label(row, text="卖出单价", style="CardLabel.TLabel").pack(side="left")
        ttk.Entry(row, textvariable=self.sell_price_var,
                  width=9).pack(side="left", padx=(6, 8))
        ttk.Label(row, text="卖出数量", style="CardLabel.TLabel").pack(side="left")
        ttk.Entry(row, textvariable=self.sell_qty_var,
                  width=8).pack(side="left", padx=(6, 8))
        ttk.Button(row, text="确认卖出", style="Accent.TButton",
                   command=self.on_add_sell).pack(side="left")

    def _bind_events(self) -> None:
        # 全局监听滚轮，但仅在指针位于内容区时生效
        self.root.bind_all("<MouseWheel>", self._on_mousewheel, add="+")

    def _on_mousewheel(self, event) -> None:
        if event.delta == 0:
            return
        px, py = self.root.winfo_pointerx(), self.root.winfo_pointery()
        cx, cy = self.cards_canvas.winfo_rootx(), self.cards_canvas.winfo_rooty()
        cw, ch = self.cards_canvas.winfo_width(), self.cards_canvas.winfo_height()
        if not (cx <= px <= cx + cw and cy <= py <= cy + ch):
            return
        self.cards_canvas.yview_scroll(int(-event.delta / 120), "units")

    def _on_cards_configure(self, _event=None) -> None:
        self.cards_canvas.configure(scrollregion=self.cards_canvas.bbox("all"))
        self._update_scrollbar_visibility()

    def _on_canvas_configure(self, event=None) -> None:
        if event is not None:
            self.cards_canvas.itemconfigure(
                self.cards_window, width=event.width)
        self._update_scrollbar_visibility()

    def _update_scrollbar_visibility(self) -> None:
        bbox = self.cards_canvas.bbox("all")
        if not bbox:
            self.cards_scrollbar.pack_forget()
            return
        content_height = bbox[3] - bbox[1]
        canvas_height = self.cards_canvas.winfo_height()
        if content_height > canvas_height + 2:
            if not self.cards_scrollbar.winfo_ismapped():
                self.cards_scrollbar.pack(
                    side="right", fill="y", padx=(0, 8), pady=8)
        else:
            if self.cards_scrollbar.winfo_ismapped():
                self.cards_scrollbar.pack_forget()

    def _clear_cards(self) -> None:
        for child in self.cards_container.winfo_children():
            child.destroy()

    def _render_cards(self) -> None:
        self._clear_cards()
        groups = self.service.grouped_buy_groups()
        all_groups = self.service.grouped_buy_groups(
            include_zero_inventory=True)
        keep_map = {
            g["name"]: g for g in all_groups if g["name"] in self.session_keep_names
        }
        for name in sorted(keep_map.keys()):
            if all(g["name"] != name for g in groups):
                groups.append(keep_map[name])
        if not groups:
            ttk.Label(self.cards_container, text="暂无买入记录",
                      style="Sub.TLabel").pack(anchor="w", padx=8, pady=8)
            return

        for group in groups:
            level = int(group["level"])
            card_style = f"Level{level}.Card.TLabelframe" if level in (
                1, 2, 3, 4, 5) else "Card.TLabelframe"
            tag_text = str(group.get("tag", "长期"))
            card = ttk.LabelFrame(
                self.cards_container, text=f"{group['name']}（Lv.{group['level']}｜{tag_text}）", style=card_style)
            card.pack(fill="x", padx=3, pady=4)

            top = ttk.Frame(card, style="Card.TFrame")
            top.pack(fill="x", padx=10, pady=(8, 4))
            metric_row = ttk.Frame(top, style="Card.TFrame")
            metric_row.pack(fill="x")
            for col, width in enumerate((165, 150, 120, 140, 100, 190)):
                metric_row.columnconfigure(col, minsize=width, weight=0)
            avg_buy_v = float(group["avg_buy"])
            break_even_v = float(group["break_even"])
            avg_sell_v = float(group["avg_sell"])

            avg_buy_lbl = ttk.Label(
                metric_row, text=f"平均买入价: {self._format_full_number(avg_buy_v)}", style="ValueStrong.TLabel")
            avg_buy_lbl.grid(row=0, column=0, sticky="w")
            self._attach_tooltip(
                avg_buy_lbl, f"平均买入价: {self._format_full_number(avg_buy_v)}")

            break_even_lbl = ttk.Label(
                metric_row, text=f"回本价: {self._format_full_number(break_even_v)}", style="ValueStrong.TLabel")
            break_even_lbl.grid(row=0, column=1, sticky="w")
            ratio_pct = float(group.get("break_even_ratio", 0.87)) * 100
            self._attach_tooltip(
                break_even_lbl,
                f"回本价: {self._format_full_number(break_even_v)}（系数 {ratio_pct:.2f}%）",
            )

            ttk.Label(metric_row, text=f"库存: {group['inventory']}", style="Badge.TLabel").grid(
                row=0, column=2, sticky="w")
            avg_sell_lbl = ttk.Label(
                metric_row, text=f"平均卖出: {self._format_full_number(avg_sell_v)}", style="Value.TLabel")
            avg_sell_lbl.grid(row=0, column=3, sticky="w")
            self._attach_tooltip(
                avg_sell_lbl, f"平均卖出: {self._format_full_number(avg_sell_v)}")

            profit_v = float(group["realized_profit"])
            profit_lbl = ttk.Label(
                metric_row, text=f"收益: {self._format_compact_number(profit_v)}", style="ValueStrong.TLabel")
            profit_lbl.grid(row=0, column=4, sticky="w")
            self._attach_tooltip(
                profit_lbl, f"收益: {self._format_full_number(profit_v)}")

            inventory_cost_v = float(group["inventory_cost"])
            inventory_cost_lbl = ttk.Label(
                metric_row, text=f"库存花费: {self._format_compact_number(inventory_cost_v)}", style="ValueStrong.TLabel")
            inventory_cost_lbl.grid(row=0, column=5, sticky="w")
            self._attach_tooltip(
                inventory_cost_lbl, f"库存花费: {self._format_full_number(inventory_cost_v)}")

            body = ttk.Frame(card, style="Card.TFrame")
            body.pack(fill="x", padx=10, pady=(0, 8))

            price_row = ttk.Frame(body, style="Card.TFrame")
            price_row.pack(fill="x", pady=(0, 6))
            ttk.Label(price_row, text="买入价格记录：", style="CardLabel.TLabel").pack(
                side="left")
            buy_lines = ", ".join(
                [f"{int(round(float(r['buy_price'])))} x {int(r['buy_qty'])}" for r in group["price_rows"]])
            ttk.Label(price_row, text=buy_lines, style="Value.TLabel").pack(
                side="left", padx=(8, 0))
        self.root.after_idle(self._update_scrollbar_visibility)

    def on_add_sell(self) -> None:
        try:
            ammo_name = self.sell_name_var.get().strip()
            requested_qty = int(self.sell_qty_var.get().strip())
            sold_qty = self.service.add_sell(
                ammo_name, requested_qty, float(self.sell_price_var.get().strip()))
            if sold_qty < requested_qty:
                messagebox.showinfo(
                    "已按库存卖出", f"请求卖出 {requested_qty}，实际按库存卖出 {sold_qty}")
            if self.service.current_inventory(ammo_name) <= 0:
                self.session_keep_names.add(ammo_name)
            self.sell_price_var.set("")
            self.sell_qty_var.set("")
            self._refresh_all()
        except Exception as err:
            messagebox.showerror("错误", str(err))

    def _refresh_all(self) -> None:
        self.name_combo["values"] = self.service.ammo_names()
        sell_candidates = [g["name"] for g in self.service.grouped_buy_groups()]
        self.sell_name_combo["values"] = sell_candidates
        if self.sell_name_var.get().strip() not in sell_candidates:
            self.sell_name_var.set(sell_candidates[0] if sell_candidates else "")
        self._refresh_combo_level_colors(self.name_combo, self.name_var.get().strip())
        self._refresh_combo_level_colors(self.sell_name_combo, self.sell_name_var.get().strip())
        total_profit = sum(
            float(g["realized_profit"])
            for g in self.service.grouped_buy_groups(include_zero_inventory=True)
        )
        total_inventory_cost = sum(
            float(g["inventory_cost"])
            for g in self.service.grouped_buy_groups(include_zero_inventory=True)
        )
        self.total_profit_label.config(
            text=f"总收益: {self._format_compact_number(total_profit)}")
        self._attach_tooltip(self.total_profit_label,
                             f"总收益: {self._format_full_number(total_profit)}")
        self.total_inventory_cost_label.config(
            text=f"总库存花费: {self._format_compact_number(total_inventory_cost)}"
        )
        self._attach_tooltip(
            self.total_inventory_cost_label,
            f"总库存花费: {self._format_full_number(total_inventory_cost)}",
        )
        total_inventory_qty = sum(
            int(g["inventory"])
            for g in self.service.grouped_buy_groups(include_zero_inventory=True)
            if int(g["inventory"]) > 0
        )
        self.total_inventory_qty_label.config(text=f"总子弹数量: {total_inventory_qty}")
        self._render_cards()

    def on_add_buy(self) -> None:
        try:
            self.service.add_buy(
                self.name_var.get().strip(),
                int(self.buy_qty_var.get().strip()),
                float(self.buy_price_var.get().strip()),
            )
            self.buy_qty_var.set("")
            self.buy_price_var.set("")
            self._refresh_all()
        except Exception as err:
            messagebox.showerror("错误", str(err))

    def open_settings(self) -> None:
        open_settings_dialog(
            root=self.root,
            service=self.service,
            level_color_fn=self._level_color,
            on_after_save=self._refresh_all,
            name_var=self.name_var,
            name_combo=self.name_combo,
        )

    def open_records_manager(self) -> None:
        open_records_manager_dialog(
            root=self.root,
            service=self.service,
            refresh_main=self._refresh_all,
            prepare_dropdown_colors=self._prepare_combobox_dropdown_colors,
            refresh_combo_level_colors=self._refresh_combo_level_colors,
            clear_combo_selection=self._clear_combo_selection,
        )

    def open_profit_summary(self) -> None:
        open_profit_summary_dialog(
            root=self.root,
            service=self.service,
            format_compact_number=self._format_compact_number,
            format_full_number=self._format_full_number,
        )


def run_app() -> None:
    root = tk.Tk()
    App(root)
    root.mainloop()
