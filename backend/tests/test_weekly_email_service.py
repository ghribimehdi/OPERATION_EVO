import sys
from pathlib import Path
import unittest

sys.path.append(str(Path(__file__).resolve().parents[1]))

from database.db import init_db
from services.email_service import build_weekly_system_summary


class WeeklyEmailServiceTestCase(unittest.TestCase):
    def setUp(self):
        init_db()

    def test_build_weekly_system_summary_contains_summary_sections(self):
        summary = build_weekly_system_summary()
        self.assertIn('Résumé hebdomadaire', summary)
        self.assertIn('Tickets', summary)
        self.assertIn('Évolution', summary)


if __name__ == '__main__':
    unittest.main()
