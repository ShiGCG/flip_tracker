from __future__ import annotations

from collections import defaultdict
from datetime import datetime
from typing import Dict, List, Tuple
import uuid
import json
import math

from .models import AmmoType, BuyRecord, SellRecord, to_dict
from .storage import (
    JsonStorage,
    LEDGER_FILE,
    AMMO_IMPORT_FILE,
    TRADE_LOG_FILE,
    PROFIT_SUMMARY_FILE,
    load_initial_state,
)


DEFAULT_BREAK_EVEN_RATIO = 0.8700
VALID_AMMO_TAGS = {"日抛", "周抛", "长期", "赛季"}
TAG_PRIORITY = {"日抛": 0, "周抛": 1, "长期": 2, "赛季": 3}


class LedgerService:
    def __init__(self) -> None:
        self.store = JsonStorage(LEDGER_FILE)
        state = load_initial_state()

        self.ammo_types: Dict[str, AmmoType] = {}
        for row in state["ammo_types"]:
            row.setdefault("break_even_ratio", DEFAULT_BREAK_EVEN_RATIO)
            row.setdefault("tag", "长期")
            ammo = AmmoType(**row)
            self.ammo_types[ammo.name] = ammo
        original_order = list(self.ammo_types.keys())
        self._reorder_ammo_types()

        self.buy_records: List[BuyRecord] = [
            BuyRecord(**row) for row in state["buy_records"]]
        self.sell_records: List[SellRecord] = [
            SellRecord(**row) for row in state["sell_records"]]
        if list(self.ammo_types.keys()) != original_order:
            self.save()

    def _ammo_type_sort_key(self, ammo: AmmoType) -> tuple:
        return (-int(ammo.level), ammo.name)

    def _ordered_ammo_types(self) -> List[AmmoType]:
        return sorted(self.ammo_types.values(), key=self._ammo_type_sort_key)

    def _reorder_ammo_types(self) -> None:
        ordered = self._ordered_ammo_types()
        self.ammo_types = {a.name: a for a in ordered}

    def save(self) -> None:
        payload = {
            "ammo_types": [to_dict(v) for v in self._ordered_ammo_types()],
            "buy_records": [to_dict(r) for r in self.buy_records],
            "sell_records": [to_dict(r) for r in self.sell_records],
        }
        self.store.save(payload)
        self.write_profit_summary()

    def _append_trade_log(self, event: Dict[str, object]) -> None:
        TRADE_LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
        with TRADE_LOG_FILE.open("a", encoding="utf-8") as f:
            f.write(json.dumps(event, ensure_ascii=False) + "\n")

    def write_profit_summary(self) -> None:
        summary_items: List[Dict[str, object]] = []
        total_profit = 0.0
        for group in self.grouped_buy_groups(include_zero_inventory=True):
            item_profit = float(group["realized_profit"])
            summary_items.append(
                {
                    "ammo_name": group["name"],
                    "level": group["level"],
                    "inventory": group["inventory"],
                    "avg_buy": round(float(group["avg_buy"]), 4),
                    "avg_sell": round(float(group["avg_sell"]), 4),
                    "realized_profit": round(item_profit, 4),
                }
            )
            total_profit += item_profit

        payload = {
            "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "total_realized_profit": round(total_profit, 4),
            "items": summary_items,
        }
        JsonStorage(PROFIT_SUMMARY_FILE).save(payload)

    def ammo_names(self) -> List[str]:
        return list(self.ammo_types.keys())

    def ammo_type_rows(self) -> List[Dict[str, object]]:
        rows: List[Dict[str, object]] = []
        for name in self.ammo_names():
            rows.append(
                {
                    "name": name,
                    "level": self.ammo_types[name].level,
                    "break_even_ratio": self.ammo_types[name].break_even_ratio,
                    "tag": self.ammo_types[name].tag,
                    "has_records": self._has_any_records(name),
                }
            )
        return rows

    def _has_any_records(self, ammo_name: str) -> bool:
        return any(r.ammo_name == ammo_name for r in self.buy_records) or any(
            r.ammo_name == ammo_name for r in self.sell_records
        )

    def get_level(self, ammo_name: str) -> int:
        ammo = self.ammo_types.get(ammo_name)
        if ammo is None:
            raise ValueError("未找到该子弹名称，请先导入或新增")
        return ammo.level

    def add_ammo_type(
        self,
        name: str,
        level: int,
        image: str = "default",
        break_even_ratio: float = DEFAULT_BREAK_EVEN_RATIO,
        tag: str = "长期",
    ) -> None:
        clean = name.strip()
        if not clean:
            raise ValueError("名称不能为空")
        if level <= 0:
            raise ValueError("等级必须大于0")
        if break_even_ratio <= 0 or break_even_ratio > 1:
            raise ValueError("回本系数必须在 0 到 1 之间")
        if tag not in VALID_AMMO_TAGS:
            raise ValueError("标签必须是：日抛、周抛、长期、赛季")
        if clean in self.ammo_types and self.ammo_types[clean].level != level:
            raise ValueError("该名称已存在且等级不同，名称与等级必须绑定")
        self.ammo_types[clean] = AmmoType(
            name=clean,
            level=level,
            image=image,
            break_even_ratio=break_even_ratio,
            tag=tag,
        )
        self._reorder_ammo_types()
        self.save()

    def set_ammo_type(
        self,
        name: str,
        level: int,
        break_even_ratio: float | None = None,
        tag: str | None = None,
    ) -> None:
        clean = name.strip()
        if not clean:
            raise ValueError("名称不能为空")
        if level <= 0:
            raise ValueError("等级必须大于0")

        old = self.ammo_types.get(clean)
        ratio = old.break_even_ratio if (old is not None and break_even_ratio is None) else (
            break_even_ratio if break_even_ratio is not None else DEFAULT_BREAK_EVEN_RATIO
        )
        tag_value = old.tag if (old is not None and tag is None) else (tag if tag is not None else "长期")
        if ratio <= 0 or ratio > 1:
            raise ValueError("回本系数必须在 0 到 1 之间")
        if tag_value not in VALID_AMMO_TAGS:
            raise ValueError("标签必须是：日抛、周抛、长期、赛季")
        if old is not None and old.level != level and self._has_any_records(clean):
            raise ValueError("该名称已有交易记录，不能修改等级")

        self.ammo_types[clean] = AmmoType(
            name=clean,
            level=level,
            image=old.image if old else "default",
            break_even_ratio=ratio,
            tag=tag_value,
        )
        self._reorder_ammo_types()
        self.save()

    def delete_ammo_type(self, name: str) -> None:
        clean = name.strip()
        if clean not in self.ammo_types:
            raise ValueError("名称不存在")
        if self._has_any_records(clean):
            raise ValueError("该名称已有交易记录，不能删除")
        del self.ammo_types[clean]
        self._reorder_ammo_types()
        self.save()

    def import_ammo_types(self) -> int:
        source = JsonStorage(AMMO_IMPORT_FILE)
        if not source.exists():
            raise ValueError("未找到导入文件 data\\ammo_types_import.json")

        data = source.load()
        rows = data.get("ammo_types", [])
        added = 0
        for row in rows:
            name = str(row.get("name", "")).strip()
            level = int(row.get("level", 0))
            image = str(row.get("image", "default"))
            break_even_ratio = float(
                row.get("break_even_ratio", DEFAULT_BREAK_EVEN_RATIO))
            tag = str(row.get("tag", "长期"))
            if not name or level <= 0:
                continue
            if break_even_ratio <= 0 or break_even_ratio > 1:
                break_even_ratio = DEFAULT_BREAK_EVEN_RATIO
            if tag not in VALID_AMMO_TAGS:
                tag = "长期"
            old = self.ammo_types.get(name)
            if old is None:
                self.ammo_types[name] = AmmoType(
                    name=name,
                    level=level,
                    image=image or "default",
                    break_even_ratio=break_even_ratio,
                    tag=tag,
                )
                added += 1
            elif old.level == level:
                old.image = image or old.image
                old.break_even_ratio = break_even_ratio
                old.tag = tag
            else:
                # 名称-等级冲突时跳过，保持绑定关系不被破坏
                continue

        self._reorder_ammo_types()
        self.save()
        return added

    def add_buy(self, ammo_name: str, quantity: int, unit_price: float) -> None:
        if quantity <= 0:
            raise ValueError("买入数量必须大于0")
        if unit_price < 0:
            raise ValueError("买入单价不能小于0")
        if ammo_name not in self.ammo_types:
            raise ValueError("名称不存在，请先导入或新增类型")

        level = self.ammo_types[ammo_name].level
        self.buy_records.append(
            BuyRecord(
                record_id=str(uuid.uuid4()),
                ammo_name=ammo_name,
                level=level,
                quantity=quantity,
                unit_price=unit_price,
                created_at=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            )
        )
        self._append_trade_log(
            {
                "time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "action": "buy",
                "ammo_name": ammo_name,
                "level": level,
                "quantity": quantity,
                "unit_price": unit_price,
                "total": round(quantity * unit_price, 4),
            }
        )
        self.save()

    def current_inventory(self, ammo_name: str) -> int:
        buy_qty = sum(
            r.quantity for r in self.buy_records if r.ammo_name == ammo_name)
        sell_qty = sum(
            r.quantity for r in self.sell_records if r.ammo_name == ammo_name)
        return buy_qty - sell_qty

    def add_sell(self, ammo_name: str, quantity: int, unit_price: float) -> int:
        if quantity <= 0:
            raise ValueError("卖出数量必须大于0")
        if unit_price < 0:
            raise ValueError("卖出单价不能小于0")
        if ammo_name not in self.ammo_types:
            raise ValueError("名称不存在")

        inventory = self.current_inventory(ammo_name)
        if inventory <= 0:
            raise ValueError("当前库存为 0，无法卖出")
        sold_qty = min(quantity, inventory)

        level = self.ammo_types[ammo_name].level
        self.sell_records.append(
            SellRecord(
                record_id=str(uuid.uuid4()),
                ammo_name=ammo_name,
                level=level,
                quantity=sold_qty,
                unit_price=unit_price,
                created_at=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            )
        )
        self._append_trade_log(
            {
                "time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "action": "sell",
                "ammo_name": ammo_name,
                "level": level,
                "requested_quantity": quantity,
                "quantity": sold_qty,
                "unit_price": unit_price,
                "total": round(sold_qty * unit_price, 4),
            }
        )
        self.save()
        return sold_qty

    def grouped_buy_groups(self, include_zero_inventory: bool = False) -> List[Dict[str, object]]:
        # 以“每种子弹一个分组块”返回，便于 UI 做外框分组展示
        grouped: Dict[Tuple[str, int, float], int] = defaultdict(int)
        for r in self.buy_records:
            grouped[(r.ammo_name, r.level, r.unit_price)] += r.quantity

        by_name: Dict[str, List[Tuple[int, float, int]]] = defaultdict(list)
        for (name, level, price), qty in grouped.items():
            by_name[name].append((level, price, qty))

        groups: List[Dict[str, object]] = []
        for name in by_name.keys():
            parts = sorted(by_name[name], key=lambda x: x[1])
            level = parts[0][0]

            total_qty = sum(q for _, _, q in parts)
            total_cost = sum(price * qty for _, price, qty in parts)
            avg_buy = total_cost / total_qty if total_qty > 0 else 0.0
            ratio = float(self.ammo_types[name].break_even_ratio)
            break_even = math.ceil(avg_buy / ratio) if ratio > 0 else 0.0

            sold_qty = sum(
                s.quantity for s in self.sell_records if s.ammo_name == name)
            sold_total = sum(
                s.total for s in self.sell_records if s.ammo_name == name)
            avg_sell = sold_total / sold_qty if sold_qty > 0 else 0.0
            inventory = total_qty - sold_qty
            realized_profit = sold_total - (sold_qty * break_even)
            inventory_cost = max(inventory, 0) * avg_buy

            if (not include_zero_inventory) and inventory <= 0:
                continue

            price_rows = [{"buy_price": price, "buy_qty": qty}
                          for _, price, qty in parts]
            tag = self.ammo_types[name].tag
            latest_buy_raw = max(
                (r.created_at for r in self.buy_records if r.ammo_name == name),
                default="1970-01-01 00:00:00",
            )
            try:
                latest_buy_dt = datetime.strptime(latest_buy_raw, "%Y-%m-%d %H:%M:%S")
            except ValueError:
                latest_buy_dt = datetime.min
            groups.append(
                {
                    "name": name,
                    "level": level,
                    "image": self.ammo_types[name].image,
                    "break_even_ratio": ratio,
                    "tag": tag,
                    "price_rows": price_rows,
                    "avg_buy": avg_buy,
                    "break_even": break_even,
                    "sold_qty": sold_qty,
                    "avg_sell": avg_sell,
                    "inventory": inventory,
                    "realized_profit": realized_profit,
                    "inventory_cost": inventory_cost,
                    "_sort_tag_rank": TAG_PRIORITY.get(tag, 99),
                    "_sort_latest_buy_ts": latest_buy_dt.timestamp(),
                }
            )
        groups.sort(
            key=lambda g: (
                int(g["_sort_tag_rank"]),
                -float(g["_sort_latest_buy_ts"]),
                str(g["name"]),
            )
        )
        return groups

    def grouped_buy_rows(self) -> List[Dict[str, object]]:
        # 兼容旧界面调用
        rows: List[Dict[str, object]] = []
        for group in self.grouped_buy_groups():
            first = True
            for line in group["price_rows"]:
                rows.append(
                    {
                        "name": group["name"] if first else "",
                        "name_key": group["name"],
                        "level": group["level"] if first else "",
                        "image": group["image"] if first else "",
                        "buy_price": line["buy_price"],
                        "buy_qty": line["buy_qty"],
                        "avg_buy": group["avg_buy"] if first else "",
                        "break_even": group["break_even"] if first else "",
                        "sold_qty": group["sold_qty"] if first else "",
                        "avg_sell": group["avg_sell"] if first else "",
                        "inventory": group["inventory"] if first else "",
                        "is_group_header": first,
                    }
                )
                first = False
        return rows

    def all_sells(self) -> List[SellRecord]:
        return list(self.sell_records)

    def buy_record_rows(self) -> List[Dict[str, object]]:
        rows: List[Dict[str, object]] = []
        for r in sorted(
            self.buy_records,
            key=lambda x: (x.created_at, x.record_id),
            reverse=True,
        ):
            rows.append(
                {
                    "record_id": r.record_id,
                    "ammo_name": r.ammo_name,
                    "level": r.level,
                    "quantity": r.quantity,
                    "unit_price": r.unit_price,
                    "created_at": r.created_at,
                }
            )
        return rows

    def sell_record_rows(self) -> List[Dict[str, object]]:
        rows: List[Dict[str, object]] = []
        for r in sorted(
            self.sell_records,
            key=lambda x: (x.created_at, x.record_id),
            reverse=True,
        ):
            rows.append(
                {
                    "record_id": r.record_id,
                    "ammo_name": r.ammo_name,
                    "level": r.level,
                    "quantity": r.quantity,
                    "unit_price": r.unit_price,
                    "created_at": r.created_at,
                }
            )
        return rows

    def update_buy_record(self, record_id: str, ammo_name: str, quantity: int, unit_price: float) -> None:
        if quantity <= 0:
            raise ValueError("买入数量必须大于0")
        if unit_price < 0:
            raise ValueError("买入单价不能小于0")
        if ammo_name not in self.ammo_types:
            raise ValueError("名称不存在，请先在设置中新增类型")

        target = next(
            (r for r in self.buy_records if r.record_id == record_id), None)
        if target is None:
            raise ValueError("买入记录不存在")

        target.ammo_name = ammo_name
        target.level = self.ammo_types[ammo_name].level
        target.quantity = quantity
        target.unit_price = unit_price
        self.save()

    def update_sell_record(self, record_id: str, ammo_name: str, quantity: int, unit_price: float) -> None:
        if quantity <= 0:
            raise ValueError("卖出数量必须大于0")
        if unit_price < 0:
            raise ValueError("卖出单价不能小于0")
        if ammo_name not in self.ammo_types:
            raise ValueError("名称不存在，请先在设置中新增类型")

        target = next(
            (r for r in self.sell_records if r.record_id == record_id), None)
        if target is None:
            raise ValueError("卖出记录不存在")

        buy_qty = sum(
            r.quantity for r in self.buy_records if r.ammo_name == ammo_name)
        other_sell_qty = sum(
            r.quantity for r in self.sell_records
            if r.record_id != record_id and r.ammo_name == ammo_name
        )
        if quantity + other_sell_qty > buy_qty:
            raise ValueError("修改后卖出总量超过买入总量")

        target.ammo_name = ammo_name
        target.level = self.ammo_types[ammo_name].level
        target.quantity = quantity
        target.unit_price = unit_price
        self.save()
