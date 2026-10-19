import sys
import unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from etl.s05_staging import approved_project_views
from olap.run_olap import report_payload
from decimal import Decimal
from datetime import date, datetime, timezone


class CatalogExtensionTests(unittest.TestCase):
    def setUp(self):
        self.contract = {"dw.v_ml_" + s for s in ["users", "movies", "movie_genres", "ratings"]}
        self.core = self.contract | {"analytics.v_active_user_cluster", "analytics.v_active_cluster_genre_profile"}
        self.olap = {"analytics.v_olap_" + s for s in ["kpi", "movie_metrics", "genre_age_gender", "time_rollup", "genre_quarter", "movie_day_segment"]}

    def test_core_unchanged_accepted(self):
        self.assertTrue(approved_project_views(self.core, self.contract))

    def test_all_six_approved_accepted(self):
        self.assertTrue(approved_project_views(self.core | self.olap, self.contract))

    def test_missing_contract_rejected(self):
        self.assertFalse(approved_project_views((self.core | self.olap) - {"dw.v_ml_ratings"}, self.contract))

    def test_partial_olap_rejected(self):
        self.assertFalse(approved_project_views(self.core | {"analytics.v_olap_kpi"}, self.contract))

    def test_unknown_extra_rejected(self):
        self.assertFalse(approved_project_views(self.core | self.olap | {"analytics.v_olap_rogue"}, self.contract))

    def test_wrong_schema_rejected(self):
        self.assertFalse(approved_project_views(self.core | {x.replace("analytics.", "dw.") for x in self.olap}, self.contract))

    def test_report_numeric_precision_and_dates(self):
        value = Decimal('3.581564452139502843905623724')
        result = report_payload({'mean':value,'quarter':date(2000,7,1),'at':datetime(2000,7,1,tzinfo=timezone.utc)})
        self.assertEqual(result['mean'],str(value))
        self.assertEqual(result['quarter'],'2000-07-01')
        self.assertEqual(result['at'],'2000-07-01T00:00:00+00:00')

    def test_report_unknown_type_rejected(self):
        with self.assertRaises(TypeError):
            report_payload({'unexpected':object()})


if __name__ == "__main__":
    unittest.main()
