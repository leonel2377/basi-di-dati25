"""
Console-based interaction helpers for the inventory tracker.
"""

from __future__ import annotations

from typing import Callable

import pandas as pd

from .status import StockStatus


def build_cli_reorder_prompt(input_fn: Callable[[str], str] = input) -> Callable[[pd.Series], bool]:
    """
    Create a reorder prompt function that interacts via the console.

    The returned callable accepts a pandas Series representing the item row.
    """

    def prompt(row: pd.Series) -> bool:
        product = f"{row['product_name']} ({row['product_id']})"
        message = (
            f"Stock for {product} is low (quantity: {row['quantity']}, "
            f"reorder point: {row['reorder_point']}). Confirm reorder? [y/N]: "
        )
        response = input_fn(message).strip().lower()
        return response in {"y", "yes"}

    return prompt


def print_summary(df: pd.DataFrame) -> None:
    """
    Print a textual summary of inventory status counts by color.
    """
    counts = df["status"].value_counts().reindex([status.value for status in StockStatus], fill_value=0)
    print("\nInventory Status Summary")
    print("------------------------")
    for status in StockStatus:
        print(f"{status.name.title():<8} : {counts[status.value]}")
    print()

