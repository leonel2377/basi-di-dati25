"""
Machine Learning modules for demand prediction and inventory optimization.

Implements:
- Demand forecasting using Random Forest, XGBoost, and LSTM
- Optimal reorder quantity prediction
- Product volatility classification
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Literal, Optional

import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder, StandardScaler

try:
    import xgboost as xgb
    XGBOOST_AVAILABLE = True
except ImportError:
    XGBOOST_AVAILABLE = False

try:
    from tensorflow import keras
    from tensorflow.keras import layers
    TENSORFLOW_AVAILABLE = True
except ImportError:
    TENSORFLOW_AVAILABLE = False


@dataclass
class DemandPrediction:
    """Result of demand prediction for a product."""

    product_id: str
    predicted_demand: float
    confidence_interval_lower: float
    confidence_interval_upper: float
    model_used: str
    volatility_class: str


@dataclass
class OptimalReorderPrediction:
    """Optimal reorder quantity prediction."""

    product_id: str
    current_quantity: int
    predicted_demand: float
    optimal_reorder_quantity: int
    rationale: str


class DemandPredictor:
    """
    Machine Learning models for predicting future demand and stock levels.
    """

    def __init__(
        self,
        model_type: Literal["random_forest", "xgboost", "lstm"] = "random_forest",
    ) -> None:
        """
        Initialize demand predictor with specified model type.

        Parameters
        ----------
        model_type
            Type of ML model to use: 'random_forest', 'xgboost', or 'lstm'
        """
        self.model_type = model_type
        self.model: Optional[object] = None
        self.scaler = StandardScaler()
        self.label_encoder = LabelEncoder()
        self.is_trained = False

        if model_type == "xgboost" and not XGBOOST_AVAILABLE:
            raise ImportError(
                "XGBoost not available. Install with: pip install xgboost"
            )
        if model_type == "lstm" and not TENSORFLOW_AVAILABLE:
            raise ImportError(
                "TensorFlow not available. Install with: pip install tensorflow"
            )

    def train(
        self,
        sales_history: pd.DataFrame,
        target_column: str = "quantity_sold",
        test_size: float = 0.2,
    ) -> dict[str, float]:
        """
        Train the demand prediction model on historical sales data.

        Parameters
        ----------
        sales_history
            DataFrame with columns: date, product_id, quantity_sold, and features
        target_column
            Name of the target column to predict
        test_size
            Proportion of data to use for testing

        Returns
        -------
        Dictionary with training metrics (train_score, test_score)
        """
        if sales_history.empty:
            raise ValueError("Sales history DataFrame is empty")

        # Prepare features
        df = sales_history.copy()
        df["date"] = pd.to_datetime(df["date"])
        df["day_of_week"] = df["date"].dt.dayofweek
        df["month"] = df["date"].dt.month
        df["year"] = df["date"].dt.year

        # Encode categorical features
        if "product_id" in df.columns:
            df["product_id_encoded"] = self.label_encoder.fit_transform(
                df["product_id"]
            )

        # Feature engineering: rolling statistics
        df = df.sort_values(["product_id", "date"])
        for window in [7, 30]:
            df[f"rolling_mean_{window}"] = (
                df.groupby("product_id")[target_column]
                .rolling(window=window, min_periods=1)
                .mean()
                .reset_index(0, drop=True)
            )
            df[f"rolling_std_{window}"] = (
                df.groupby("product_id")[target_column]
                .rolling(window=window, min_periods=1)
                .std()
                .fillna(0)
                .reset_index(0, drop=True)
            )

        # Select features
        feature_columns = [
            "day_of_week",
            "month",
            "year",
            "rolling_mean_7",
            "rolling_mean_30",
            "rolling_std_7",
            "rolling_std_30",
        ]
        if "product_id_encoded" in df.columns:
            feature_columns.append("product_id_encoded")

        X = df[feature_columns].fillna(0)
        y = df[target_column]

        # Split data
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=test_size, random_state=42, shuffle=False
        )

        # Scale features
        X_train_scaled = self.scaler.fit_transform(X_train)
        X_test_scaled = self.scaler.transform(X_test)

        # Train model based on type
        if self.model_type == "random_forest":
            self.model = RandomForestRegressor(n_estimators=100, random_state=42, n_jobs=-1)
            self.model.fit(X_train_scaled, y_train)
            train_score = self.model.score(X_train_scaled, y_train)
            test_score = self.model.score(X_test_scaled, y_test)

        elif self.model_type == "xgboost":
            if not XGBOOST_AVAILABLE:
                raise ImportError("XGBoost not available")
            self.model = xgb.XGBRegressor(n_estimators=100, random_state=42)
            self.model.fit(X_train_scaled, y_train)
            train_score = self.model.score(X_train_scaled, y_train)
            test_score = self.model.score(X_test_scaled, y_test)

        elif self.model_type == "lstm":
            if not TENSORFLOW_AVAILABLE:
                raise ImportError("TensorFlow not available")
            # Reshape for LSTM: (samples, timesteps, features)
            # For simplicity, use sequence length of 1 (can be improved)
            X_train_lstm = X_train_scaled.reshape(X_train_scaled.shape[0], 1, X_train_scaled.shape[1])
            X_test_lstm = X_test_scaled.reshape(X_test_scaled.shape[0], 1, X_test_scaled.shape[1])

            self.model = keras.Sequential([
                layers.LSTM(50, activation='relu', input_shape=(1, X_train_scaled.shape[1])),
                layers.Dense(25, activation='relu'),
                layers.Dense(1)
            ])
            self.model.compile(optimizer='adam', loss='mse', metrics=['mae'])
            self.model.fit(
                X_train_lstm, y_train,
                epochs=20,
                batch_size=32,
                validation_data=(X_test_lstm, y_test),
                verbose=0
            )
            train_score = self.model.evaluate(X_train_lstm, y_train, verbose=0)[1]
            test_score = self.model.evaluate(X_test_lstm, y_test, verbose=0)[1]

        self.is_trained = True
        return {"train_score": float(train_score), "test_score": float(test_score)}

    def predict_demand(
        self,
        product_id: str,
        current_date: pd.Timestamp,
        historical_data: pd.DataFrame,
        days_ahead: int = 30,
    ) -> DemandPrediction:
        """
        Predict future demand for a product.

        Parameters
        ----------
        product_id
            ID of the product to predict
        current_date
            Current date for prediction
        historical_data
            Historical sales data for feature calculation
        days_ahead
            Number of days ahead to predict

        Returns
        -------
        DemandPrediction with predicted demand and confidence intervals
        """
        if not self.is_trained:
            raise ValueError("Model must be trained before making predictions")

        # Prepare features for prediction
        pred_date = current_date + pd.Timedelta(days=days_ahead)
        product_history = historical_data[historical_data["product_id"] == product_id].copy()

        if product_history.empty:
            # If no history, return default prediction
            return DemandPrediction(
                product_id=product_id,
                predicted_demand=10.0,
                confidence_interval_lower=5.0,
                confidence_interval_upper=15.0,
                model_used=self.model_type,
                volatility_class="unknown",
            )

        # Calculate rolling statistics
        product_history = product_history.sort_values("date")
        recent_mean = product_history["quantity_sold"].tail(30).mean() if len(product_history) >= 30 else product_history["quantity_sold"].mean()
        recent_std = product_history["quantity_sold"].tail(30).std() if len(product_history) >= 30 else product_history["quantity_sold"].std()

        # Create feature vector
        features = pd.DataFrame({
            "day_of_week": [pred_date.dayofweek],
            "month": [pred_date.month],
            "year": [pred_date.year],
            "rolling_mean_7": [recent_mean],
            "rolling_mean_30": [recent_mean],
            "rolling_std_7": [recent_std if not pd.isna(recent_std) else 0],
            "rolling_std_30": [recent_std if not pd.isna(recent_std) else 0],
            "product_id_encoded": [
                self.label_encoder.transform([product_id])[0]
                if product_id in self.label_encoder.classes_
                else 0
            ],
        })

        # Scale and predict
        features_scaled = self.scaler.transform(features)

        if self.model_type == "lstm":
            features_lstm = features_scaled.reshape(1, 1, features_scaled.shape[1])
            prediction = float(self.model.predict(features_lstm, verbose=0)[0, 0])
        else:
            prediction = float(self.model.predict(features_scaled)[0])

        # Calculate confidence intervals (simple approximation)
        std_dev = recent_std if not pd.isna(recent_std) else prediction * 0.2
        confidence_lower = max(0, prediction - 1.96 * std_dev)
        confidence_upper = prediction + 1.96 * std_dev

        # Classify volatility
        cv = (recent_std / recent_mean) if recent_mean > 0 else 0
        if cv < 0.2:
            volatility = "low"
        elif cv < 0.5:
            volatility = "medium"
        else:
            volatility = "high"

        return DemandPrediction(
            product_id=product_id,
            predicted_demand=prediction,
            confidence_interval_lower=confidence_lower,
            confidence_interval_upper=confidence_upper,
            model_used=self.model_type,
            volatility_class=volatility,
        )


def predict_optimal_reorder_quantity(
    product_id: str,
    current_quantity: int,
    demand_prediction: DemandPrediction,
    reorder_point: int,
    critical_point: int,
    lead_time_days: int = 7,
    safety_stock_factor: float = 1.5,
) -> OptimalReorderPrediction:
    """
    Predict optimal reorder quantity based on demand forecast.

    Parameters
    ----------
    product_id
        Product ID
    current_quantity
        Current stock quantity
    demand_prediction
        Predicted demand from ML model
    reorder_point
        Current reorder point threshold
    critical_point
        Current critical point threshold
    lead_time_days
        Expected lead time for delivery in days
    safety_stock_factor
        Safety factor for safety stock calculation

    Returns
    -------
    OptimalReorderPrediction with recommended reorder quantity
    """
    # Calculate demand during lead time
    daily_demand = demand_prediction.predicted_demand / 30  # Assume monthly prediction
    lead_time_demand = daily_demand * lead_time_days

    # Calculate safety stock
    demand_std = (demand_prediction.confidence_interval_upper - demand_prediction.predicted_demand) / 1.96
    safety_stock = safety_stock_factor * demand_std * np.sqrt(lead_time_days)

    # Optimal order quantity formula: EOQ-like approach with demand forecast
    target_stock = lead_time_demand + safety_stock + reorder_point
    optimal_quantity = max(0, int(target_stock - current_quantity))

    # Adjust based on volatility
    if demand_prediction.volatility_class == "high":
        optimal_quantity = int(optimal_quantity * 1.2)  # Increase for high volatility
    elif demand_prediction.volatility_class == "low":
        optimal_quantity = int(optimal_quantity * 0.9)  # Decrease for low volatility

    rationale = (
        f"Based on {demand_prediction.model_used} model: "
        f"predicted demand={demand_prediction.predicted_demand:.1f}/month, "
        f"volatility={demand_prediction.volatility_class}, "
        f"lead_time_demand={lead_time_demand:.1f}, safety_stock={safety_stock:.1f}"
    )

    return OptimalReorderPrediction(
        product_id=product_id,
        current_quantity=current_quantity,
        predicted_demand=demand_prediction.predicted_demand,
        optimal_reorder_quantity=max(optimal_quantity, reorder_point - current_quantity),
        rationale=rationale,
    )


def classify_product_volatility(sales_history: pd.DataFrame) -> pd.DataFrame:
    """
    Classify products by demand volatility based on historical sales.

    Parameters
    ----------
    sales_history
        DataFrame with columns: product_id, date, quantity_sold

    Returns
    -------
    DataFrame with product_id and volatility_class columns
    """
    df = sales_history.copy()
    df["date"] = pd.to_datetime(df["date"])

    volatility_data = []
    for product_id in df["product_id"].unique():
        product_data = df[df["product_id"] == product_id].sort_values("date")
        if len(product_data) < 7:
            volatility_class = "insufficient_data"
        else:
            mean_sales = product_data["quantity_sold"].mean()
            std_sales = product_data["quantity_sold"].std()
            cv = (std_sales / mean_sales) if mean_sales > 0 else float("inf")

            if cv < 0.2:
                volatility_class = "low"
            elif cv < 0.5:
                volatility_class = "medium"
            else:
                volatility_class = "high"

        volatility_data.append({
            "product_id": product_id,
            "volatility_class": volatility_class,
            "coefficient_of_variation": cv if mean_sales > 0 else 0,
            "mean_demand": mean_sales,
            "std_demand": std_sales if not pd.isna(std_sales) else 0,
        })

    return pd.DataFrame(volatility_data)

