"""
Inventory item stock status definitions and utilities.
"""

from __future__ import annotations

from enum import Enum
from dataclasses import dataclass


class StockStatus(str, Enum):
    """Represents the interpreted inventory status for an item."""

    GREEN = "green"
    ORANGE = "orange"
    RED = "red"

    @property
    def description(self) -> str:
        """Human readable description suitable for UI display."""
        descriptions = {
            StockStatus.GREEN: "Stock sufficient",
            StockStatus.ORANGE: "Stock low - review reorder",
            StockStatus.RED: "Stock critical - immediate action required",
        }
        return descriptions[self]

    @property
    def color(self) -> str:
        """Color alias for plotting with matplotlib / seaborn."""
        colors = {
            StockStatus.GREEN: "#2ecc71",
            StockStatus.ORANGE: "#f39c12",
            StockStatus.RED: "#e74c3c",
        }
        return colors[self]


@dataclass(frozen=True)
class StatusThresholds:
    """
    Represents threshold configuration for computing stock status.

    Attributes
    ----------
    reorder_point:
        Stock level at which the system should suggest a reorder (inclusive).
    critical_point:
        Stock level below which stock is considered critical (strictly).
    """

    reorder_point: int
    critical_point: int

    def validate(self) -> None:
        """Ensure thresholds follow expected ordering."""
        if self.reorder_point < 0 or self.critical_point < 0:
            raise ValueError("Thresholds cannot be negative")
        if self.critical_point > self.reorder_point:
            raise ValueError("Critical point must be <= reorder point")


def classify_stock_level(quantity: float, thresholds: StatusThresholds) -> StockStatus:
    """
    Classify a quantity into a StockStatus based on provided thresholds.

    Parameters
    ----------
    quantity:
        Current stock quantity for an item.
    thresholds:
        Threshold configuration for the item.
    """
    thresholds.validate()

    if quantity <= thresholds.critical_point:
        return StockStatus.RED
    if quantity <= thresholds.reorder_point:
        return StockStatus.ORANGE
    return StockStatus.GREEN

