import json
import math
import os
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
import torch
from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from torch import nn
from torch.utils.data import DataLoader, TensorDataset


TARGET = "Tot_Mdcr_Pymt_Amt"
DROP_ALWAYS = {
    "Rndrng_NPI",
    "Rndrng_Prvdr_Last_Org_Name",
    "Rndrng_Prvdr_First_Name",
    "Rndrng_Prvdr_MI",
    "Rndrng_Prvdr_Crdntls",
    "Rndrng_Prvdr_St1",
    "Rndrng_Prvdr_St2",
    "Rndrng_Prvdr_City",
    "Rndrng_Prvdr_Zip5",
    "Rndrng_Prvdr_RUCA_Desc",
}


class PaymentRegressor(nn.Module):
    def __init__(self, input_dim: int):
        super().__init__()
        self.net = nn.Sequential(
            nn.Linear(input_dim, 256),
            nn.ReLU(),
            nn.BatchNorm1d(256),
            nn.Dropout(0.20),
            nn.Linear(256, 128),
            nn.ReLU(),
            nn.BatchNorm1d(128),
            nn.Dropout(0.10),
            nn.Linear(128, 32),
            nn.ReLU(),
            nn.Linear(32, 1),
        )

    def forward(self, x):
        return self.net(x).squeeze(1)


def has_provider_payment_target(csv_path: str) -> bool:
    try:
        columns = pd.read_csv(csv_path, nrows=0).columns
    except Exception:
        return False
    return TARGET in {column.strip() for column in columns}


def money_to_float(series: pd.Series) -> pd.Series:
    if pd.api.types.is_numeric_dtype(series):
        return series
    return (
        series.astype(str)
        .str.replace("$", "", regex=False)
        .str.replace(",", "", regex=False)
        .str.strip()
        .replace({"": np.nan, "nan": np.nan, "NaN": np.nan})
        .astype(float)
    )


def prepare_frame(df: pd.DataFrame) -> tuple[pd.DataFrame, pd.Series, list[str], list[str]]:
    df = df.copy()
    for column in df.columns:
        if column == TARGET or any(token in column for token in ["Amt", "Chrg", "Srvcs", "Benes", "HCPCS", "RUCA"]):
            try:
                df[column] = money_to_float(df[column])
            except ValueError:
                pass

    df = df[df[TARGET].notna() & (df[TARGET] > 0)].copy()
    y = np.log1p(df[TARGET].astype(float))

    leakage_columns = {
        TARGET,
        "Tot_Mdcr_Alowd_Amt",
        "Tot_Mdcr_Stdzd_Amt",
        "Drug_Mdcr_Pymt_Amt",
        "Drug_Mdcr_Alowd_Amt",
        "Drug_Mdcr_Stdzd_Amt",
        "Med_Mdcr_Pymt_Amt",
        "Med_Mdcr_Alowd_Amt",
        "Med_Mdcr_Stdzd_Amt",
    }
    candidate_columns = [
        column for column in df.columns if column not in DROP_ALWAYS and column not in leakage_columns
    ]
    X = df[candidate_columns]
    numeric_columns = [column for column in X.columns if pd.api.types.is_numeric_dtype(X[column])]
    categorical_columns = [column for column in X.columns if column not in numeric_columns]
    return X, y, numeric_columns, categorical_columns


def build_one_hot_encoder():
    try:
        return OneHotEncoder(handle_unknown="ignore", min_frequency=25, sparse_output=False)
    except TypeError:
        return OneHotEncoder(handle_unknown="ignore", min_frequency=25, sparse=False)


def build_preprocessor(numeric_columns: list[str], categorical_columns: list[str]) -> ColumnTransformer:
    numeric_pipe = Pipeline(
        steps=[
            ("imputer", SimpleImputer(strategy="median")),
            ("scaler", StandardScaler()),
        ]
    )
    categorical_pipe = Pipeline(
        steps=[
            ("imputer", SimpleImputer(strategy="most_frequent")),
            ("onehot", build_one_hot_encoder()),
        ]
    )
    return ColumnTransformer(
        transformers=[
            ("num", numeric_pipe, numeric_columns),
            ("cat", categorical_pipe, categorical_columns),
        ],
        remainder="drop",
    )


def to_tensor_dataset(X: np.ndarray, y: pd.Series) -> TensorDataset:
    features = torch.tensor(X.astype(np.float32), dtype=torch.float32)
    target = torch.tensor(y.to_numpy(dtype=np.float32), dtype=torch.float32)
    return TensorDataset(features, target)


def train_model(model, train_loader, val_loader, epochs: int, learning_rate: float, device):
    optimizer = torch.optim.AdamW(model.parameters(), lr=learning_rate, weight_decay=1e-4)
    loss_fn = nn.SmoothL1Loss()
    best_val = math.inf
    best_state = None

    for _ in range(epochs):
        model.train()
        for xb, yb in train_loader:
            xb = xb.to(device)
            yb = yb.to(device)
            optimizer.zero_grad()
            loss = loss_fn(model(xb), yb)
            loss.backward()
            optimizer.step()

        model.eval()
        val_losses = []
        with torch.no_grad():
            for xb, yb in val_loader:
                xb = xb.to(device)
                yb = yb.to(device)
                val_losses.append(loss_fn(model(xb), yb).item())
        val_loss = float(np.mean(val_losses))
        if val_loss < best_val:
            best_val = val_loss
            best_state = {key: value.detach().cpu().clone() for key, value in model.state_dict().items()}

    if best_state is not None:
        model.load_state_dict(best_state)
    return model


def predict(model, X: np.ndarray, device) -> np.ndarray:
    model.eval()
    preds = []
    loader = DataLoader(torch.tensor(X.astype(np.float32), dtype=torch.float32), batch_size=4096)
    with torch.no_grad():
        for xb in loader:
            preds.append(model(xb.to(device)).cpu().numpy())
    return np.concatenate(preds)


def root_mean_squared_error(actual: np.ndarray, predicted: np.ndarray) -> float:
    return math.sqrt(mean_squared_error(actual, predicted))


def quantile_summary(values: np.ndarray) -> dict[str, float]:
    quantiles = np.quantile(values, [0, 0.01, 0.05, 0.5, 0.95, 0.99, 1.0])
    return {
        "min": float(quantiles[0]),
        "p01": float(quantiles[1]),
        "p05": float(quantiles[2]),
        "median": float(quantiles[3]),
        "p95": float(quantiles[4]),
        "p99": float(quantiles[5]),
        "max": float(quantiles[6]),
    }


def train_provider_payment_model(
    csv_path: str,
    output_dir: Path,
    sample_rows: int | None = None,
    epochs: int = 5,
    batch_size: int = 2048,
    learning_rate: float = 1e-3,
    seed: int = 42,
) -> dict:
    torch.manual_seed(seed)
    np.random.seed(seed)
    output_dir.mkdir(parents=True, exist_ok=True)

    nrows = sample_rows if sample_rows and sample_rows > 0 else None
    df = pd.read_csv(csv_path, low_memory=False, nrows=nrows)
    df.columns = [column.strip() for column in df.columns]
    if TARGET not in df.columns:
        raise ValueError(f"Expected target column {TARGET!r} in {csv_path}")

    X, y, numeric_columns, categorical_columns = prepare_frame(df)
    if len(X) < 100:
        raise ValueError(f"Not enough rows to train after cleaning: {len(X)}")

    X_train, X_temp, y_train, y_temp = train_test_split(X, y, test_size=0.30, random_state=seed)
    X_val, X_test, y_val, y_test = train_test_split(X_temp, y_temp, test_size=0.50, random_state=seed)

    preprocessor = build_preprocessor(numeric_columns, categorical_columns)
    X_train_np = preprocessor.fit_transform(X_train)
    X_val_np = preprocessor.transform(X_val)
    X_test_np = preprocessor.transform(X_test)

    train_loader = DataLoader(
        to_tensor_dataset(X_train_np, y_train),
        batch_size=batch_size,
        shuffle=True,
    )
    val_loader = DataLoader(
        to_tensor_dataset(X_val_np, y_val),
        batch_size=batch_size,
        shuffle=False,
    )

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    model = PaymentRegressor(input_dim=X_train_np.shape[1]).to(device)
    model = train_model(model, train_loader, val_loader, epochs, learning_rate, device)

    pred_log = predict(model, X_test_np, device)
    actual_log = y_test.to_numpy()
    pred_dollars = np.expm1(pred_log)
    actual_dollars = np.expm1(actual_log)
    clipped_pred_log = np.clip(pred_log, actual_log.min(), actual_log.max())
    clipped_pred_dollars = np.expm1(clipped_pred_log)

    absolute_errors = np.abs(actual_dollars - pred_dollars)
    clipped_absolute_errors = np.abs(actual_dollars - clipped_pred_dollars)
    metrics = {
        "rows": int(len(X)),
        "encoded_features": int(X_train_np.shape[1]),
        "sample_rows": int(nrows or len(df)),
        "epochs": int(epochs),
        "mae_log": float(mean_absolute_error(actual_log, pred_log)),
        "rmse_log": float(root_mean_squared_error(actual_log, pred_log)),
        "r2_log": float(r2_score(actual_log, pred_log)),
        "mae": float(mean_absolute_error(actual_dollars, pred_dollars)),
        "rmse": float(root_mean_squared_error(actual_dollars, pred_dollars)),
        "median_absolute_error": float(np.median(absolute_errors)),
        "clipped_mae": float(mean_absolute_error(actual_dollars, clipped_pred_dollars)),
        "clipped_rmse": float(root_mean_squared_error(actual_dollars, clipped_pred_dollars)),
        "clipped_median_absolute_error": float(np.median(clipped_absolute_errors)),
        "actual_dollar_quantiles": quantile_summary(actual_dollars),
        "predicted_dollar_quantiles": quantile_summary(pred_dollars),
        "absolute_error_quantiles": quantile_summary(absolute_errors),
        "device": str(device),
    }

    model_path = output_dir / "model.pt"
    preprocessor_path = output_dir / "preprocessor.joblib"
    metrics_path = output_dir / "metrics.json"
    feature_columns_path = output_dir / "feature_columns.json"
    torch.save(
        {
            "model_state_dict": model.cpu().state_dict(),
            "input_dim": X_train_np.shape[1],
            "target": TARGET,
        },
        model_path,
    )
    joblib.dump(preprocessor, preprocessor_path)
    metrics_path.write_text(json.dumps(metrics, indent=2), encoding="utf-8")
    feature_columns_path.write_text(
        json.dumps(
            {
                "target": TARGET,
                "numeric_columns": numeric_columns,
                "categorical_columns": categorical_columns,
            },
            indent=2,
        ),
        encoding="utf-8",
    )

    return {
        "metrics": metrics,
        "model_uri": str(model_path),
        "preprocessor_uri": str(preprocessor_path),
        "metrics_uri": str(metrics_path),
        "feature_columns_uri": str(feature_columns_path),
    }


def training_settings_from_env() -> dict:
    return {
        "sample_rows": int(os.getenv("TRAINING_SAMPLE_ROWS", "200000")),
        "epochs": int(os.getenv("TRAINING_EPOCHS", "5")),
        "batch_size": int(os.getenv("TRAINING_BATCH_SIZE", "2048")),
        "learning_rate": float(os.getenv("TRAINING_LEARNING_RATE", "0.001")),
        "seed": int(os.getenv("TRAINING_SEED", "42")),
    }

