"""
Script to generate synthetic sales history data for ML model training.
"""

from __future__ import annotations

import random
from datetime import datetime, timedelta

import numpy as np
import pandas as pd


def generate_sales_history(
    product_ids: list[str],
    start_date: str = "2023-01-01",
    end_date: str = "2024-12-31",
    base_demand_range: tuple[int, int] = (5, 50),
) -> pd.DataFrame:
    """
    Generate synthetic sales history data for products.

    Parameters
    ----------
    product_ids
        List of product IDs to generate data for
    start_date
        Start date for sales history
    end_date
        End date for sales history
    base_demand_range
        Range for base demand levels (min, max)

    Returns
    -------
    DataFrame with columns: date, product_id, quantity_sold
    """
    start = datetime.strptime(start_date, "%Y-%m-%d")
    end = datetime.strptime(end_date, "%Y-%m-%d")
    dates = pd.date_range(start, end, freq="D")

    sales_data = []

    # Generate base demand for each product
    product_base_demand = {
        pid: random.randint(*base_demand_range) for pid in product_ids
    }

    for product_id in product_ids:
        base_demand = product_base_demand[product_id]

        for date in dates:
            # Add seasonality (higher sales on weekends, certain months)
            day_of_week_factor = 1.3 if date.weekday() >= 5 else 1.0  # Weekend boost
            month_factor = 1.2 if date.month in [11, 12] else 1.0  # Holiday season

            # Add random variation
            random_factor = np.random.normal(1.0, 0.3)
            random_factor = max(0.1, random_factor)  # Ensure positive

            # Add trend (some products have trends)
            trend_factor = 1.0
            if hash(product_id) % 3 == 0:  # 1/3 of products have trends
                days_from_start = (date - start).days
                trend_factor = 1.0 + (days_from_start / 1000) * 0.1  # Gradual increase

            # Calculate daily sales
            daily_sales = int(
                base_demand * day_of_week_factor * month_factor * random_factor * trend_factor
            )
            daily_sales = max(0, daily_sales)  # Ensure non-negative

            sales_data.append({
                "date": date,
                "product_id": product_id,
                "quantity_sold": daily_sales,
            })

    df = pd.DataFrame(sales_data)
    return df.sort_values(["product_id", "date"])


if __name__ == "__main__":
    # Generate sales history for products in sample_inventory.csv
    import os
    script_dir = os.path.dirname(os.path.abspath(__file__))
    inventory_path = os.path.join(script_dir, "sample_inventory.csv")
    inventory_df = pd.read_csv(inventory_path)
    product_ids = inventory_df["product_id"].unique().tolist()

    print(f"Generating sales history for {len(product_ids)} products...")
    sales_df = generate_sales_history(
        product_ids=product_ids,
        start_date="2023-01-01",
        end_date="2024-12-31",
    )

    output_path = os.path.join(script_dir, "sales_history.csv")
    sales_df.to_csv(output_path, index=False)
    print(f"Generated {len(sales_df)} sales records")
    print(f"Saved to {output_path}")
    print("\nFirst few rows:")
    print(sales_df.head(10))

