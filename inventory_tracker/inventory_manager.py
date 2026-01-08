"""
Business logic for computing inventory status and handling reorder decisions.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Optional

import pandas as pd

from .status import StatusThresholds, StockStatus, classify_stock_level


ReorderPrompt = Callable[[pd.Series], bool]


@dataclass
class InventoryDecision:
    """Represents the outcome for an individual inventory item."""

    status: StockStatus
    auto_reordered: bool = False
    reorder_confirmed: bool = False

    @property
    def should_reorder(self) -> bool:
        return self.status in {StockStatus.RED, StockStatus.ORANGE} and (
            self.auto_reordered or self.reorder_confirmed
        )


class InventoryManager:
    """
    Central object orchestrating stock evaluation and reorder logic.
    """

    def __init__(
        self,
        inventory_df: pd.DataFrame,
        reorder_prompt: Optional[ReorderPrompt] = None,
    ) -> None:
        self._df = inventory_df.copy()
        self._decisions: dict[str, InventoryDecision] = {}
        self._reorder_prompt = reorder_prompt

    @property
    def inventory(self) -> pd.DataFrame:
        """Return a defensive copy for read-only operations."""
        return self._df.copy()

    @property
    def decisions(self) -> dict[str, InventoryDecision]:
        return dict(self._decisions)

    def evaluate(self) -> pd.DataFrame:
        """
        Evaluate the inventory DataFrame and enrich it with status metadata.
        """
        decisions: dict[str, InventoryDecision] = {}
        status_values = []

        for _, row in self._df.iterrows():
            thresholds = StatusThresholds(
                reorder_point=int(row["reorder_point"]),
                critical_point=int(row["critical_point"]),
            )
            status = classify_stock_level(row["quantity"], thresholds)
            decisions[row["product_id"]] = self._make_decision(row, status)
            status_values.append(status.value)

        self._decisions = decisions
        self._df["status"] = status_values

        return self.inventory

    def _make_decision(self, row: pd.Series, status: StockStatus) -> InventoryDecision:
        if status is StockStatus.GREEN:
            return InventoryDecision(status=status)

        if status is StockStatus.RED:
            return InventoryDecision(status=status, auto_reordered=True)

        if self._reorder_prompt is None:
            return InventoryDecision(status=status, reorder_confirmed=False)

        confirmed = self._reorder_prompt(row)
        return InventoryDecision(status=status, reorder_confirmed=confirmed)

    def apply_reorders(self) -> pd.DataFrame:
        """
        Update inventory quantities based on decisions.
        """
        df = self._df.copy()
        for idx, row in df.iterrows():
            decision = self._decisions.get(row["product_id"])
            if decision and decision.should_reorder:
                df.at[idx, "quantity"] = row["quantity"] + row.get("reorder_quantity", 0)
        self._df = df
        return self.inventory

