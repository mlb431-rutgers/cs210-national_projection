from __future__ import annotations

from pathlib import Path

import pandas as pd
import requests

from src.db import DATA_DIR
from src.ingest.harmonize import (
    CENSUS_B03002,
    STATE_FIPS_TO_CODE,
    census_to_race_origin_shares,
)

ACS_URL = "https://api.census.gov/data/{year}/acs/acs1"
RAW_DIR = DATA_DIR / "raw"

AGE_SHARES = {
    "0-4": 0.058, "5-9": 0.060, "10-14": 0.064, "15-19": 0.064, "20-24": 0.066,
    "25-29": 0.070, "30-34": 0.070, "35-39": 0.068, "40-44": 0.063, "45-49": 0.060,
    "50-54": 0.064, "55-59": 0.067, "60-64": 0.064, "65-69": 0.054, "70-74": 0.045,
    "75-79": 0.032, "80-84": 0.020, "85+": 0.021,
}


def fetch_b03002(year: int = 2023) -> pd.DataFrame:
    fields = "NAME," + ",".join(CENSUS_B03002.values())
    url = f"{ACS_URL.format(year=year)}?get={fields}&for=state:*"
    cache = RAW_DIR / f"census_b03002_{year}.csv"
    cache.parent.mkdir(parents=True, exist_ok=True)

    if cache.exists():
        return pd.read_csv(cache, dtype={"state": str})

    resp = requests.get(url, timeout=20)
    resp.raise_for_status()
    rows = resp.json()
    df = pd.DataFrame(rows[1:], columns=rows[0])
    for c in CENSUS_B03002.values():
        df[c] = pd.to_numeric(df[c], errors="coerce")
    df.to_csv(cache, index=False)
    return df


def build_population(year: int) -> pd.DataFrame:
    raw = fetch_b03002(year)
    raw = raw[raw["state"].isin(STATE_FIPS_TO_CODE)]
    rows = []
    for _, r in raw.iterrows():
        state_code = STATE_FIPS_TO_CODE[r["state"]]
        total = float(r[CENSUS_B03002["total"]])
        shares = census_to_race_origin_shares(r.to_dict())
        for (race, origin), ro_share in shares.items():
            for age_group, ag_share in AGE_SHARES.items():
                for sex in ("m", "f"):
                    sex_share = 0.50
                    if age_group in ("80-84", "85+"):
                        sex_share = 0.40 if sex == "m" else 0.60
                    cell = total * ro_share * ag_share * sex_share
                    rows.append({
                        "state_code": state_code,
                        "year": year,
                        "race": race,
                        "origin": origin,
                        "sex": sex,
                        "age_group": age_group,
                        "population": max(int(round(cell)), 0),
                        "is_projection": 0,
                    })
    return pd.DataFrame(rows)


def build_population_2023() -> pd.DataFrame:
    return build_population(2023)


if __name__ == "__main__":
    for yr in (2018, 2023):
        df = build_population(yr)
        out = DATA_DIR / f"population_{yr}.csv"
        df.to_csv(out, index=False)
        total = df["population"].sum()
        print(f"Wrote {len(df):,} rows to {out}  (national total {total:,})")
