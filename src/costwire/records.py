"""One price number = one PriceRecord.

Product rule: never guess a number. Every number must carry a source URL
and the date it applies to. If either is missing, we refuse to make the
record, so a bad number can never sneak into the brief.
"""

from dataclasses import dataclass
from datetime import date


@dataclass(frozen=True)
class PriceRecord:
    item: str          # e.g. "anhydrous"
    price: float       # e.g. 850.0
    unit: str          # e.g. "$/ton"
    as_of: date        # the date the source says the price applies to
    source_url: str    # link to the exact report
    source_name: str   # e.g. "USDA AMS Iowa Production Cost Report"

    def __post_init__(self):
        if not self.item.strip():
            raise ValueError("item name is required")
        if not isinstance(self.as_of, date):
            raise ValueError(f"{self.item}: as_of must be a date")
        if not self.source_url.startswith(("http://", "https://")):
            raise ValueError(f"{self.item}: a source URL is required")
        if not self.source_name.strip():
            raise ValueError(f"{self.item}: a source name is required")
        if isinstance(self.price, bool) or not isinstance(self.price, (int, float)):
            raise ValueError(f"{self.item}: price must be a number")
        if self.price != self.price or self.price < 0:  # NaN or negative
            raise ValueError(f"{self.item}: price must be a real, non-negative number")

    def to_row(self) -> dict:
        """Flat dict for writing to CSV."""
        return {
            "item": self.item,
            "price": self.price,
            "unit": self.unit,
            "as_of": self.as_of.isoformat(),
            "source_name": self.source_name,
            "source_url": self.source_url,
        }
