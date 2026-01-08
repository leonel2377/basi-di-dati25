# Inventory Tracker with Dynamic Reorder Alerts

This project provides a Python-based tool for tracking inventory levels, identifying stock shortages, and triggering reorder workflows. It loads product data from CSV files, evaluates each item against configurable thresholds, and visualizes stock status with color-coded dashboards.

## Features

- Load inventory data from CSV using `pandas`
- Classify item stock levels into `GREEN`, `ORANGE`, and `RED` zones
- Prompt the user to confirm reorders for low-stock items
- Automatically mark critical items for immediate reorder
- Display textual summaries and bar chart visualizations with `matplotlib`/`seaborn`
- Includes sample inventory data and unit tests for the classification logic
- **🔬 Machine Learning Features** (NEW):
  - Predict future stock levels/demand from sales history using Random Forest, XGBoost, or LSTM
  - Predict optimal reorder quantities based on demand patterns
  - Classify products by demand volatility for inventory strategy

## Quick Start

1. **Install dependencies**

   ```bash
   python -m venv .venv
   .venv\Scripts\activate  # Windows
   pip install -r requirements.txt
   ```

2. **Run the application**

   ```bash
   python main.py
   ```

  Use `python main.py --help` to see additional options such as:
  - `--inventory path/to/file.csv` to load another dataset
  - `--save-plot output.png` to export the bar chart
  - `--no-show-plot` to skip interactive display (headless mode)
  - `--orange-strategy {prompt,auto-confirm,auto-decline}` to control low-stock handling
  - `--enable-ml` to activate ML predictions for demand forecasting
  - `--ml-model {random_forest,xgboost,lstm}` to choose ML model type
  - `--sales-history path/to/sales.csv` to specify sales history file

### ML Features Usage

First, generate sales history data:
```bash
python data/generate_sales_history.py
```

Then run with ML predictions:
```bash
# With Random Forest (default)
python main.py --enable-ml --orange-strategy auto-confirm --no-show-plot

# With XGBoost
python main.py --enable-ml --ml-model xgboost --orange-strategy auto-confirm

# With LSTM
python main.py --enable-ml --ml-model lstm --orange-strategy auto-confirm
```

See [ML_FEATURES.md](ML_FEATURES.md) for detailed ML documentation.

3. **Run tests**

   ```bash
   pytest
   ```

## CSV Format

The inventory CSV file must provide the following columns:

- `product_id`
- `product_name`
- `category`
- `quantity`
- `reorder_point`
- `critical_point`
- `reorder_quantity` (optional but used when reorders are applied)

Sample data is provided in `data/sample_inventory.csv`.

## ML Features Details

The project includes advanced Machine Learning capabilities:

1. **Demand Forecasting**: Predicts future stock levels using historical sales data
   - Models: Random Forest, XGBoost, LSTM
   - Features: Rolling statistics, temporal patterns, product encoding

2. **Optimal Reorder Quantity Prediction**: Calculates optimal reorder amounts based on:
   - Predicted demand during lead time
   - Safety stock calculations
   - Product volatility classification

3. **Volatility Classification**: Classifies products as low/medium/high volatility
   - Based on coefficient of variation
   - Informs inventory strategy and safety stock levels

See [ML_FEATURES.md](ML_FEATURES.md) for comprehensive documentation.

## Stretch Goals

- Generate automated PDF or HTML reports summarizing daily inventory status
- Integrate with supplier APIs to submit reorders directly
- Add a lightweight GUI to complement the CLI prompts
- Expand ML features with more models and advanced features

