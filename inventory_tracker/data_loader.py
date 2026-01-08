"""
Utilities for loading and validating inventory datasets.
"""

from __future__ import annotations

from pathlib import Path
from typing import Iterable, Optional

import pandas as pd

REQUIRED_COLUMNS = {
    "product_id",
    "product_name",
    "category",
    "quantity",
    "reorder_point",
    "critical_point",
}


class InventoryDataError(RuntimeError):
    """Raised when inventory data does not meet validation expectations."""


def load_inventory_csv(path: str | Path, encoding: Optional[str] = "utf-8") -> pd.DataFrame:
    """
    Load inventory data from a CSV file.

    The CSV is expected to include at least the columns defined in
    ``REQUIRED_COLUMNS``.
    """
    file_path = Path(path)
    if not file_path.exists():
        raise FileNotFoundError(f"Inventory file not found: {file_path}")

    df = pd.read_csv(file_path, encoding=encoding)
    _validate_columns(df.columns)

    # Check for duplicate product IDs
    duplicates = df[df.duplicated(subset=["product_id"], keep=False)]
    if not duplicates.empty:
        duplicate_ids = duplicates["product_id"].unique()
        raise InventoryDataError(
            f"Duplicate product_id found in inventory data: {', '.join(duplicate_ids)}. "
            f"Each product_id must be unique."
        )

    numeric_columns = ["quantity", "reorder_point", "critical_point"]
    df[numeric_columns] = df[numeric_columns].apply(pd.to_numeric, errors="raise")

    # Check for negative values in numeric columns
    for col in numeric_columns:
        if (df[col] < 0).any():
            negative_rows = df[df[col] < 0]
            raise InventoryDataError(
                f"Negative values found in column '{col}'. "
                f"Found in products: {', '.join(negative_rows['product_id'].tolist())}"
            )

    # Check for NaN values in required numeric columns
    for col in numeric_columns:
        if df[col].isna().any():
            nan_rows = df[df[col].isna()]
            raise InventoryDataError(
                f"Missing (NaN) values found in column '{col}'. "
                f"Found in products: {', '.join(nan_rows['product_id'].tolist())}"
            )

    return df


def _validate_columns(columns: Iterable[str]) -> None:
    missing = REQUIRED_COLUMNS - set(columns)
    if missing:
        raise InventoryDataError(
            f"Inventory data missing required columns: {', '.join(sorted(missing))}"
        )

