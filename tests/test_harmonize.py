import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.ingest.harmonize import (
    CENSUS_B03002,
    STATE_FIPS_TO_CODE,
    census_to_race_origin_shares,
)


class TestStateFIPS(unittest.TestCase):
    def test_includes_all_50_states_plus_dc(self):
        self.assertEqual(len(STATE_FIPS_TO_CODE), 51)

    def test_codes_are_two_letter_strings(self):
        for code in STATE_FIPS_TO_CODE.values():
            self.assertEqual(len(code), 2)
            self.assertTrue(code.isupper())

    def test_known_examples(self):
        self.assertEqual(STATE_FIPS_TO_CODE["06"], "CA")
        self.assertEqual(STATE_FIPS_TO_CODE["48"], "TX")
        self.assertEqual(STATE_FIPS_TO_CODE["11"], "DC")


class TestCensusShares(unittest.TestCase):
    def test_shares_sum_to_about_one(self):
        row = {
            CENSUS_B03002["total"]: 38_965_193,
            CENSUS_B03002["non_hisp_total"]: 23_204_756,
            CENSUS_B03002["non_hisp_white"]: 12_962_645,
            CENSUS_B03002["non_hisp_black"]: 2_004_832,
            CENSUS_B03002["non_hisp_asian"]: 6_042_726,
            CENSUS_B03002["hisp_total"]: 15_760_437,
            CENSUS_B03002["hisp_white"]: 2_036_607,
            CENSUS_B03002["hisp_black"]: 98_957,
            CENSUS_B03002["hisp_asian"]: 104_125,
        }
        shares = census_to_race_origin_shares(row)
        total = sum(shares.values())
        self.assertAlmostEqual(total, 1.0, places=4)

    def test_shares_are_non_negative(self):
        row = {
            CENSUS_B03002["total"]: 1_000_000,
            CENSUS_B03002["non_hisp_total"]: 800_000,
            CENSUS_B03002["non_hisp_white"]: 600_000,
            CENSUS_B03002["non_hisp_black"]: 100_000,
            CENSUS_B03002["non_hisp_asian"]: 50_000,
            CENSUS_B03002["hisp_total"]: 200_000,
            CENSUS_B03002["hisp_white"]: 150_000,
            CENSUS_B03002["hisp_black"]: 10_000,
            CENSUS_B03002["hisp_asian"]: 5_000,
        }
        shares = census_to_race_origin_shares(row)
        for value in shares.values():
            self.assertGreaterEqual(value, 0.0)


if __name__ == "__main__":
    unittest.main()
