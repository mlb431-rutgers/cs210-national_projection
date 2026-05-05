import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import pandas as pd

from src.ccm import (
    AVG_LFPR,
    MAX_MIGRATION_FRACTION_PER_STEP,
    compute_labor_gap,
    compute_labor_migrants,
    next_age_group,
)
from src.db import BASE_YEAR, get_connection


class TestNextAgeGroup(unittest.TestCase):
    def setUp(self):
        self.groups = [
            "0-4", "5-9", "10-14", "15-19", "20-24", "25-29",
            "30-34", "35-39", "40-44", "45-49", "50-54", "55-59",
            "60-64", "65-69", "70-74", "75-79", "80-84", "85+",
        ]

    def test_advances_by_one(self):
        self.assertEqual(next_age_group("20-24", self.groups), "25-29")

    def test_85_plus_is_open_ended(self):
        self.assertEqual(next_age_group("85+", self.groups), "85+")


class TestLaborMechanics(unittest.TestCase):
    def test_unemployment_grosses_up_demand(self):
        gap = compute_labor_gap(labor_supply=900_000, total_employment=1_000_000)
        self.assertGreater(gap, 100_000)
        self.assertLess(gap, 200_000)

    def test_migrant_count_uses_avg_lfpr(self):
        n = compute_labor_migrants(labor_gap=100_000, labor_supply=10_000_000)
        self.assertAlmostEqual(n, int(round(100_000 / AVG_LFPR)), delta=1)

    def test_cap_binds_when_gap_is_huge(self):
        n = compute_labor_migrants(labor_gap=5_000_000, labor_supply=400_000)
        cap = int(round(MAX_MIGRATION_FRACTION_PER_STEP * 400_000 / AVG_LFPR))
        self.assertEqual(n, cap)


class TestProjectionDatabase(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.conn = get_connection(read_only=True)

    @classmethod
    def tearDownClass(cls):
        cls.conn.close()

    def test_baseline_row_count(self):
        n = self.conn.execute(
            "SELECT COUNT(*) FROM population WHERE year=? AND is_projection=0",
            (BASE_YEAR,),
        ).fetchone()[0]
        self.assertEqual(n, 14_688)

    def test_no_negative_populations(self):
        n = self.conn.execute(
            "SELECT COUNT(*) FROM population WHERE population < 0"
        ).fetchone()[0]
        self.assertEqual(n, 0)

    def test_projection_row_count(self):
        n = self.conn.execute(
            "SELECT COUNT(*) FROM population WHERE is_projection=1"
        ).fetchone()[0]
        self.assertEqual(n, 102_816)

    def test_state_count(self):
        n = self.conn.execute("SELECT COUNT(*) FROM states").fetchone()[0]
        self.assertEqual(n, 51)

    def test_top_state_is_california(self):
        top = self.conn.execute("""
            SELECT s.state_name FROM population p
            JOIN states s USING(state_code)
            WHERE p.year=? AND p.is_projection=0
            GROUP BY p.state_code
            ORDER BY SUM(p.population) DESC LIMIT 1
        """, (BASE_YEAR,)).fetchone()[0]
        self.assertEqual(top, "California")


if __name__ == "__main__":
    unittest.main()
