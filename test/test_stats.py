from unittest import TestCase
from datetime import datetime

from bin.stats import parse_date, parse_size


class StatsTest(TestCase):

    def test_parse_date(self):
        """Test `parse_date()` with known inputs."""
        s = "12:02, 28. M\u00e4r. 2018"
        r = parse_date(s)
        self.assertEqual(r, datetime(2018, 3, 28, 12, 2))
        s = "18:33, 1. Apr. 2019"
        r = parse_date(s)
        self.assertEqual(r, datetime(2019, 4, 1, 18, 33))


    def test_parse_size(self):
        """Test `parse_size()` with known inputs."""
        known = [
            ("(0)", 0),
            ("(-232)", -232),
            ("(987)", 987),
            ("null", 0),
            ("(null)", 0),
        ]
        for string, result in known:
            self.assertEqual(parse_size(string), result)
