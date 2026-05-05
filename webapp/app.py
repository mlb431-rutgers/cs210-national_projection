from __future__ import annotations

import json

from flask import Flask, g, jsonify, render_template, request

from src.db import DB_PATH, get_connection
from webapp import figures


def create_app() -> Flask:
    app = Flask(__name__)
    app.config["DB_PATH"] = str(DB_PATH)

    @app.before_request
    def _open_db():
        g.conn = get_connection(read_only=True)

    @app.teardown_request
    def _close_db(exc):
        conn = g.pop("conn", None)
        if conn is not None:
            conn.close()

    @app.context_processor
    def inject_states():
        conn = get_connection(read_only=True)
        states = [
            {"state_code": r[0], "state_name": r[1]}
            for r in conn.execute("SELECT state_code, state_name FROM states ORDER BY state_name")
        ]
        conn.close()
        return {"all_states": states}

    @app.route("/")
    def index():
        year = int(request.args.get("year", 2058))
        chor = figures.build_choropleth(g.conn, year=year)
        nat = figures.build_national_totals(g.conn)
        rank = figures.build_growth_ranking(g.conn)
        nat_2023 = g.conn.execute(
            "SELECT SUM(total_population), SUM(total_labor_force) "
            "FROM v_state_year_totals WHERE year=2023"
        ).fetchone()
        nat_2058 = g.conn.execute(
            "SELECT SUM(total_population), SUM(total_labor_force) "
            "FROM v_state_year_totals WHERE year=2058"
        ).fetchone()
        headline = {
            "pop_2023": nat_2023[0], "pop_2058": nat_2058[0],
            "lf_2023": nat_2023[1], "lf_2058": nat_2058[1],
            "pop_change_pct": 100 * (nat_2058[0] - nat_2023[0]) / nat_2023[0],
            "lf_change_pct": 100 * (nat_2058[1] - nat_2023[1]) / nat_2023[1],
        }
        return render_template(
            "index.html",
            year=year,
            chor_json=chor.to_json(),
            nat_json=nat.to_json(),
            rank_json=rank.to_json(),
            headline=headline,
        )

    @app.route("/state/<state_code>")
    def state_view(state_code: str):
        state_code = state_code.upper()
        year = int(request.args.get("year", 2058))
        row = g.conn.execute(
            "SELECT state_name, region, division FROM states WHERE state_code=?", (state_code,)
        ).fetchone()
        if row is None:
            return f"Unknown state: {state_code}", 404
        ts = figures.build_state_timeseries(g.conn, state_code)
        pyr = figures.build_pyramid(g.conn, state_code, year)
        return render_template(
            "state.html",
            state_code=state_code,
            state_name=row[0], region=row[1], division=row[2],
            year=year,
            ts_json=ts.to_json(), pyr_json=pyr.to_json(),
        )

    @app.route("/methodology")
    def methodology():
        try:
            metrics = []
            with open("data/validation/imputation_metrics.csv") as f:
                lines = f.read().strip().split("\n")
                hdr = lines[0].split(",")
                for ln in lines[1:]:
                    metrics.append(dict(zip(hdr, ln.split(","))))
        except FileNotFoundError:
            metrics = []
        try:
            with open("data/validation/backcast_state_mape.csv") as f:
                lines = f.read().strip().split("\n")
            hdr = lines[0].split(",")
            states_err = [dict(zip(hdr, ln.split(","))) for ln in lines[1:]]
            states_err.sort(key=lambda r: float(r["abs_pct_err"]))
            best5 = states_err[:5]
            worst5 = states_err[-5:][::-1]
            national_proj = sum(float(r["projected"]) for r in states_err)
            national_obs = sum(float(r["observed"]) for r in states_err)
            national_err = abs(national_proj - national_obs) / national_obs * 100
        except FileNotFoundError:
            best5 = worst5 = []
            national_err = None
        return render_template(
            "methodology.html",
            imputation_metrics=metrics,
            best5=best5, worst5=worst5,
            national_err=national_err,
        )

    @app.route("/api/state/<state_code>")
    def api_state(state_code: str):
        year = int(request.args.get("year", 2058))
        pyr = figures.build_pyramid(g.conn, state_code.upper(), year)
        return jsonify(json.loads(pyr.to_json()))

    @app.route("/api/states")
    def api_states():
        rows = g.conn.execute(
            "SELECT state_code, state_name FROM states ORDER BY state_name"
        ).fetchall()
        return jsonify([{"state_code": r[0], "state_name": r[1]} for r in rows])

    return app


if __name__ == "__main__":
    create_app().run(debug=True, port=5000)
