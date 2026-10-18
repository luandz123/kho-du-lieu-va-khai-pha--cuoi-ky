"""Invented fixtures only; no database connection or real user rows."""
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from etl.s05_staging import SafeError
from etl.s06b_bridge import canonical_bridge_frame, namespace, prepare_bridge


class BridgeTests(unittest.TestCase):
    def prepare(self, movies=None, movie_map=None, genre_map=None):
        return prepare_bridge(
            movies if movies is not None else [(1, "701", 'Éxample, "fixture"', "Drama|Comedy"), (2, "702", "Second", "Drama")],
            movie_map if movie_map is not None else [(701, 9001), (702, 9011)],
            genre_map if genre_map is not None else [("Comedy", 57), ("Drama", 63)],
            {"Comedy", "Drama"})

    def error(self, code, **kwargs):
        with self.assertRaises(SafeError) as caught:
            self.prepare(**kwargs)
        self.assertEqual(caught.exception.code, code)

    def test_multigenre_maps_surrogates_without_changing_movies(self):
        p = self.prepare()
        self.assertEqual(p["pairs"], [(701, "Comedy"), (701, "Drama"), (702, "Drama")])
        self.assertEqual(p["mapped"], [(9001, 57), (9001, 63), (9011, 63)])
        self.assertEqual(p["genre_counts"], {701: 2, 702: 1})

    def test_missing_movie_mapping(self):
        self.error("MISSING_MOVIE_MAPPING", movie_map=[(702, 9)])

    def test_missing_genre_mapping(self):
        self.error("MISSING_GENRE_MAPPING", genre_map=[("Comedy", 1)])

    def test_duplicate_natural_movie_mapping(self):
        self.error("NON_UNIQUE_MOVIE_MAPPING", movie_map=[(701, 9), (701, 10)])

    def test_duplicate_surrogate_movie_mapping(self):
        self.error("NON_UNIQUE_MOVIE_MAPPING", movie_map=[(701, 9), (702, 9)])

    def test_duplicate_genre_mapping(self):
        self.error("NON_UNIQUE_GENRE_MAPPING", genre_map=[("Comedy", 1), ("Drama", 1)])

    def test_duplicate_pair_is_not_deduplicated(self):
        self.error("DUPLICATE_SOURCE_MOVIE_GENRE", movies=[(1, "701", "Fixture", "Drama|Drama")])

    def test_duplicate_source_movie(self):
        self.error("DUPLICATE_SOURCE_MOVIE", movies=[(1, "701", "A", "Drama"), (2, "701", "B", "Comedy")])

    def test_unknown_genre(self):
        self.error("UNKNOWN_SOURCE_GENRE", movies=[(1, "701", "Fixture", "Drama|OtherFixture")])

    def test_no_genre_whitespace_normalization(self):
        self.error("UNKNOWN_SOURCE_GENRE", movies=[(1, "701", "Fixture", " Comedy")])

    def test_empty_and_null_genre(self):
        for value in ["", None]:
            self.error("EMPTY_SOURCE_GENRES", movies=[(1, "701", "Fixture", value)])

    def test_extra_dimension_movie_is_not_silently_ignored(self):
        self.error("SOURCE_AND_DIMENSION_MOVIE_SET_DIFFER", movie_map=[(701, 1), (702, 2), (703, 3)])

    def test_invalid_surrogate(self):
        self.error("INVALID_MOVIE_MAPPING", movie_map=[(701, None), (702, 2)])

    def test_canonical_column_order_and_sort_csv_bytes(self):
        from mining.data_io import serialize_df_to_canonical_csv_bytes
        frame = canonical_bridge_frame(["movie_id", "genre_name"], [(702, "Drama"), (701, "Drama"), (701, "Comedy")])
        expected = b"movie_id,genre_name\n701,Comedy\n701,Drama\n702,Drama\n"
        self.assertEqual(serialize_df_to_canonical_csv_bytes("movie_genres", frame), expected)
        with self.assertRaises(SafeError):
            canonical_bridge_frame(["genre_name", "movie_id"], [])

    def test_invalid_namespace(self):
        for value in ["public", "dw;DROP", "s06b_test_bad"]:
            with self.assertRaises(SafeError):
                namespace(value)


if __name__ == "__main__":
    unittest.main()
