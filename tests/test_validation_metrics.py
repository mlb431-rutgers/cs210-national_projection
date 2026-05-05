import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import pandas as pd

from src.db import DATA_DIR


class TestImputationMetrics(unittest.TestCase):
    def setUp(self):
        path = DATA_DIR / "validation" / "imputation_metrics.csv"
        if not path.exists():
            self.skipTest("Run notebook 4 first.")
        self.df = pd.read_csv(path)

    def test_three_targets(self):
        self.assertEqual(len(self.df), 3)

    def test_r_squared_above_threshold(self):
        self.assertTrue((self.df["r2"] >= 0.7).all())


class TestMigrationModel(unittest.TestCase):
    def setUp(self):
        path = DATA_DIR / "validation" / "migration_model_metrics.csv"
        if not path.exists():
            self.skipTest("Run notebook 4 (section 5) first.")
        self.df = pd.read_csv(path)

    def test_one_row(self):
        self.assertEqual(len(self.df), 1)

    def test_holdout_r2_is_meaningful(self):
        self.assertGreater(self.df["r2"].iloc[0], 0.5)


class TestBackcastMetrics(unittest.TestCase):
    def setUp(self):
        path = DATA_DIR / "validation" / "backcast_state_mape.csv"
        if not path.exists():
            self.skipTest("Run notebook 5 first.")
        self.df = pd.read_csv(path)

    def test_all_51_states(self):
        self.assertEqual(len(self.df), 51)

    def test_national_error_within_5_percent(self):
        err = abs(self.df["projected"].sum() - self.df["observed"].sum())
        err_pct = 100 * err / self.df["observed"].sum()
        self.assertLess(err_pct, 5.0)

    def test_no_state_runs_away(self):
        self.assertTrue((self.df["abs_pct_err"] < 15.0).all())

    def test_dc_is_no_longer_extreme_outlier(self):
        dc_err = self.df.loc[self.df["state_code"] == "DC", "abs_pct_err"].iloc[0]
        self.assertLess(dc_err, 12.0)


if __name__ == "__main__":
    unittest.main()
