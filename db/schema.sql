PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS states (
    state_code   TEXT PRIMARY KEY,
    state_name   TEXT NOT NULL UNIQUE,
    region       TEXT NOT NULL,
    division     TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS age_groups (
    age_group    TEXT PRIMARY KEY,
    age_min      INTEGER NOT NULL,
    age_max      INTEGER,
    sort_order   INTEGER NOT NULL UNIQUE
);

CREATE TABLE IF NOT EXISTS population (
    state_code     TEXT NOT NULL,
    year           INTEGER NOT NULL,
    race           TEXT NOT NULL CHECK (race IN ('white','black','asian','other')),
    origin         TEXT NOT NULL CHECK (origin IN ('hisp','non-hisp')),
    sex            TEXT NOT NULL CHECK (sex IN ('m','f')),
    age_group      TEXT NOT NULL,
    population     INTEGER NOT NULL CHECK (population >= 0),
    is_projection  INTEGER NOT NULL DEFAULT 0 CHECK (is_projection IN (0,1)),
    PRIMARY KEY (state_code, year, race, origin, sex, age_group, is_projection),
    FOREIGN KEY (state_code) REFERENCES states(state_code),
    FOREIGN KEY (age_group) REFERENCES age_groups(age_group)
);

CREATE TABLE IF NOT EXISTS fertility_rates (
    state_code      TEXT NOT NULL,
    year            INTEGER NOT NULL,
    race            TEXT NOT NULL CHECK (race IN ('white','black','asian','other')),
    origin          TEXT NOT NULL CHECK (origin IN ('hisp','non-hisp')),
    age_group       TEXT NOT NULL,
    fertility_rate  REAL NOT NULL CHECK (fertility_rate >= 0),
    source          TEXT NOT NULL,
    PRIMARY KEY (state_code, year, race, origin, age_group),
    FOREIGN KEY (state_code) REFERENCES states(state_code),
    FOREIGN KEY (age_group) REFERENCES age_groups(age_group)
);

CREATE TABLE IF NOT EXISTS mortality_rates (
    state_code      TEXT NOT NULL,
    year            INTEGER NOT NULL,
    race            TEXT NOT NULL CHECK (race IN ('white','black','asian','other')),
    origin          TEXT NOT NULL CHECK (origin IN ('hisp','non-hisp')),
    sex             TEXT NOT NULL CHECK (sex IN ('m','f')),
    age_group       TEXT NOT NULL,
    mortality_rate  REAL NOT NULL CHECK (mortality_rate >= 0 AND mortality_rate <= 1),
    source          TEXT NOT NULL,
    PRIMARY KEY (state_code, year, race, origin, sex, age_group),
    FOREIGN KEY (state_code) REFERENCES states(state_code),
    FOREIGN KEY (age_group) REFERENCES age_groups(age_group)
);

CREATE TABLE IF NOT EXISTS labor_force_participation (
    state_code   TEXT NOT NULL,
    year         INTEGER NOT NULL,
    race         TEXT NOT NULL CHECK (race IN ('white','black','asian','other')),
    origin       TEXT NOT NULL CHECK (origin IN ('hisp','non-hisp')),
    sex          TEXT NOT NULL CHECK (sex IN ('m','f')),
    age_group    TEXT NOT NULL,
    lfpr         REAL NOT NULL CHECK (lfpr >= 0 AND lfpr <= 1),
    source       TEXT NOT NULL,
    PRIMARY KEY (state_code, year, race, origin, sex, age_group),
    FOREIGN KEY (state_code) REFERENCES states(state_code),
    FOREIGN KEY (age_group) REFERENCES age_groups(age_group)
);

CREATE TABLE IF NOT EXISTS employment_projections (
    state_code        TEXT NOT NULL,
    year              INTEGER NOT NULL,
    total_employment  INTEGER NOT NULL CHECK (total_employment >= 0),
    source            TEXT NOT NULL,
    PRIMARY KEY (state_code, year),
    FOREIGN KEY (state_code) REFERENCES states(state_code)
);

CREATE TABLE IF NOT EXISTS migration_estimates (
    state_code      TEXT NOT NULL,
    year            INTEGER NOT NULL,
    race            TEXT NOT NULL CHECK (race IN ('white','black','asian','other')),
    origin          TEXT NOT NULL CHECK (origin IN ('hisp','non-hisp')),
    sex             TEXT NOT NULL CHECK (sex IN ('m','f')),
    age_group       TEXT NOT NULL,
    net_migration   INTEGER,
    migration_rate  REAL,
    source          TEXT NOT NULL,
    PRIMARY KEY (state_code, year, race, origin, sex, age_group),
    FOREIGN KEY (state_code) REFERENCES states(state_code),
    FOREIGN KEY (age_group) REFERENCES age_groups(age_group)
);

CREATE INDEX IF NOT EXISTS idx_population_state_year           ON population (state_code, year);
CREATE INDEX IF NOT EXISTS idx_fertility_state_year            ON fertility_rates (state_code, year);
CREATE INDEX IF NOT EXISTS idx_mortality_state_year            ON mortality_rates (state_code, year);
CREATE INDEX IF NOT EXISTS idx_lfpr_state_year                 ON labor_force_participation (state_code, year);
CREATE INDEX IF NOT EXISTS idx_employment_state_year           ON employment_projections (state_code, year);
CREATE INDEX IF NOT EXISTS idx_migration_state_year            ON migration_estimates (state_code, year);
CREATE INDEX IF NOT EXISTS idx_population_is_projection        ON population (is_projection);

DROP VIEW IF EXISTS v_population_with_labor_force;
CREATE VIEW v_population_with_labor_force AS
SELECT
    p.state_code,
    p.year,
    p.race,
    p.origin,
    p.sex,
    p.age_group,
    p.population,
    p.is_projection,
    CAST(ROUND(p.population * COALESCE(l.lfpr, 0)) AS INTEGER) AS labor_force
FROM population p
LEFT JOIN labor_force_participation l
    ON p.state_code = l.state_code
    AND p.race = l.race
    AND p.origin = l.origin
    AND p.sex = l.sex
    AND p.age_group = l.age_group;

DROP VIEW IF EXISTS v_state_year_totals;
CREATE VIEW v_state_year_totals AS
SELECT
    s.state_name,
    v.state_code,
    s.region,
    v.year,
    v.is_projection,
    SUM(v.population)  AS total_population,
    SUM(v.labor_force) AS total_labor_force
FROM v_population_with_labor_force v
JOIN states s ON s.state_code = v.state_code
GROUP BY v.state_code, v.year, v.is_projection;
