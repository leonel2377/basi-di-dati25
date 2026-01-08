"""
High-level orchestration for running the inventory tracker workflow.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Literal, Optional

import pandas as pd

from .data_loader import InventoryDataError, load_inventory_csv
from .inventory_manager import InventoryManager
from .ml_predictor import (
    DemandPredictor,
    classify_product_volatility,
    predict_optimal_reorder_quantity,
)
from .user_interface import build_cli_reorder_prompt, print_summary
from .visualization import plot_inventory_status


@dataclass
class InventoryAppConfig:
    """Configuration options for running the inventory tracker app."""

    inventory_path: Path
    encoding: str = "utf-8"
    save_plot_path: Optional[Path] = None
    auto_show_plot: bool = True
    orange_strategy: Literal["prompt", "auto-confirm", "auto-decline"] = "prompt"
    enable_ml_predictions: bool = False
    sales_history_path: Optional[Path] = None
    ml_model_type: Literal["random_forest", "xgboost", "lstm"] = "random_forest"


class InventoryApp:
    """
    High-level interface for running the inventory tracker workflow.
    """

    def __init__(self, config: InventoryAppConfig) -> None:
        self.config = config
        self._validate_config()

    def run(self) -> None:
        """
        Execute the end-to-end workflow: load data, evaluate, interact, visualize.
        """
        df = self._load()

        # ML predictions if enabled
        if self.config.enable_ml_predictions:
            df = self._apply_ml_predictions(df)

        manager = InventoryManager(df, reorder_prompt=self._resolve_reorder_prompt())
        evaluated = manager.evaluate()

        print_summary(evaluated)

        updated = manager.apply_reorders()
        self._display_table(updated)

        if self.config.enable_ml_predictions:
            self._display_ml_insights(evaluated)

        if self.config.auto_show_plot or self.config.save_plot_path is not None:
            plot_inventory_status(
                updated,
                save_path=str(self.config.save_plot_path) if self.config.save_plot_path else None,
            )

    def _load(self) -> pd.DataFrame:
        try:
            return load_inventory_csv(self.config.inventory_path, encoding=self.config.encoding)
        except FileNotFoundError as exc:
            raise SystemExit(str(exc)) from exc
        except InventoryDataError as exc:
            raise SystemExit(str(exc)) from exc

    def _resolve_reorder_prompt(self):
        if self.config.orange_strategy == "auto-confirm":
            return lambda _: True
        if self.config.orange_strategy == "auto-decline":
            return lambda _: False
        return build_cli_reorder_prompt()

    @staticmethod
    def _display_table(df: pd.DataFrame) -> None:
        display_columns = [
            "product_id",
            "product_name",
            "category",
            "quantity",
            "reorder_point",
            "critical_point",
            "status",
        ]
        if "reorder_quantity" in df.columns:
            display_columns.append("reorder_quantity")

        print("Updated Inventory Table")
        print("----------------------")
        print(df[display_columns].to_string(index=False))

    def _validate_config(self) -> None:
        valid = {"prompt", "auto-confirm", "auto-decline"}
        if self.config.orange_strategy not in valid:
            raise ValueError(
                f"Invalid orange strategy '{self.config.orange_strategy}'. "
                f"Expected one of: {', '.join(sorted(valid))}"
            )
        if self.config.enable_ml_predictions and self.config.sales_history_path is None:
            # Try to find default sales history
            default_path = Path("data") / "sales_history.csv"
            if default_path.exists():
                self.config.sales_history_path = default_path
            else:
                raise ValueError(
                    "ML predictions enabled but no sales history path provided. "
                    "Either provide --sales-history or ensure data/sales_history.csv exists."
                )

    def _apply_ml_predictions(self, df: pd.DataFrame) -> pd.DataFrame:
        """Apply ML predictions to update reorder quantities and add volatility classification."""
        if self.config.sales_history_path is None or not self.config.sales_history_path.exists():
            print("Warning: Sales history file not found. Skipping ML predictions.")
            return df

        try:
            sales_history = pd.read_csv(self.config.sales_history_path)
            sales_history["date"] = pd.to_datetime(sales_history["date"])

            # Classify product volatility
            volatility_df = classify_product_volatility(sales_history)
            df = df.merge(volatility_df[["product_id", "volatility_class"]], on="product_id", how="left")
            df["volatility_class"] = df["volatility_class"].fillna("unknown")

            # Train demand predictor
            print(f"\nTraining {self.config.ml_model_type} model for demand prediction...")
            predictor = DemandPredictor(model_type=self.config.ml_model_type)
            metrics = predictor.train(sales_history)
            print(f"Model training complete. Train score: {metrics['train_score']:.3f}, "
                  f"Test score: {metrics['test_score']:.3f}")

            # Predict optimal reorder quantities
            print("\nPredicting optimal reorder quantities using ML...")
            current_date = pd.Timestamp.now()
            optimal_quantities = []

            for idx, row in df.iterrows():
                try:
                    demand_pred = predictor.predict_demand(
                        product_id=row["product_id"],
                        current_date=current_date,
                        historical_data=sales_history,
                        days_ahead=30,
                    )
                    optimal_reorder = predict_optimal_reorder_quantity(
                        product_id=row["product_id"],
                        current_quantity=int(row["quantity"]),
                        demand_prediction=demand_pred,
                        reorder_point=int(row["reorder_point"]),
                        critical_point=int(row["critical_point"]),
                    )
                    optimal_quantities.append(optimal_reorder.optimal_reorder_quantity)

                    # Update reorder_quantity with ML prediction if better
                    if "reorder_quantity" in df.columns:
                        current_reorder = row.get("reorder_quantity", 0)
                        # Use ML prediction if it's more reasonable (within 50% of current)
                        if abs(optimal_reorder.optimal_reorder_quantity - current_reorder) / max(current_reorder, 1) < 0.5:
                            df.loc[idx, "reorder_quantity"] = optimal_reorder.optimal_reorder_quantity
                except Exception as e:
                    print(f"Warning: Could not predict for {row['product_id']}: {e}")
                    optimal_quantities.append(row.get("reorder_quantity", 0))

            df["ml_predicted_reorder"] = optimal_quantities
            print("ML predictions applied successfully.\n")

        except Exception as e:
            print(f"Error applying ML predictions: {e}")
            print("Continuing with standard inventory tracking...")

        return df

    def _display_ml_insights(self, df: pd.DataFrame) -> None:
        """Display ML-generated insights."""
        print("\n" + "=" * 60)
        print("ML-Generated Insights")
        print("=" * 60)

        if "volatility_class" in df.columns:
            print("\nProduct Volatility Classification:")
            print("-" * 60)
            volatility_summary = df.groupby("volatility_class").size()
            for vol_class, count in volatility_summary.items():
                print(f"  {vol_class.capitalize():<15}: {count} products")

        if "ml_predicted_reorder" in df.columns:
            print("\nML-Predicted Optimal Reorder Quantities:")
            print("-" * 60)
            display_cols = ["product_id", "product_name", "reorder_quantity", "ml_predicted_reorder"]
            if "volatility_class" in df.columns:
                display_cols.insert(3, "volatility_class")
            print(df[display_cols].to_string(index=False))

        print("\n" + "=" * 60 + "\n")

