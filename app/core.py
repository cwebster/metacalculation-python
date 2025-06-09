import numpy as np
import pandas as pd
from app.models import UncertaintyResult
from io import StringIO
from fastapi import HTTPException

WEIGHTS = {"A": 4, "B": 2, "C": 1, "D": 0}
BOOT_LIMIT = 10
BOOT_N = 999

# === Core math helpers ===
def weighted_median(values: np.ndarray, weights: np.ndarray, interpolate: bool = True) -> float:
    """
    Weighted median matching matrixStats::weightedMedian (R) with interpolate=True, ties="weighted".
    """
    values = np.asarray(values, dtype=float)
    weights = np.asarray(weights, dtype=float)
    if values.size == 0:
        raise ValueError("No data points for weighted median")
    # Negative weights are treated as zero
    weights = np.where(weights < 0, 0, weights)
    # If all weights are zero, return nan
    if np.all(weights == 0):
        return float("nan")
    # If any weights are infinite, only consider those
    if np.any(np.isinf(weights)):
        inf_mask = np.isinf(weights)
        values = values[inf_mask]
        weights = np.ones_like(values)
    # Remove NaNs (optional, if you want to match na.rm=TRUE)
    mask = ~np.isnan(values) & ~np.isnan(weights)
    values = values[mask]
    weights = weights[mask]
    if values.size == 0:
        return float("nan")
    # Sort values and weights by value
    sorter = np.argsort(values)
    v = values[sorter]
    w = weights[sorter]
    total = w.sum()
    if v.size == 1:
        return float(v[0])
    # Normalize weights
    w = w / total
    # Centered cumulative weights
    wcum = np.cumsum(w) - w / 2
    # Find first index where wcum >= 0.5
    idx = np.searchsorted(wcum, 0.5)
    if idx == 0 or idx == v.size:
        return float(v[idx])
    # Interpolation as in C code
    if interpolate:
        dx = v[idx] - v[idx-1]
        Dy = wcum[idx] - wcum[idx-1]
        dy = 0.5 - wcum[idx]
        if Dy == 0:
            return float(v[idx])
        dx = (dy / Dy) * dx
        return float(dx + v[idx])
    else:
        return float(v[idx])

def trunc_testdata(data) -> pd.DataFrame:
    """
    Accepts either CSV text or a DataFrame.
    """

    if isinstance(data, str):
        try:
            df = pd.read_csv(StringIO(data), sep=",", header=0, skip_blank_lines=True)
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Invalid CSV input: {e}")
    elif isinstance(data, pd.DataFrame):
        df = data.copy()
    else:
        raise HTTPException(status_code=400, detail="Input must be CSV text or DataFrame")
    df = df.dropna()
    if "Include" not in df.columns:
        raise HTTPException(status_code=400, detail="'Include' column missing")
    # Accept boolean True or string "TRUE" (case-insensitive)
    mask = (df["Include"] == True) | (df["Include"].astype(str).str.upper() == "TRUE")
    df = df[mask].copy()

    # compute CI width weight
    df["ci_weight"] = 1.0 / (df["CI_upper"] - df["CI_lower"])

    # aggregate by ID, taking highest Score first
    grouped = df.sort_values(["ID", "Score"], ascending=[True, False]).groupby("ID", group_keys=False)
    def agg_fn(g):
        return pd.Series({
            "Score": g["Score"].iloc[0],
            "CV": weighted_median(g["CV"].values, g["ci_weight"].values),
            "CI_lower": weighted_median(g["CI_lower"].values, g["ci_weight"].values),
            "CI_upper": weighted_median(g["CI_upper"].values, g["ci_weight"].values),
        })
    trunc = grouped.apply(agg_fn).reset_index()

    # recompute weights for meta calculation
    trunc["ci_weight"] = 1.0 / (trunc["CI_upper"] - trunc["CI_lower"])
    trunc["score_weight"] = trunc["Score"].map(WEIGHTS).fillna(0)
    trunc["tot_weight"] = trunc["ci_weight"] * trunc["score_weight"]

    return trunc

from typing import Optional

def calc_median_uncertainty(df: pd.DataFrame, seed: Optional[int] = None) -> UncertaintyResult:
    """
    Replicates calc_median_uncertainty from R:
    - if n == 0: returns N=0 with nulls
    - if n == 1: returns that single CV & CI
    - if n <= BOOT_LIMIT: weighted median + min/max
    - else: bootstrap percentile CI (R type='perc', quantile type=7)
    """
    n = len(df)
    if n == 0:
        return UncertaintyResult(
            N=0, **{"W.Median": None, "Range_lower": None, "Range_upper": None}
        )
    if n == 1:
        row = df.iloc[0]
        return UncertaintyResult(
            N=1,
            **{
                "W.Median": float(row["CV"]),
                "Range_lower": float(row["CI_lower"]),
                "Range_upper": float(row["CI_upper"]),
            }
        )

    est = weighted_median(df["CV"].to_numpy(), df["tot_weight"].to_numpy())

    if n <= BOOT_LIMIT:
        return UncertaintyResult(
            N=n,
            **{
                "W.Median": est,
                "Range_lower": float(df["CV"].min()),
                "Range_upper": float(df["CV"].max()),
            }
        )

    # --- Bootstrapping (index-based, R-style) ---
    rng = np.random.default_rng(seed)
    boot_meds = []
    for _ in range(BOOT_N):
        idxs = rng.integers(0, n, n)
        sample_cv = df["CV"].values[idxs]
        sample_weights = df["tot_weight"].values[idxs]
        boot_meds.append(weighted_median(sample_cv, sample_weights))

    # Match R's quantile type=7 as closely as possible
    np_version = tuple(map(int, np.__version__.split('.')[:2]))
    if np_version >= (1, 22):
        lower = float(np.percentile(boot_meds, 2.5, method="linear"))
        upper = float(np.percentile(boot_meds, 97.5, method="linear"))
    else:
        boot_meds_arr = np.array(boot_meds)
        lower = float(np.percentile(boot_meds_arr, 2.5, method="linear"))
        upper = float(np.percentile(boot_meds_arr, 97.5, method="linear"))

    return UncertaintyResult(
        N=n, **{"W.Median": est, "Range_lower": lower, "Range_upper": upper}
    )