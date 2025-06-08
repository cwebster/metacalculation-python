from fastapi import FastAPI, Body, HTTPException
from app.models import UncertaintyResult
import pandas as pd
import numpy as np
from io import StringIO

app = FastAPI()

# === Configuration constants ===
WEIGHTS   = {"A": 4, "B": 2, "C": 1, "D": 0}
BOOT_LIMIT = 10
BOOT_N     = 999

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

def trunc_testdata(csv_text: str) -> pd.DataFrame:
    """
    Replicates trunc_testdata.R:
    - reads CSV from the raw text body
    - filters Include == TRUE
    - groups by ID, takes highest-Score row then weighted medians of CV and CI bounds
    - recomputes ci_weight, score_weight, tot_weight
    """
    try:
        df = pd.read_csv(StringIO(csv_text), sep=",", header=0, skip_blank_lines=True)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Invalid CSV input: {e}")
    # drop any NA
    df = df.dropna()
    df = df[df["Include"] == True]

    # compute CI width weight
    df["ci_weight"] = 1.0 / (df["CI_upper"] - df["CI_lower"])

    # aggregate by ID, taking highest Score first
    grouped = (
        df.sort_values(["ID", "Score"], ascending=[True, False])
          .groupby("ID")
    )
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

def calc_median_uncertainty(df: pd.DataFrame) -> UncertaintyResult:
    """
    Replicates calc_median_uncertainty from R:
    - if n == 0: returns N=0 with nulls
    - if n == 1: returns that single CV & CI
    - if n <= BOOT_LIMIT: weighted median + min/max
    - else: bootstrap percentile CI (R type='perc')
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

    est = weighted_median(df["CV"].values, df["tot_weight"].values)

    if n <= BOOT_LIMIT:
        return UncertaintyResult(
            N=n,
            **{
                "W.Median": est,
                "Range_lower": float(df["CV"].min()),
                "Range_upper": float(df["CV"].max()),
            }
        )

    # bootstrap
    boot_meds = []
    for _ in range(BOOT_N):
        sample = df.sample(n=n, replace=True)
        boot_meds.append(
            weighted_median(sample["CV"].values, sample["tot_weight"].values)
        )
    lower = float(np.percentile(boot_meds, 2.5))
    upper = float(np.percentile(boot_meds, 97.5))
    return UncertaintyResult(
        N=n, **{"W.Median": est, "Range_lower": lower, "Range_upper": upper}
    )

# === FastAPI endpoints ===
@app.get("/health")
def health():
    return "OK"

@app.post("/metacalculation", response_model=UncertaintyResult)
def metacalculation(body: str = Body(..., media_type="text/plain")):
    df = trunc_testdata(body)
    return calc_median_uncertainty(df)
