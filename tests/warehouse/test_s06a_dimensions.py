"""6A pure-transform tests: invented fixtures, no DB or actual personal rows."""
import json
import unittest
from datetime import date

from etl.s06a_dimensions import ROOT, SafeError, canonical_dimension_frame, integer, prepare_dimensions, utc_instant


class DimensionTransforms(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.contract = json.loads((ROOT / "docs/shared/data_contract.json").read_text(encoding="utf-8"))
        cls.codes = json.loads((ROOT / "results/eda/canonical_manifest.json").read_text(encoding="utf-8"))["source_code_sets"]

    def prepare(self, users=None, movies=None, low=946684799, high=946684800):
        return prepare_dimensions(
            [(1, "101", "F", "18", "4")] if users is None else users,
            [(1, "701", "Fixture (2001)", "Comedy|Drama")] if movies is None else movies,
            low, high, self.contract, self.codes)

    def test_all_seven_age_labels_and_occupation_retained(self):
        users = [(i + 1, str(101 + i), "F", code, "4") for i, code in enumerate(self.contract["age_labels"])]
        rows = self.prepare(users=users)["rows"]["dim_user"]
        self.assertEqual([r[2] for r in rows], list(self.contract["age_labels"].values()))
        self.assertTrue(all(r[3] == 4 for r in rows))

    def test_title_special_characters_preserved(self):
        title = '  Éxample, "fixture" (2001)'
        self.assertEqual(self.prepare(movies=[(1, "701", title, "Comedy")])["rows"]["dim_movie"][0], (701, title, 2001))

    def test_absent_or_nonfour_digit_or_trailing_year_is_null(self):
        for title in ["No year", "Fixture (999)", "Fixture (2001) "]:
            with self.subTest(title=title):
                self.assertIsNone(self.prepare(movies=[(1, "701", title, "Comedy")])["rows"]["dim_movie"][0][2])

    def test_final_parenthesized_year_only(self):
        self.assertEqual(self.prepare(movies=[(1, "701", "Fixture (1990) (2002)", "Comedy")])["rows"]["dim_movie"][0][2], 2002)

    def test_utc_midnight_not_machine_timezone(self):
        p = self.prepare()
        self.assertEqual(p["rows"]["dim_date"], [(date(1999, 12, 31),), (date(2000, 1, 1),)])
        self.assertEqual(p["utc"]["min_rated_at"], "1999-12-31T23:59:59Z")
        self.assertEqual(p["utc"]["max_rated_at"], "2000-01-01T00:00:00Z")

    def test_leap_day_continuous_calendar(self):
        p = self.prepare(low=951696000, high=951868800)  # 2000-02-28 through 2000-03-01 UTC.
        self.assertEqual(p["rows"]["dim_date"], [(date(2000, 2, 28),), (date(2000, 2, 29),), (date(2000, 3, 1),)])

    def test_negative_epoch_is_utc(self):
        self.assertEqual(utc_instant(-1).isoformat(), "1969-12-31T23:59:59+00:00")

    def test_duplicate_user_or_movie_rejected(self):
        with self.assertRaises(SafeError):
            self.prepare(users=[(1, "101", "F", "18", "4"), (2, "101", "M", "25", "1")])
        with self.assertRaises(SafeError):
            self.prepare(movies=[(1, "701", "A", "Comedy"), (2, "701", "B", "Drama")])

    def test_invalid_user_codes_rejected(self):
        for gender, age, occupation in [("X", "18", "4"), ("F", "17", "4"), ("F", "18", "21"), (None, "18", "4")]:
            with self.subTest(gender=gender, age=age):
                with self.assertRaises(SafeError):
                    self.prepare(users=[(1, "101", gender, age, occupation)])

    def test_unknown_or_duplicate_movie_genre_rejected(self):
        for genres in ["Comedy|UnspecifiedFixture", "Comedy|Comedy", " Comedy", ""]:
            with self.subTest(genres=genres):
                with self.assertRaises(SafeError):
                    self.prepare(movies=[(1, "701", "Fixture", genres)])

    def test_integer_and_timestamp_domain(self):
        for value in [None, "1.0", " 1", "1e2"]:
            with self.assertRaises(SafeError):
                integer(value, 1, 100, "FIXTURE")
        for low, high in [(2, 1), (2**63, 2**63), (2**63 - 1, 2**63 - 1)]:
            with self.assertRaises(SafeError):
                self.prepare(low=low, high=high)

    def test_genre_global_grain_one_row_each(self):
        p = self.prepare(movies=[(1, "701", "First", "Comedy|Drama"), (2, "702", "Second", "Drama")])
        self.assertEqual(p["rows"]["dim_genre"], [("Comedy",), ("Drama",)])
        self.assertEqual(len(p["rows"]["dim_movie"]), 2)

    def test_canonical_view_client_sorts_rows_and_preserves_nullable_integer(self):
        from mining.data_io import serialize_df_to_canonical_csv_bytes
        frame = canonical_dimension_frame("movies", ["movie_id", "title", "release_year"],
                                          [(702, "No year", None), (701, 'Éxample, "film" (2001)', 2001)])
        expected = 'movie_id,title,release_year\n701,"Éxample, ""film"" (2001)",2001\n702,No year,\n'.encode("utf-8")
        self.assertEqual(serialize_df_to_canonical_csv_bytes("movies", frame), expected)


if __name__ == "__main__":
    unittest.main()
