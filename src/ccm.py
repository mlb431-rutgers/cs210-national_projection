from __future__ import annotations

import pandas as pd

MALE_SEX_RATIO_AT_BIRTH = 1.05 / 2.05
FEMALE_SEX_RATIO_AT_BIRTH = 1.0 - MALE_SEX_RATIO_AT_BIRTH

UNEMPLOYMENT_RATE = 0.04

AVG_LFPR = 0.6475

STEP_YEARS = 5

YOUNG_AGE_GROUPS = ("0-4", "5-9", "10-14")

MAX_MIGRATION_FRACTION_PER_STEP = 0.05


def next_age_group(age_group: str, ordered_age_groups: list[str]) -> str:
    idx = ordered_age_groups.index(age_group)
    if idx == len(ordered_age_groups) - 1:
        return age_group
    return ordered_age_groups[idx + 1]


def compute_births(pop_df: pd.DataFrame, fertility_df: pd.DataFrame, state_code: str) -> pd.DataFrame:
    mothers = pop_df[(pop_df["state_code"] == state_code) & (pop_df["sex"] == "f")]
    f_rates = fertility_df[fertility_df["state_code"] == state_code]

    merged = mothers.merge(f_rates, on=["state_code", "race", "origin", "age_group"], how="left")
    merged["fertility_rate"] = merged["fertility_rate"].fillna(0.0)
    merged["births"] = merged["population"] * merged["fertility_rate"] * STEP_YEARS

    grouped = merged.groupby(["race", "origin"], as_index=False)["births"].sum()

    rows = []
    for _, r in grouped.iterrows():
        total = r["births"]
        rows.append({
            "state_code": state_code, "race": r["race"], "origin": r["origin"],
            "sex": "m", "age_group": "0-4",
            "population": round(total * MALE_SEX_RATIO_AT_BIRTH),
        })
        rows.append({
            "state_code": state_code, "race": r["race"], "origin": r["origin"],
            "sex": "f", "age_group": "0-4",
            "population": round(total * FEMALE_SEX_RATIO_AT_BIRTH),
        })
    return pd.DataFrame(rows)


def project_zero_migration(pop_df: pd.DataFrame, fertility_df: pd.DataFrame,
                           mortality_df: pd.DataFrame, state_code: str,
                           ordered_age_groups: list[str]) -> pd.DataFrame:
    state_pop = pop_df[pop_df["state_code"] == state_code].copy()
    state_mort = mortality_df[mortality_df["state_code"] == state_code]

    merged = state_pop.merge(
        state_mort, on=["state_code", "race", "origin", "sex", "age_group"], how="left"
    )
    merged["mortality_rate"] = merged["mortality_rate"].fillna(0.0)
    merged["survived"] = (merged["population"] * (1.0 - merged["mortality_rate"])).round().astype(int)

    merged["new_age_group"] = merged["age_group"].apply(
        lambda ag: next_age_group(ag, ordered_age_groups)
    )

    aged = (
        merged.groupby(["state_code", "race", "origin", "sex", "new_age_group"], as_index=False)["survived"]
        .sum()
        .rename(columns={"new_age_group": "age_group", "survived": "population"})
    )
    aged = aged[aged["age_group"] != "0-4"]

    births = compute_births(state_pop, fertility_df, state_code)
    return pd.concat([aged, births], ignore_index=True)


def compute_labor_supply(pop_df: pd.DataFrame, lfpr_df: pd.DataFrame, state_code: str) -> int:
    sp = pop_df[pop_df["state_code"] == state_code]
    sl = lfpr_df[lfpr_df["state_code"] == state_code]
    merged = sp.merge(sl, on=["state_code", "race", "origin", "sex", "age_group"], how="left")
    merged["lfpr"] = merged["lfpr"].fillna(0.0)
    return int(round((merged["population"] * merged["lfpr"]).sum()))


def compute_labor_gap(labor_supply: int, total_employment: int,
                      unemployment_rate: float = UNEMPLOYMENT_RATE) -> int:
    labor_demand = total_employment / (1.0 - unemployment_rate)
    return int(round(labor_demand - labor_supply))


def compute_labor_migrants(labor_gap: int, labor_supply: int = 0,
                           avg_lfpr: float = AVG_LFPR,
                           max_fraction: float = MAX_MIGRATION_FRACTION_PER_STEP) -> int:
    raw = int(round(labor_gap / avg_lfpr))
    if labor_supply <= 0:
        return raw
    cap = int(round(max_fraction * labor_supply / avg_lfpr))
    if raw > cap:
        return cap
    if raw < -cap:
        return -cap
    return raw


def allocate_labor_migrants(pop_df: pd.DataFrame, migration_df: pd.DataFrame,
                            labor_migrants: int, state_code: str) -> pd.DataFrame:
    if labor_migrants == 0:
        return pd.DataFrame(columns=[
            "state_code", "race", "origin", "sex", "age_group", "allocated_migrants"
        ])

    sp = pop_df[pop_df["state_code"] == state_code]
    sm = migration_df[migration_df["state_code"] == state_code]
    merged = sp.merge(sm, on=["state_code", "race", "origin", "sex", "age_group"], how="left")
    merged["migration_rate"] = merged["migration_rate"].fillna(0.0)
    merged["weight"] = (merged["migration_rate"].abs() * merged["population"]).clip(lower=0)

    total_weight = merged["weight"].sum()
    if total_weight <= 0:
        merged["share"] = 1.0 / len(merged)
    else:
        merged["share"] = merged["weight"] / total_weight

    merged["allocated_migrants"] = (merged["share"] * labor_migrants).round().astype(int)
    return merged[["state_code", "race", "origin", "sex", "age_group", "allocated_migrants"]]


def project_one_step(pop_df: pd.DataFrame, fertility_df: pd.DataFrame,
                     mortality_df: pd.DataFrame, lfpr_df: pd.DataFrame,
                     employment_df: pd.DataFrame, migration_df: pd.DataFrame,
                     state_code: str, target_year: int,
                     ordered_age_groups: list[str]) -> pd.DataFrame:
    zero_mig = project_zero_migration(
        pop_df, fertility_df, mortality_df, state_code, ordered_age_groups
    )

    supply = compute_labor_supply(zero_mig, lfpr_df, state_code)
    emp_row = employment_df[
        (employment_df["state_code"] == state_code) & (employment_df["year"] == target_year)
    ]
    total_employment = int(emp_row["total_employment"].iloc[0]) if len(emp_row) else 0
    gap = compute_labor_gap(supply, total_employment)
    labor_migrants = compute_labor_migrants(gap, labor_supply=supply)

    alloc = allocate_labor_migrants(zero_mig, migration_df, labor_migrants, state_code)

    state_mig = migration_df[migration_df["state_code"] == state_code]
    merged = zero_mig.merge(
        state_mig, on=["state_code", "race", "origin", "sex", "age_group"], how="left"
    )
    merged["migration_rate"] = merged["migration_rate"].fillna(0.0)
    is_young = merged["age_group"].isin(YOUNG_AGE_GROUPS)
    merged["young_migrants"] = 0
    merged.loc[is_young, "young_migrants"] = (
        merged.loc[is_young, "population"] * merged.loc[is_young, "migration_rate"]
    ).round().astype(int)

    merged = merged.merge(
        alloc, on=["state_code", "race", "origin", "sex", "age_group"], how="left"
    )
    merged["allocated_migrants"] = merged["allocated_migrants"].fillna(0).astype(int)

    merged["net_migrants"] = merged["young_migrants"].where(is_young, merged["allocated_migrants"])
    merged["new_population"] = (merged["population"] + merged["net_migrants"]).clip(lower=0)

    result = merged[[
        "state_code", "race", "origin", "sex", "age_group", "new_population"
    ]].rename(columns={"new_population": "population"}).copy()
    result["year"] = target_year
    result["is_projection"] = 1
    return result


def run_full_projection(pop_baseline: pd.DataFrame, fertility_df: pd.DataFrame,
                        mortality_df: pd.DataFrame, lfpr_df: pd.DataFrame,
                        employment_df: pd.DataFrame, migration_df: pd.DataFrame,
                        ordered_age_groups: list[str],
                        projection_years: tuple[int, ...]) -> pd.DataFrame:
    states = sorted(pop_baseline["state_code"].unique())
    all_steps = []
    for state in states:
        curr = pop_baseline[pop_baseline["state_code"] == state].copy()
        for target_year in projection_years:
            step = project_one_step(
                pop_df=curr, fertility_df=fertility_df, mortality_df=mortality_df,
                lfpr_df=lfpr_df, employment_df=employment_df, migration_df=migration_df,
                state_code=state, target_year=target_year,
                ordered_age_groups=ordered_age_groups,
            )
            all_steps.append(step)
            curr = step
    return pd.concat(all_steps, ignore_index=True)
