# -*- coding: utf8 -*-

from __future__ import unicode_literals

from datetime import datetime
from faker import Faker
from mock import patch

from django.core.urlresolvers import reverse
from django.test import TestCase

from tests.factories.record import ResultFactory


class ResultPolicyCreationTests(TestCase):

    fixtures = ['result_policy_status']

    @classmethod
    def setUpClass(cls):
        super(ResultPolicyCreationTests, cls).setUpClass()
        cls.today = datetime.today().strftime('%Y-%m-%dT%H:%M')
        cls.url = reverse('policy:result_policy')
        cls.serializer_init_data = {
            'valid_from': cls.today,
            'valid_to': cls.today,
            'previous_policies': '{"a": 22}',
        }

    def setUp(self):
        self.policy = ResultPolicy(state=ResultPolicyStatus(code=ResultPolicyStatus.Code.ISSUED),
                                   valid_from=Faker().past_datetime())
        self.result = ResultFactory()
        self.serializer_init_data['result'] = self.result.id

    def test_creation_failed_by_previous_policies(self):
        patcher = patch('apps.policy.rest2.serializers.ResultPolicyCreateUpdateDestroySerializer.validate_insured_object',
              side_effect=lambda attrs, source: attrs)
        patcher.start()

        self.serializer_init_data.update(dict(previous_policies='{"a": 22'))
        s = ResultPolicyCreateUpdateDestroySerializer(data=self.serializer_init_data)
        self.assertFalse(s.is_valid())
        self.assertTrue('previous_policies' in s.errors)
        patcher.stop()

    def test_creation_by_previous_policies(self):
        for path, se in (
                ('apps.policy.rest2.serializers.ResultPolicyCreateUpdateDestroySerializer.validate_insured_object',
                lambda attrs, source: attrs),
                ('apps.policy.rest2.serializers.ResultPolicyCreateUpdateDestroySerializer.validate',
                lambda attrs: attrs)
        ):
            patch(path, side_effect=se).start()

        s = ResultPolicyCreateUpdateDestroySerializer(data=self.serializer_init_data)
        self.assertTrue(s.is_valid())
        patch.stopall()

    def test_is_annulment_allowed_true(self):
        self.assertTrue(self.policy.is_annulment_allowed)

    def test_is_annulment_allowed_fail_state(self):
        self.policy.valid_from = Faker().past_datetime()
        self.policy.state = ResultPolicyStatus.objects.get(code=ResultPolicyStatus.Code.SAVED)
        self.assertFalse(self.policy.is_annulment_allowed)

    def test_is_annulment_allowed_when_valid_from_equal_future_date(self):
        self.policy.valid_from = Faker().future_datetime()
        self.assertFalse(self.policy.is_annulment_allowed)

    def test_is_annulment_allowed_when_valid_from_equal_today(self):
        self.policy.valid_from = datetime.today()
        self.assertFalse(self.policy.is_annulment_allowed)

    def test_is_annulment_allowed_without_valid_from_date(self):
        self.policy.valid_from = None
        self.assertFalse(self.policy.is_annulment_allowed)
