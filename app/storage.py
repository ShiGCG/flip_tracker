from __future__ import annotations

from pathlib import Path
import json
from typing import Dict, Any


BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
LEDGER_FILE = DATA_DIR / "ledger.json"
AMMO_IMPORT_FILE = DATA_DIR / "ammo_types_import.json"
TRADE_LOG_FILE = DATA_DIR / "trade_log.jsonl"
PROFIT_SUMMARY_FILE = DATA_DIR / "profit_summary.json"


DEFAULT_AMMO_TYPES = [
    {"name": "9mm FMJ", "level": 1, "image": "default", "break_even_ratio": 0.87, "tag": "长期"},
    {"name": "5.45 PS", "level": 2, "image": "default", "break_even_ratio": 0.87, "tag": "长期"},
    {"name": "7.62 BP", "level": 4, "image": "default", "break_even_ratio": 0.87, "tag": "长期"},
]


class JsonStorage:
    def __init__(self, path: Path) -> None:
        self.path = path
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def exists(self) -> bool:
        return self.path.exists()

    def load(self) -> Dict[str, Any]:
        if not self.path.exists():
            return {}
        return json.loads(self.path.read_text(encoding="utf-8"))

    def save(self, payload: Dict[str, Any]) -> None:
        self.path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def load_initial_state() -> Dict[str, Any]:
    store = JsonStorage(LEDGER_FILE)
    if not store.exists():
        state = {
            "ammo_types": DEFAULT_AMMO_TYPES,
            "buy_records": [],
            "sell_records": [],
        }
        store.save(state)
        return state

    state = store.load()
    state.setdefault("ammo_types", DEFAULT_AMMO_TYPES.copy())
    state.setdefault("buy_records", [])
    state.setdefault("sell_records", [])
    return state

