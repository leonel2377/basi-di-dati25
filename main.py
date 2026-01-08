"""
Command-line entry point for the inventory tracker application.
"""

from __future__ import annotations

import argparse
from pathlib import Path

from inventory_tracker.app import InventoryApp, InventoryAppConfig


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Inventory Tracker with Dynamic Reorder Alerts")
    parser.add_argument(
        "--inventory",
        type=Path,
        default=Path("data") / "sample_inventory.csv",
        help="Path to the inventory CSV file",
    )
    parser.add_argument(
        "--encoding",
        default="utf-8",
        help="Encoding used to read the CSV file",
    )
    parser.add_argument(
        "--save-plot",
        type=Path,
        default=None,
        help="Optional path to save the visualization image",
    )
    parser.add_argument(
        "--no-show-plot",
        action="store_true",
        help="Disable displaying the plot interactively",
    )
    parser.add_argument(
        "--orange-strategy",
        choices=["prompt", "auto-confirm", "auto-decline"],
        default="prompt",
        help="How to handle low-stock (orange) items",
    )
    parser.add_argument(
        "--enable-ml",
        action="store_true",
        help="Enable ML predictions for demand forecasting and optimal reorder quantities",
    )
    parser.add_argument(
        "--sales-history",
        type=Path,
        default=None,
        help="Path to sales history CSV file (default: data/sales_history.csv)",
    )
    parser.add_argument(
        "--ml-model",
        choices=["random_forest", "xgboost", "lstm"],
        default="random_forest",
        help="ML model type to use for predictions",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    config = InventoryAppConfig(
        inventory_path=args.inventory,
        encoding=args.encoding,
        save_plot_path=args.save_plot,
        auto_show_plot=not args.no_show_plot,
        orange_strategy=args.orange_strategy,
        enable_ml_predictions=args.enable_ml,
        sales_history_path=args.sales_history or Path("data") / "sales_history.csv",
        ml_model_type=args.ml_model,
    )
    app = InventoryApp(config)
    app.run()


if __name__ == "__main__":
    main()

