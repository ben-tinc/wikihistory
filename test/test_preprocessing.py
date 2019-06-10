from unittest import TestCase
from datetime import datetime as dt

import pandas as pd
from pandas import DataFrame, Series
import numpy as np

from lib.preprocessing import (
    parse_date,
    parse_size,
    is_IP,
    revert_heuristic,
    probably_revert,
    probably_reverted,
)


class ParsingTest(TestCase):
    """Test the basic data parsing functions."""

    def test_parse_date(self):
        """Test `parse_date()` with known inputs."""
        s = "12:02, 28. M\u00e4r. 2018"
        r = parse_date(s)
        self.assertEqual(r, dt(2018, 3, 28, 12, 2))
        s = "18:33, 1. Apr. 2019"
        r = parse_date(s)
        self.assertEqual(r, dt(2019, 4, 1, 18, 33))


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

    def test_is_IP(self):
        known_IPs = [
            '127.0.0.1',
            '192.168.1.1',
            '23.4.182.38',
            '2001:0db8:85a3:08d3:1319:8a2e:0370:7344',
            '2001:db8:0:8d3:0:8a2e:70:7344', # leading 0s can be left out
        ]
        for ip in known_IPs:
            self.assertTrue(is_IP(ip))

    def test_is_not_IP(self):
        known_non_IPs = [
            '',
            '127.0.0',
            '127.0.0.1.1',
            'abc.abc.0.1',
            '127:0:0:1',
            '2001:0db8:85a3:08d3:1319:8a2e:0370:7344:2351',
        ]
        for non_ip in known_non_IPs:
            self.assertFalse(is_IP(non_ip))



class RevertHeuristicTest(TestCase):
    """Check that `revert_heuristic()` yields the correct result for
    a single row of data.
    """

    def test_normal(self):
        """Normal revert."""
        data = {
            'name': 'Name 1',
            'cmp_name': 'Name 1',
            'change': 12,
            'cmp_change': -12,
            'early_dt': dt(2019, 1, 1, 12, 0),
            'late_dt': dt(2019, 1, 3, 12, 0),
            'later_revert': False,
        }
        self.assertTrue(revert_heuristic(**data))

    def test_revert_field(self):
        """Revert marked by an revert field."""
        data = {
            'name': 'Name 1',
            'cmp_name': 'Name 2',
            'change': 12,
            'cmp_change': 24,
            'early_dt': dt(2019, 1, 1, 12, 0),
            'late_dt': dt(2019, 1, 3, 12, 0),
            'later_revert': True,
        }
        self.assertTrue(revert_heuristic(**data))

    def test_no_revert(self):
        """ Normal non-revert."""
        data = {
            'name': 'Name 1',
            'cmp_name': 'Name 1',
            'change': 12,
            'cmp_change': 24,
            'early_dt': dt(2019, 1, 1, 12, 0),
            'late_dt': dt(2019, 1, 3, 12, 0),
            'later_revert': False,
        }
        self.assertFalse(revert_heuristic(**data))

    def test_different_pagenames(self):
        """ Non-revert because varying pagenames."""
        data = {
            'name': 'Name 1',
            'cmp_name': 'Name 2',
            'change': 12,
            'cmp_change': -12,
            'early_dt': dt(2019, 1, 1, 12, 0),
            'late_dt': dt(2019, 1, 3, 12, 0),
            'later_revert': False,
        }
        self.assertFalse(revert_heuristic(**data))

    def test_NaN_values(self):
        """ Handle NaN values correctly."""
        data = {
            'name': 'Name 1',
            'change': 12,
            'early_dt': dt(2019, 12, 31, 12, 0),
            'cmp_name': np.NaN,
            'cmp_change': np.NaN,
            'late_dt': pd.NaT,
            'later_revert': np.NaN,
        }
        self.assertFalse(revert_heuristic(**data))


class ProbablyRevertTest(TestCase):
    """Test cases for the `probably_revert()` function."""

    def test_no_revert(self):
        """Check that `probably_revert()` yields the correct results for all
        rows of a known data frame.
        """
        # No reverts at all.
        df = DataFrame([
            ['Name 1', 12, dt(2019, 12, 31, 12), False],
            ['Name 1', 14, dt(2019, 12, 30, 12), False],
            ['Name 1', 18, dt(2019, 12, 29, 12), False],
            ['Name 1', 22, dt(2019, 12, 28, 12), False],],
            columns=['pagename', 'change_size', 'date', 'revert'])
        result = probably_revert(df)
        self.assertFalse(result.any())

    def test_revert_field(self):
        """ Some default reverts."""
        df = DataFrame([
            ['Name 1', 12, dt(2019, 12, 31, 12), False],
            ['Name 1', 14, dt(2019, 12, 30, 12), True],
            ['Name 1', 18, dt(2019, 12, 29, 12), True],
            ['Name 1', 22, dt(2019, 12, 28, 12), False],],
            columns=['pagename', 'change_size', 'date', 'revert'])
        result = probably_revert(df)
        self.assertTrue((result == Series([False, True, True, False])).all())

    def test_regular_reverts(self):
        """Two regular reverts."""
        df = DataFrame([
            ['Name 1', 12, dt(2019, 12, 31, 12), False],
            ['Name 1', -12, dt(2019, 12, 30, 12), False],
            ['Name 1', -18, dt(2019, 12, 29, 12), False],
            ['Name 1', 18, dt(2019, 12, 28, 12), False],],
            columns=['pagename', 'change_size', 'date', 'revert'])
        result = probably_revert(df)
        self.assertTrue((result == Series([True, False, True, False])).all())

    def test_different_pagenames(self):
        """No reverts, because pagenames do not correspond."""
        df = DataFrame([
            ['Name 1', 12, dt(2019, 12, 31, 12), False],
            ['Name 2', -12, dt(2019, 12, 30, 12), False],
            ['Name 2', -18, dt(2019, 12, 29, 12), False],
            ['Name 3', 18, dt(2019, 12, 28, 12), False],],
            columns=['pagename', 'change_size', 'date', 'revert'])
        result = probably_revert(df)
        self.assertFalse(result.any())

    def test_revert_field_vs_pagenames(self):
        """Only one revert, because of default criterion."""
        df = DataFrame([
            ['Name 1', 12, dt(2019, 12, 31, 12), False],
            ['Name 2', -12, dt(2019, 12, 30, 12), False],
            ['Name 2', -18, dt(2019, 12, 29, 12), True],
            ['Name 3', 18, dt(2019, 12, 28, 12), False],],
            columns=['pagename', 'change_size', 'date', 'revert'])
        result = probably_revert(df)
        self.assertTrue((result == Series([False, False, True, False])).all())


class ProbablyRevertedTest(TestCase):
    """Check that `probably_reverted()` yields the correct results for all
    rows of a known data frame.
    """

    def test_no_reverted(self):
        """No reverts at all, so no reverted as well."""
        df = DataFrame([
            ['Name 1', 12, dt(2019, 12, 31, 12), False],
            ['Name 1', 14, dt(2019, 12, 30, 12), False],
            ['Name 1', 18, dt(2019, 12, 29, 12), False],
            ['Name 1', 22, dt(2019, 12, 28, 12), False],],
            columns=['pagename', 'change_size', 'date', 'revert'])
        result = probably_reverted(df)
        self.assertFalse(result.any())

    def test_revert_field(self):
        """Some default reverts."""
        df = DataFrame([
            ['Name 1', 12, dt(2019, 12, 31, 12), False],
            ['Name 1', 14, dt(2019, 12, 30, 12), True],
            ['Name 1', 18, dt(2019, 12, 29, 12), True],
            ['Name 1', 22, dt(2019, 12, 28, 12), False],],
            columns=['pagename', 'change_size', 'date', 'revert'])
        result = probably_reverted(df)
        expected = Series([False, False, True, True])
        self.assertTrue((result == expected).all())

    def test_regular_reverted(self):
        """Regular reverts should result in the previous edit being marked as
        reverted (the previous edit is always in the _following_ row).
        """
        df = DataFrame([
            ['Name 1', 12, dt(2019, 12, 31, 12), False],
            ['Name 1', -12, dt(2019, 12, 30, 12), False],
            ['Name 1', -18, dt(2019, 12, 29, 12), False],
            ['Name 1', 18, dt(2019, 12, 28, 12), False],],
            columns=['pagename', 'change_size', 'date', 'revert'])
        result = probably_reverted(df)
        expected = Series([False, True, False, True])
        self.assertTrue((result == expected).all())

    def test_different_pagenames(self):
        """Differing pagenames should prevent either edit to get marked as
        reverted, unless the revert field is set.
        """
        # All edits are non-reverts because of differing pagenames.
        df = DataFrame([
            ['Name 1', 12, dt(2019, 12, 31, 12), False],
            ['Name 2', -12, dt(2019, 12, 30, 12), False],
            ['Name 2', -18, dt(2019, 12, 29, 12), False],
            ['Name 3', 18, dt(2019, 12, 28, 12), False],],
            columns=['pagename', 'change_size', 'date', 'revert'])
        result = probably_revert(df)
        self.assertFalse(result.any())

        # The revert field results in the previous edit as being reverted.
        df = DataFrame([
            ['Name 1', 12, dt(2019, 12, 31, 12), False],
            ['Name 2', -12, dt(2019, 12, 30, 12), False],
            ['Name 2', -18, dt(2019, 12, 29, 12), True],
            ['Name 3', 18, dt(2019, 12, 28, 12), False],],
            columns=['pagename', 'change_size', 'date', 'revert'])
        result = probably_revert(df)
        expected = Series([False, False, False, True])
        self.assertFalse((result == expected).all())
