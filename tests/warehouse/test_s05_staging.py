"""Small invented fixtures only; these tests never connect to a database."""
import contextlib
import hashlib
import io
import json
import tempfile
import unittest
from pathlib import Path

from etl.s05_staging import SafeError, raw_rows, verify_sources


class ExtractTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.raw = Path(self.temp.name)

    def write(self, name, content):
        (self.raw / name).write_bytes(content.encode("latin-1"))

    def test_users_zip_discarded_without_trimming(self):
        self.write("users.dat", "101::F::18::4::inventedZIP\n")
        self.assertEqual(list(raw_rows(self.raw, "users_raw")), [(1, "101", "F", "18", "4")])

    def test_title_latin1_quotes_commas_spaces_preserved(self):
        title = '  Film é, "Example" (2001)  '
        self.write("movies.dat", "701::" + title + "::Comedy|Drama\n")
        self.assertEqual(list(raw_rows(self.raw, "movies_raw"))[0][2], title)

    def test_source_lines_and_crlf(self):
        self.write("ratings.dat", "101::701::04::000123\r\n102::701::5::124\r\n")
        self.assertEqual(list(raw_rows(self.raw, "ratings_raw")), [(1, "101", "701", "04", "000123"), (2, "102", "701", "5", "124")])

    def test_malformed_line_stops_instead_of_skip(self):
        self.write("ratings.dat", "101::701::4::123\nBROKEN\n102::701::5::124\n")
        iterator = raw_rows(self.raw, "ratings_raw")
        next(iterator)
        with self.assertRaises(SafeError) as caught:
            next(iterator)
        self.assertEqual(caught.exception.code, "MALFORMED_FIELD_COUNT")
        self.assertEqual(caught.exception.line, 2)

    def test_blank_line_rejected(self):
        self.write("movies.dat", "\n")
        with self.assertRaises(SafeError):
            list(raw_rows(self.raw, "movies_raw"))

    def test_nul_field_rejected(self):
        self.write("movies.dat", "701::Title\x00::Comedy\n")
        with self.assertRaises(SafeError) as caught:
            list(raw_rows(self.raw, "movies_raw"))
        self.assertEqual(caught.exception.code, "EMPTY_OR_NUL_FIELD")

    def test_error_message_does_not_echo_row(self):
        self.write("ratings.dat", "fixture_private_marker\n")
        with self.assertRaises(SafeError) as caught:
            list(raw_rows(self.raw, "ratings_raw"))
        self.assertNotIn("fixture_private_marker", str(caught.exception))

    def test_hash_and_line_count_must_both_match(self):
        self.write("README", "invented fixture\n")
        manifest = {"files": {"README": {"sha256": hashlib.sha256((self.raw / "README").read_bytes()).hexdigest(), "line_count": 1}}}
        self.assertTrue(verify_sources(self.raw, manifest)["README"]["matches"])
        manifest["files"]["README"]["line_count"] = 2
        with self.assertRaises(SafeError):
            verify_sources(self.raw, manifest)

    def test_utf8_bytes_not_accepted_as_known_latin1_source(self):
        self.write("movies.dat", "701::é::Comedy\n")
        digest = hashlib.sha256((self.raw / "movies.dat").read_bytes()).hexdigest()
        (self.raw / "movies.dat").write_text("701::é::Comedy\n", encoding="utf-8")
        with self.assertRaises(SafeError):
            verify_sources(self.raw, {"files": {"movies.dat": {"sha256": digest, "line_count": 1}}})


if __name__ == "__main__":
    unittest.main()
