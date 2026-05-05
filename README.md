# CS 210 Final Project - US Population and Labor Force Projection

Hannah Hollosi and Michal Borkowski, Spring 2026

## What this project does

We use the Cohort Component Method (CCM) to project the US population
and labor force from 2023 out to 2058 for all 50 states plus DC. The
baseline population numbers for 2018 and 2023 come from the US Census
Bureau (the ACS 1-year estimates, table B03002). The state employment
numbers come from the Bureau of Labor Statistics (CES 2023 and the
Employment Projections for 2022 to 2032). We project forward in 5-year
steps and we write everything to a SQLite database.

Here are some of the numbers we got.

- US population in 2023 was 338.3 million and our projection puts it
  at 428.3 million by 2058, a change of about 26.6 percent.
- US labor force in 2023 was 168.8 million and our projection puts it
  at 213.8 million by 2058, a change of about 26.7 percent.

To check that the model is reasonable, we project the real 2018
baseline forward to 2023 and compare to the real 2023 numbers. This is
called backcasting. The national error is 1.63 percent and the typical
state error is 2.80 percent.

## How to run it

1. `pip install -r requirements.txt`
2. Open the notebooks folder and run them in order, 01 first then 02,
   03, 04, and 05.
3. From the project root, run `python -m webapp.app`
   Then open your browser and go to `localhost:5000`.

The webpage has three parts. The home page shows a US map with the
projected population for each state. Each state has its own page with
a population time series and an age pyramid that you can change with
a year filter. The methodology page has an explanation of the CCM
and the validation numbers from notebook 5.

## Folders

- `data/` — Input CSVs (some real Census and BLS data, some synthetic)
- `db/` — SQLite schema (`schema.sql`) and the populated database
- `notebooks/` — The 5 notebooks, numbered in the order you run them
- `src/` — Python modules used by the notebooks and the web app
- `webapp/` — The Flask web app
- `plots/` — Static plots saved from notebooks 3, 4, and 5
- `tests/` — Smoke tests, run with `python -m unittest discover tests`

## What is real data and what is synthetic

The 2018 and 2023 baseline populations are real (US Census ACS,
table B03002). The state employment numbers are also real (BLS CES
and Employment Projections).

The fertility rates, mortality rates, labor force participation
rates, and migration rates are synthetic, but we calibrated them to
US national averages so they are realistic. We discuss this in our
writeup. We would replace them with real CDC WONDER, ACS PUMS, and
SEER data given more time, and the pipeline can accept any CSV with
the right shape.
