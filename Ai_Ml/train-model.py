"""
Trains and evaluates two candidate models for predicting a student's final
grade (G3) from studytime, G1 (midterm), and G2 (preboard):

  - Linear Regression: simple, interpretable baseline
  - Random Forest: handles any non-linear relationship between the features

Both are evaluated on a held-out test split using R^2, MAE, MSE, and RMSE.
The better-performing model (by R^2 on the test set) is saved as the one
Django will load; both are saved regardless so the choice is inspectable
and swappable later without retraining.
"""

import json
import joblib
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestRegressor
from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.model_selection import train_test_split

DATA_PATH = "datasets/prepared_data.csv"
MODELS_DIR = "models"
RANDOM_STATE = 42

FEATURES = ["studytime", "G1", "G2"]
TARGET = "G3"


def evaluate(model, X_test, y_test, name):
    predictions = model.predict(X_test)
    r2 = r2_score(y_test, predictions)
    mae = mean_absolute_error(y_test, predictions)
    mse = mean_squared_error(y_test, predictions)
    rmse = np.sqrt(mse)

    print(f"\n{name}")
    print(f"  R^2:  {r2:.4f}")
    print(f"  MAE:  {mae:.4f}")
    print(f"  MSE:  {mse:.4f}")
    print(f"  RMSE: {rmse:.4f}")

    return {"model": name, "r2": round(r2, 4), "mae": round(mae, 4),
            "mse": round(mse, 4), "rmse": round(rmse, 4)}


def train_and_evaluate():
    df = pd.read_csv(DATA_PATH)
    X = df[FEATURES]
    y = df[TARGET]

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=RANDOM_STATE
    )
    print(f"Train size: {len(X_train)}, Test size: {len(X_test)}")

    linear_model = LinearRegression()
    linear_model.fit(X_train, y_train)
    linear_results = evaluate(linear_model, X_test, y_test, "Linear Regression")

    forest_model = RandomForestRegressor(n_estimators=200, random_state=RANDOM_STATE)
    forest_model.fit(X_train, y_train)
    forest_results = evaluate(forest_model, X_test, y_test, "Random Forest")

    results = [linear_results, forest_results]
    best = max(results, key=lambda r: r["r2"])
    print(f"\nBest model by R^2 on test set: {best['model']}")

    joblib.dump(linear_model, f"{MODELS_DIR}/linear_regression.pkl")
    joblib.dump(forest_model, f"{MODELS_DIR}/random_forest.pkl")

    best_model = linear_model if best["model"] == "Linear Regression" else forest_model
    joblib.dump(best_model, f"{MODELS_DIR}/best_model.pkl")

    with open(f"{MODELS_DIR}/evaluation_results.json", "w") as f:
        json.dump({"results": results, "best_model": best["model"], "features": FEATURES}, f, indent=2)

    print(f"\nSaved: {MODELS_DIR}/linear_regression.pkl")
    print(f"Saved: {MODELS_DIR}/random_forest.pkl")
    print(f"Saved: {MODELS_DIR}/best_model.pkl  (<- this is what Django will load))")
    print(f"Saved: {MODELS_DIR}/evaluation_results.json")

    return results


if __name__ == "__main__":
    train_and_evaluate()