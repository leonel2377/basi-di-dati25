"""
Visualization utilities for the inventory tracker.
"""

from __future__ import annotations

from pathlib import Path
from typing import Optional

import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns

from .status import StockStatus


def plot_inventory_status(df: pd.DataFrame, save_path: Optional[str | Path] = None) -> None:
    """
    Render a bar chart of current stock levels color-coded by status.

    Parameters
    ----------
    df:
        Inventory DataFrame expected to contain ``status`` and ``quantity`` columns.
    save_path:
        Optional path to save the figure instead of (or in addition to) showing it.
    """
    if df.empty:
        raise ValueError("Cannot plot inventory - no data provided")

    sns.set_theme(style="whitegrid")
    color_map = {status.value: status.color for status in StockStatus}

    plt.figure(figsize=(10, 6))
    ax = sns.barplot(
        data=df.sort_values("quantity", ascending=False),
        x="product_name",
        y="quantity",
        hue="status",
        dodge=False,
        palette=color_map,
    )
    ax.set_title("Inventory Levels by Product")
    ax.set_xlabel("Product")
    ax.set_ylabel("Quantity")
    plt.setp(ax.get_xticklabels(), rotation=45, ha="right")
    ax.legend(title="Status")
    plt.tight_layout()

    if save_path:
        save_path = Path(save_path)
        save_path.parent.mkdir(parents=True, exist_ok=True)
        plt.savefig(save_path)
        print(f"Saved inventory visualization to {save_path}")

    plt.show()

