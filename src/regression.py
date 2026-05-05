from __future__ import annotations

import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestRegressor
from sklearn.linear_model import Ridge
from sklearn.metrics import mean_absolute_percentage_error, r2_score
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder

CATEGORICAL_FEATURES_FERTILITY = ["region", "race", "origin", "age_group"]
CATEGORICAL_FEATURES_OTHERS = ["region", "race", "origin", "sex", "age_group"]


def _encode(df: pd.DataFrame, features: list[str]) -> tuple[np.ndarray, OneHotEncoder]:
    enc = OneHotEncoder(sparse_output=False, handle_unknown="ignore")
    X = enc.fit_transform(df[features])
    return X, enc


def evaluate_imputation(rates: pd.DataFrame, target_col: str, features: list[str],
                        states_df: pd.DataFrame, mask_frac: float = 0.10,
                        seed: int = 210) -> dict:
    df = rates.merge(states_df[["state_code", "region"]], on="state_code", how="left")
    df = df.dropna(subset=[target_col]).reset_index(drop=True)

    rng = np.random.default_rng(seed)
    mask = rng.random(len(df)) < mask_frac
    train = df[~mask].copy()
    test = df[mask].copy()

    enc = OneHotEncoder(sparse_output=False, handle_unknown="ignore")
    X_train = enc.fit_transform(train[features])
    X_test = enc.transform(test[features])
    y_train = train[target_col].values
    y_test = test[target_col].values

    model = Ridge(alpha=1.0)
    model.fit(X_train, y_train)
    y_pred = model.predict(X_test)
    y_pred = np.clip(y_pred, 0, None)

    r2 = r2_score(y_test, y_pred)
    nonzero = y_test > 1e-9
    mape = (
        mean_absolute_percentage_error(y_test[nonzero], y_pred[nonzero])
        if nonzero.any() else float("nan")
    )

    return {
        "target": target_col,
        "n_train": len(train),
        "n_test": len(test),
        "mask_frac": mask_frac,
        "r2": r2,
        "mape": mape,
        "model": model,
        "encoder": enc,
        "feature_names": enc.get_feature_names_out(features).tolist(),
        "y_test": y_test,
        "y_pred": y_pred,
    }


MIGRATION_CATEGORICAL_FEATURES = ["region", "race", "origin", "sex", "age_group"]
MIGRATION_NUMERIC_FEATURES = ["employment_growth"]


def _build_migration_features(migration: pd.DataFrame, states: pd.DataFrame,
                              employment: pd.DataFrame) -> pd.DataFrame:
    emp_2023 = employment[employment["year"] == 2023].set_index("state_code")["total_employment"]
    emp_2028 = employment[employment["year"] == 2028].set_index("state_code")["total_employment"]
    growth = ((emp_2028 / emp_2023) ** (1 / 5) - 1).rename("employment_growth")

    df = migration.merge(states[["state_code", "region"]], on="state_code", how="left")
    df = df.merge(growth, left_on="state_code", right_index=True, how="left")
    df["employment_growth"] = df["employment_growth"].fillna(0.0)
    return df


def fit_migration_model(migration: pd.DataFrame, states: pd.DataFrame,
                        employment: pd.DataFrame, n_holdout_states: int = 10,
                        seed: int = 210) -> dict:
    df = _build_migration_features(migration, states, employment)
    df = df.dropna(subset=["migration_rate"]).reset_index(drop=True)

    rng = np.random.default_rng(seed)
    all_states = sorted(df["state_code"].unique())
    holdout_states = list(rng.choice(all_states, size=n_holdout_states, replace=False))

    train = df[~df["state_code"].isin(holdout_states)].copy()
    test = df[df["state_code"].isin(holdout_states)].copy()

    enc = OneHotEncoder(sparse_output=False, handle_unknown="ignore")
    X_train_cat = enc.fit_transform(train[MIGRATION_CATEGORICAL_FEATURES])
    X_train_num = train[MIGRATION_NUMERIC_FEATURES].values
    X_train = np.hstack([X_train_cat, X_train_num])

    X_test_cat = enc.transform(test[MIGRATION_CATEGORICAL_FEATURES])
    X_test_num = test[MIGRATION_NUMERIC_FEATURES].values
    X_test = np.hstack([X_test_cat, X_test_num])

    y_train = train["migration_rate"].values
    y_test = test["migration_rate"].values

    model = RandomForestRegressor(n_estimators=100, max_depth=8, random_state=seed)
    model.fit(X_train, y_train)
    y_pred = model.predict(X_test)

    r2 = r2_score(y_test, y_pred)
    mae = float(np.mean(np.abs(y_test - y_pred)))

    feature_names = (
        list(enc.get_feature_names_out(MIGRATION_CATEGORICAL_FEATURES))
        + MIGRATION_NUMERIC_FEATURES
    )
    importances = pd.Series(model.feature_importances_, index=feature_names)
    importances = importances.sort_values(ascending=False)

    return {
        "target": "migration_rate",
        "n_train": len(train),
        "n_test": len(test),
        "holdout_states": holdout_states,
        "r2": r2,
        "mae": mae,
        "model": model,
        "encoder": enc,
        "feature_importances": importances,
        "y_test": y_test,
        "y_pred": y_pred,
    }
