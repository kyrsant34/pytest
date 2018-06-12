# -*- coding: utf8 -*-

from __future__ import unicode_literals

from datetime import datetime
from django.test import TestCase


class PrintAttrsTests(TestCase):

    def setUp(self):
        self.policy = ResultPolicy(valid_from=datetime(2018, 04, 04), valid_to=datetime(2020, 04, 03))
        self.print_attrs = PrintAttrs(self.policy)

    def test_calculate_periods(self):
        expected_periods = [{'valid_from': datetime(2018, 04, 04), 'valid_to': datetime(2019, 04, 03)},
                            {'valid_from': datetime(2019, 04, 04), 'valid_to': datetime(2020, 04, 03)}]
        periods = self.print_attrs._get_periods()
        self.assertEqual(expected_periods, periods)
