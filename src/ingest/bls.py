from __future__ import annotations

import pandas as pd

from src.db import DATA_DIR

BLS_STATE_EMPLOYMENT_2023 = {
    "AL": 2_148_000, "AK": 333_000, "AZ": 3_239_000, "AR": 1_344_000,
    "CA": 17_980_000, "CO": 2_948_000, "CT": 1_710_000, "DE": 477_000,
    "DC": 815_000, "FL": 9_966_000, "GA": 4_879_000, "HI": 643_000,
    "ID": 822_000, "IL": 6_169_000, "IN": 3_222_000, "IA": 1_607_000,
    "KS": 1_440_000, "KY": 2_018_000, "LA": 1_976_000, "ME": 651_000,
    "MD": 2_807_000, "MA": 3_722_000, "MI": 4_504_000, "MN": 2_999_000,
    "MS": 1_181_000, "MO": 2_960_000, "MT": 510_000, "NE": 1_038_000,
    "NV": 1_511_000, "NH": 705_000, "NJ": 4_309_000, "NM": 870_000,
    "NY": 9_898_000, "NC": 4_809_000, "ND": 432_000, "OH": 5_654_000,
    "OK": 1_751_000, "OR": 1_999_000, "PA": 6_103_000, "RI": 510_000,
    "SC": 2_336_000, "SD": 462_000, "TN": 3_245_000, "TX": 14_180_000,
    "UT": 1_727_000, "VT": 313_000, "VA": 4_154_000, "WA": 3_677_000,
    "WV": 716_000, "WI": 3_018_000, "WY": 295_000,
}

BLS_STATE_GROWTH_2023_2032 = {
    "AL": 0.005, "AK": 0.003, "AZ": 0.013, "AR": 0.005, "CA": 0.007,
    "CO": 0.011, "CT": 0.003, "DE": 0.006, "DC": 0.005, "FL": 0.014,
    "GA": 0.011, "HI": 0.005, "ID": 0.013, "IL": 0.002, "IN": 0.005,
    "IA": 0.004, "KS": 0.004, "KY": 0.004, "LA": 0.002, "ME": 0.003,
    "MD": 0.006, "MA": 0.006, "MI": 0.003, "MN": 0.006, "MS": 0.003,
    "MO": 0.004, "MT": 0.007, "NE": 0.005, "NV": 0.013, "NH": 0.005,
    "NJ": 0.005, "NM": 0.004, "NY": 0.004, "NC": 0.012, "ND": 0.004,
    "OH": 0.003, "OK": 0.005, "OR": 0.008, "PA": 0.003, "RI": 0.003,
    "SC": 0.011, "SD": 0.005, "TN": 0.011, "TX": 0.014, "UT": 0.012,
    "VT": 0.002, "VA": 0.007, "WA": 0.010, "WV": -0.002, "WI": 0.005,
    "WY": 0.003,
}

PROJECTION_YEARS = (2023, 2028, 2033, 2038, 2043, 2048, 2053, 2058)


def build_employment_projections() -> pd.DataFrame:
    rows = []
    for state in BLS_STATE_EMPLOYMENT_2023:
        base = BLS_STATE_EMPLOYMENT_2023[state]
        g = BLS_STATE_GROWTH_2023_2032[state]
        for y in PROJECTION_YEARS:
            emp = base * (1 + g) ** (y - 2023)
            rows.append({
                "state_code": state,
                "year": y,
                "total_employment": max(int(round(emp)), 0),
                "source": "BLS_CES_2023_plus_EP_2022_2032",
            })
    return pd.DataFrame(rows)


if __name__ == "__main__":
    df = build_employment_projections()
    out = DATA_DIR / "employment_projections.csv"
    df.to_csv(out, index=False)
    print(f"Wrote {len(df):,} rows to {out}")
    print(f"2023 national total: {df[df.year==2023].total_employment.sum():,}")
