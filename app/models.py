from __future__ import annotations

from dataclasses import dataclass, asdict


@dataclass
class AmmoType:
    name: str
    level: int
    image: str = "default"
    break_even_ratio: float = 0.87
    tag: str = "长期"


@dataclass
class BuyRecord:
    record_id: str
    ammo_name: str
    level: int
    quantity: int
    unit_price: float
    created_at: str

    @property
    def total(self) -> float:
        return self.quantity * self.unit_price


@dataclass
class SellRecord:
    record_id: str
    ammo_name: str
    level: int
    quantity: int
    unit_price: float
    created_at: str

    @property
    def total(self) -> float:
        return self.quantity * self.unit_price


def to_dict(obj: object) -> dict:
    return asdict(obj)

