"""Pure invented fixtures for 6C, including chunked canonical serialization."""
import sys
import unittest
from datetime import date
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from etl.s05_staging import SafeError
from etl.s06c_fact import COLUMNS, CanonicalDigest, mapped_rating, mapped_rows, mappings, namespace, parse_rating


class FactTests(unittest.TestCase):
    def maps(self):
        return mappings([(101, 9001), (102, 9002)], [(701, 8001)], [(date(1999, 12, 31), 7001), (date(2000, 1, 1), 7002)])

    def test_original_ids_map_to_different_surrogates(self):
        out = mapped_rating((1, "101", "701", "5", "946684800"), self.maps())
        self.assertEqual(out[:5], (9001, 8001, 7002, 5, 946684800))

    def test_missing_user(self):
        with self.assertRaisesRegex(SafeError, "MISSING_USER_MAPPING"):
            mapped_rating((1, "999", "701", "5", "946684800"), self.maps())

    def test_missing_movie(self):
        with self.assertRaisesRegex(SafeError, "MISSING_MOVIE_MAPPING"):
            mapped_rating((1, "101", "999", "5", "946684800"), self.maps())

    def test_missing_date(self):
        with self.assertRaisesRegex(SafeError, "MISSING_DATE_MAPPING"):
            mapped_rating((1, "101", "701", "5", "946857600"), self.maps())

    def test_duplicate_natural_mapping(self):
        with self.assertRaises(SafeError):
            mappings([(101, 1), (101, 2)], [], [])

    def test_duplicate_surrogate_mapping(self):
        with self.assertRaises(SafeError):
            mappings([(101, 1), (102, 1)], [], [])

    def test_duplicate_user_movie_not_deduplicated(self):
        rows = [(1, "101", "701", "5", "946684799"), (2, "101", "701", "4", "946684800")]
        with self.assertRaisesRegex(SafeError, "DUPLICATE_SOURCE_USER_MOVIE"):
            list(mapped_rows(rows, self.maps()))

    def test_rating_domain(self):
        for r in ["0", "6", "-1", "1.0", None]:
            with self.subTest(rating=r), self.assertRaises(SafeError):
                parse_rating((1, "101", "701", r, "946684800"))

    def test_all_five_stars_accepted(self):
        for r in range(1, 6):
            self.assertEqual(parse_rating((1, "101", "701", str(r), "946684800"))[2], r)

    def test_ids_positive_integer(self):
        for bad in ["0", "-1", "1.0", None, " 101", str(2**31)]:
            with self.assertRaises(SafeError):
                parse_rating((1, bad, "701", "5", "946684800"))

    def test_timestamp_int64_and_supported_date(self):
        for ts in [str(2**63), str(-(2**63) - 1), str(2**63 - 1), "1.5", None]:
            with self.assertRaises(SafeError):
                parse_rating((1, "101", "701", "5", ts))

    def test_utc_midnight_two_adjacent_days(self):
        before = mapped_rating((1, "101", "701", "5", "946684799"), self.maps())
        after = mapped_rating((2, "102", "701", "4", "946684800"), self.maps())
        self.assertEqual((before[2], after[2]), (7001, 7002))
        self.assertEqual(before[-1].isoformat(), "1999-12-31T23:59:59+00:00")
        self.assertEqual(after[-1].isoformat(), "2000-01-01T00:00:00+00:00")

    def test_negative_epoch_is_utc(self):
        self.assertEqual(parse_rating((1, "101", "701", "5", "-1"))[-1].isoformat(), "1969-12-31T23:59:59+00:00")

    def test_one_source_rating_yields_one_fact_regardless_of_genre(self):
        rows = [(1, "101", "701", "5", "946684800")]
        self.assertEqual(len(list(mapped_rows(rows, self.maps()))), 1)

    def test_chunked_serialization_equals_single_reviewed_serializer(self):
        import hashlib
        from mining.data_io import serialize_df_to_canonical_csv_bytes
        rows = [(101, 701, 5, 946684799, "1999-12-31T23:59:59Z"), (102, 701, 4, 946684800, "2000-01-01T00:00:00Z")]
        expected = hashlib.sha256(serialize_df_to_canonical_csv_bytes("ratings", pd.DataFrame(rows, columns=COLUMNS))).hexdigest()
        digest = CanonicalDigest()
        digest.update(rows[:1]); digest.update(rows[1:])
        self.assertEqual(digest.hexdigest(), expected)

    def test_empty_canonical_header(self):
        import hashlib
        expected = hashlib.sha256(b"user_id,movie_id,rating,timestamp,rated_at\n").hexdigest()
        self.assertEqual(CanonicalDigest().hexdigest(), expected)

    def test_namespace_guard(self):
        for value in ["public", "dw;DROP", "s06c_test_bad"]:
            with self.assertRaises(SafeError):
                namespace(value)


if __name__ == "__main__":
    unittest.main()
