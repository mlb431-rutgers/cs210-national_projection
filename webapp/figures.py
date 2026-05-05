from __future__ import annotations

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go


def build_choropleth(conn, year: int = 2058) -> go.Figure:
    df = pd.read_sql(
        """
        SELECT state_code, state_name, total_population, total_labor_force
        FROM v_state_year_totals WHERE year = ?
        """,
        conn, params=(year,),
    )
    fig = px.choropleth(
        df, locations="state_code", locationmode="USA-states", scope="usa",
        color="total_population", color_continuous_scale="Viridis",
        hover_name="state_name",
        hover_data={"total_population": ":,", "total_labor_force": ":,", "state_code": False},
        labels={"total_population": "Population"},
        title=f"Projected population by state, {year}",
    )
    fig.update_layout(margin=dict(l=0, r=0, t=50, b=0), height=520)
    return fig


def build_state_timeseries(conn, state_code: str) -> go.Figure:
    df = pd.read_sql(
        """
        SELECT year, is_projection, total_population, total_labor_force
        FROM v_state_year_totals WHERE state_code = ? ORDER BY year
        """,
        conn, params=(state_code,),
    )
    fig = go.Figure()
    for kind, mask, dash in [
        ("Observed", df["is_projection"] == 0, "solid"),
        ("Projected", df["is_projection"] == 1, "dash"),
    ]:
        sub = df[mask]
        fig.add_trace(go.Scatter(
            x=sub["year"], y=sub["total_population"],
            mode="lines+markers", name=f"Population ({kind})",
            line=dict(dash=dash, color="#4C72B0", width=3),
        ))
        fig.add_trace(go.Scatter(
            x=sub["year"], y=sub["total_labor_force"],
            mode="lines+markers", name=f"Labor force ({kind})",
            line=dict(dash=dash, color="#C44E52", width=3),
        ))
    fig.update_layout(
        title="Population and labor force over time",
        xaxis_title="Year", yaxis_title="Count", height=420,
        legend=dict(orientation="h", yanchor="bottom", y=1.02),
    )
    return fig


def build_pyramid(conn, state_code: str, year: int) -> go.Figure:
    df = pd.read_sql(
        """
        SELECT ag.age_group, ag.sort_order, p.sex, SUM(p.population) AS population
        FROM population p JOIN age_groups ag ON ag.age_group = p.age_group
        WHERE p.state_code = ? AND p.year = ?
        GROUP BY ag.age_group, ag.sort_order, p.sex
        ORDER BY ag.sort_order
        """,
        conn, params=(state_code, year),
    )
    pivot = df.pivot(index="age_group", columns="sex", values="population").reindex(
        df.sort_values("sort_order")["age_group"].unique()
    ).fillna(0)
    fig = go.Figure()
    fig.add_trace(go.Bar(
        y=pivot.index, x=-pivot.get("m", 0),
        name="Male", orientation="h", marker_color="#4C72B0",
        hovertemplate="Age %{y}<br>Male: %{customdata:,}<extra></extra>",
        customdata=pivot.get("m", 0),
    ))
    fig.add_trace(go.Bar(
        y=pivot.index, x=pivot.get("f", 0),
        name="Female", orientation="h", marker_color="#C44E52",
        hovertemplate="Age %{y}<br>Female: %{x:,}<extra></extra>",
    ))
    fig.update_layout(
        title=f"Age pyramid, {year}",
        barmode="relative", height=520,
        xaxis_title="Population", yaxis_title="Age group",
    )
    return fig


def build_national_totals(conn) -> go.Figure:
    df = pd.read_sql(
        """
        SELECT year, is_projection,
               SUM(total_population) AS pop, SUM(total_labor_force) AS lf
        FROM v_state_year_totals GROUP BY year, is_projection ORDER BY year
        """,
        conn,
    )
    fig = go.Figure()
    obs = df[df["is_projection"] == 0]
    proj = df[df["is_projection"] == 1]
    fig.add_trace(go.Scatter(x=obs["year"], y=obs["pop"], mode="lines+markers",
                             name="Population (observed)", line=dict(color="#333", width=3)))
    fig.add_trace(go.Scatter(x=proj["year"], y=proj["pop"], mode="lines+markers",
                             name="Population (projected)", line=dict(dash="dash", color="#4C72B0", width=3)))
    fig.add_trace(go.Scatter(x=obs["year"], y=obs["lf"], mode="lines+markers",
                             name="Labor force (observed)", line=dict(color="#777", width=3)))
    fig.add_trace(go.Scatter(x=proj["year"], y=proj["lf"], mode="lines+markers",
                             name="Labor force (projected)", line=dict(dash="dash", color="#C44E52", width=3)))
    fig.update_layout(
        title="U.S. national totals, 2018-2058",
        xaxis_title="Year", yaxis_title="Count", height=420,
        legend=dict(orientation="h", yanchor="bottom", y=1.02),
    )
    return fig


def build_growth_ranking(conn, top_n: int = 10) -> go.Figure:
    df = pd.read_sql(
        """
        SELECT s.state_name, s.state_code,
            SUM(CASE WHEN p.year=2023 AND p.is_projection=0 THEN p.population ELSE 0 END) AS pop_2023,
            SUM(CASE WHEN p.year=2058 AND p.is_projection=1 THEN p.population ELSE 0 END) AS pop_2058
        FROM population p JOIN states s ON s.state_code = p.state_code
        GROUP BY p.state_code
        """,
        conn,
    )
    df["pct_change"] = 100 * (df["pop_2058"] - df["pop_2023"]) / df["pop_2023"]
    df = df.sort_values("pct_change", ascending=False)
    top = df.head(top_n).iloc[::-1]
    bot = df.tail(top_n)
    fig = go.Figure()
    fig.add_trace(go.Bar(
        y=top["state_name"], x=top["pct_change"], orientation="h",
        marker_color="#4C72B0", name="Top growers",
    ))
    fig.add_trace(go.Bar(
        y=bot["state_name"], x=bot["pct_change"], orientation="h",
        marker_color="#C44E52", name="Bottom growers",
    ))
    fig.update_layout(
        title=f"Top and bottom {top_n} states by 2023-2058 population change",
        xaxis_title="% change", height=520, barmode="group",
    )
    return fig
