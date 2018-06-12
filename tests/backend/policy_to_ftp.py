# -*- coding: utf8 -*-

from __future__ import unicode_literals
from datetime import datetime
from mock import patch, Mock

from django.test import TestCase

from tests.factories.account import UserFactory
from tests.factories.record import MockedRecordFactory, ResultFactory, RecordOptionalEquipmentFactory
from tests.factories.policy import MockedResultPolicyFactory
from tests.factories.person import PersonFactory, NaturalPersonFactory



class FTPAttrsTests(TestCase):

    fixtures = ['result_policy_status']

    def setUp(self):
        self.record = MockedRecordFactory()
        self.result = ResultFactory(record=self.record)
        self.storage = ResultStorage.objects.create(result=self.result)
        self.insured_object = InsuredObjectFactory()
        self.policy = MockedResultPolicyFactory(result=self.result, insured_object=self.insured_object)
        self.ftp_attrs = self._create_ftp_attrs()

    def _create_ftp_attrs(self):
        with patch('apps.policy.utils.FTPAttrs._validate_policy'):
            return FTPAttrs(self.policy)


class FTPAttrsValidateTests(FTPAttrsTests):

    ERROR_MESSAGE = u'Для получения атрибутов {cls} необходим {param} (policy_id={policy_id})'

    def setUp(self):
        super(FTPAttrsValidateTests, self).setUp()
        self.car = CarFactory()
        self.insured_object.object = self.car
        self.policy.pnumber = '5/12/002765/КАЗ/17'

    def test_success(self):
        self.ftp_attrs._validate_policy()

    def test_invalid_result(self):
        self.ftp_attrs.policy.result = None
        with self.assertRaises(BackendValidationError) as context:
            self.ftp_attrs._validate_policy()
        expected_msg = self.ERROR_MESSAGE.format(cls=FTPAttrs, policy_id=self.policy.id, param=self.result.__class__)
        self.assertEqual(expected_msg, unicode(context.exception), context.exception)

    def test_invalid_storage(self):
        ResultStorage.objects.all().delete()
        with self.assertRaises(BackendValidationError) as context:
            self.ftp_attrs._validate_policy()
        expected_msg = self.ERROR_MESSAGE.format(cls=FTPAttrs, policy_id=self.policy.id, param=self.storage.__class__)
        self.assertEqual(expected_msg, unicode(context.exception), context.exception)

    def test_invalid_insured_object(self):
        self.ftp_attrs.policy.insured_object = None
        with self.assertRaises(BackendValidationError) as context:
            self.ftp_attrs._validate_policy()
        expected_msg = self.ERROR_MESSAGE.format(cls=FTPAttrs, policy_id=self.policy.id,
                                                 param=self.insured_object.__class__)
        self.assertEqual(expected_msg, unicode(context.exception), context.exception)

    def test_invalid_pnumber(self):
        self.ftp_attrs.policy.pnumber = None
        with self.assertRaises(BackendValidationError) as context:
            self.ftp_attrs._validate_policy()
        expected_msg = self.ERROR_MESSAGE.format(cls=FTPAttrs, policy_id=self.policy.id, param='pnumber')
        self.assertEqual(expected_msg, unicode(context.exception), context.exception)


class FTPAttrsPolicyTests(FTPAttrsTests):

    def setUp(self):
        super(FTPAttrsPolicyTests, self).setUp()
        self.previous_policies = '111, 000'
        self.natural_person = NaturalPersonFactory()
        self.beneficiary = PersonFactory(natural_person=self.natural_person)
        self.insured_object.beneficiary = self.beneficiary
        self.creator = UserFactory()
        self.policy.creator = self.creator
        self.policy.valid_from = datetime(2018, 5, 5, 5, 5, 5)
        self.policy.valid_to = datetime(2019, 4, 4, 5, 5, 5)
        self.policy.created = self.policy.valid_from

    def test_policy_attrs(self):
        series = '11'
        number = '22'
        self.ftp_attrs._get_number_and_series = Mock(return_value=(series, number))
        self.ftp_attrs._get_previous_policies = Mock(return_value=self.previous_policies)
        self.ftp_attrs._get_valid_from_and_valid_to = Mock(return_value=(self.policy.valid_from, self.policy.valid_to))

        expected_attrs = {
            'policy': self.policy,
            'created': '2018-05-05T05:05:05',
            'valid_from': '2018-05-05T05:05:05',
            'valid_to': '2019-04-04T05:05:05',
            'days_duration': 335,
            'number': number,
            'series': series,
            'beneficiary': self.natural_person,
            'creator_full_name': self.creator.get_full_name(),
            'previous_policies': self.previous_policies,
        }

        attrs = self.ftp_attrs._get_policy_attrs()
        self.assertDictEqual(expected_attrs, attrs)

    def test_number_and_series(self):
        self.policy.pnumber = '5/12/002765/КАЗ/17'
        series, number = self.ftp_attrs._get_number_and_series()
        self.assertEqual(series, '5/12/-КАЗ/17')
        self.assertEqual(number, '002765')

    def test_dict_previous_policies(self):
        self.policy.previous_policies = {'0': '312', '1': '555'}
        previous_policies = self.ftp_attrs._get_previous_policies()
        self.assertIn(previous_policies, ('312, 555', '555, 312'))

    def test_list_previous_policies(self):
        self.policy.previous_policies = ['312', '555']
        previous_policies = self.ftp_attrs._get_previous_policies()
        self.assertEqual(previous_policies, '312, 555')

    def test_str_previous_policies(self):
        self.policy.previous_policies = '312, 555'
        previous_policies = self.ftp_attrs._get_previous_policies()
        self.assertEqual(previous_policies, '')

    def test_valid_from_and_valid_to(self):
        months_duration = 11
        self.policy.valid_to = None
        self.record.insurance_duration = InsuranceDurationFactory(months=months_duration)
        valid_from, valid_to = self.ftp_attrs._get_valid_from_and_valid_to()
        self.assertEqual(valid_from, self.policy.valid_from)
        self.assertEqual(valid_to, datetime(2019, 4, 4, 5, 5, 5))


class FTPAttrsRecordTests(FTPAttrsTests):

    def setUp(self):
        super(FTPAttrsRecordTests, self).setUp()
        self.optional_equipment = RecordOptionalEquipmentFactory(record=self.record)

    def test_record(self):
        self.record.insurance_sum = 700000
        attrs = self.ftp_attrs._get_record_attrs()
        self.assertEqual(self.record, attrs['record'])

    def test_risk_insurance_sum(self):
        insurance_premium = 111
        self.ftp_attrs.storage.data = {'Skasko': insurance_premium}
        attrs = self.ftp_attrs._get_record_attrs()
        expected_attrs = {
            'insurance_sum': self.record.insurance_sum,
            'title': self.record.insurance_type.title,
            'insurance_premium': insurance_premium
        }
        self.assertIn(expected_attrs, attrs['risks'])

    def test_risk_car_cost(self):
        self.record.is_calculate_gap = True
        self.record.car_cost = 500000
        insurance_premium = 222
        self.ftp_attrs.storage.data = {'Sgap': insurance_premium}
        attrs = self.ftp_attrs._get_record_attrs()
        expected_attrs = {
                'insurance_sum': self.record.car_cost,
                'title': InsuranceType.objects.get(code=InsuranceType.Code.GAP).title,
                'insurance_premium': insurance_premium
        }
        self.assertIn(expected_attrs, attrs['risks'])

    def test_risk_casualty_cost(self):
        self.record.is_accident_insured = True
        self.record.casualty_cost = 5000
        insurance_premium = 333
        self.ftp_attrs.storage.data = {'Sns': insurance_premium}
        attrs = self.ftp_attrs._get_record_attrs()
        expected_attrs = {
            'insurance_sum': self.record.casualty_cost,
            'title': InsuranceType.objects.get(code=InsuranceType.Code.NS).title,
            'insurance_premium': insurance_premium
        }
        self.assertIn(expected_attrs, attrs['risks'])

    def test_risk_help_in_casualty_cost(self):
        self.record.help_in_casualty = HelpInCasualtyFactory()
        self.record.help_in_casualty_cost = 100000
        insurance_premium = 444
        self.ftp_attrs.storage.data = {'Sdgo': insurance_premium}
        attrs = self.ftp_attrs._get_record_attrs()
        expected_attrs = {
            'insurance_sum': self.record.help_in_casualty_cost,
            'title': InsuranceType.objects.get(code=InsuranceType.Code.DTP).title,
            'insurance_premium': insurance_premium
        }
        self.assertIn(expected_attrs, attrs['risks'])

    def test_risk_optional_equipment(self):
        self.record.is_optional_equipment_insured = True
        insurance_premium = 555
        self.ftp_attrs.storage.data = {'Sdo': insurance_premium}
        attrs = self.ftp_attrs._get_record_attrs()
        expected_attrs = {
            'insurance_sum': self.optional_equipment.insurance_amount,
            'title': u'Доп. оборудование',
            'insurance_premium': insurance_premium
        }
        self.assertIn(expected_attrs, attrs['risks'])

    def test_insurance_program_title(self):
        title = 'MULTI'
        with patch('apps.policy.utils.FTPAttrs._get_insurance_program_title', Mock(return_value=title)):
            attrs = self.ftp_attrs._get_record_attrs()
        self.assertEqual(title, attrs['insurance_program_title'])

    def test_deductible_value(self):
        self.record.deductible_value.title = '16 000 руб'
        deductible_value = self.ftp_attrs._get_deductible_value(self.record)
        self.assertEqual('16000', deductible_value)

    def test_empty_deductible_value(self):
        self.record.deductible_value = None
        deductible_value = self.ftp_attrs._get_deductible_value(self.record)
        self.assertEqual('', deductible_value)

    def test_insurance_program_title_with_not_kasco(self):
        self.record.insurance_type = InsuranceType.get_by_code(InsuranceType.Code.DTP)
        res = self.ftp_attrs._get_insurance_program_title()
        self.assertEqual(res, '')

    def test_insurance_program_title_without_insurance_program_group(self):
        self.record.insurance_type = InsuranceType.get_by_code(InsuranceType.Code.KASKO)
        self.record.insurance_program_group = None
        res = self.ftp_attrs._get_insurance_program_title()
        self.assertEqual(res, '')

    def test_insurance_program_title_with_special_insurance_program_group(self):
        self.record.insurance_type = InsuranceType.get_by_code(InsuranceType.Code.KASKO)
        self.record.insurance_program_group = InsuranceProgramGroupFactory(
                                                            code=InsuranceProgramGroup.Code.SPECIAL_PROGRAM)
        self.record.insurance_program = InsuranceProgramFactory(title='first program',
                                                                     group=self.record.insurance_program_group)
        res = self.ftp_attrs._get_insurance_program_title()
        self.assertEqual(res, self.record.insurance_program.title)

    def test_insurance_program_title_with_not_special_insurance_program_group(self):
        self.record.insurance_type = InsuranceType.get_by_code(InsuranceType.Code.KASKO)
        self.record.insurance_program_group = InsuranceProgramGroupFactory(code='NOT_SPECIAL',
                                                                                title='first group')
        res = self.ftp_attrs._get_insurance_program_title()
        self.assertEqual(res, self.record.insurance_program_group.title)


class FTPAttrsCarTests(FTPAttrsTests):

    def setUp(self):
        super(FTPAttrsCarTests, self).setUp()

        self.car_mark = CarMarkFactory(title='BMW')
        self.car_model_group = CarModelGroupFactory(title='46')
        self.car_model = CarModelFactory(rsa_car_id='111', car_mark=self.car_mark, car_model_group=self.car_model_group)

        self.car = CarFactory(car_model=self.car_model, car_mark=self.car_mark)

        self.credential = CredentialFactory(credential_type=CredentialType.objects.get(
                                                                    code=CredentialType.VEHICLE_REGISTRATION),
                                            content_object=self.car)
        self.insured_object.object = self.car

    def test_success(self):
        attrs = self.ftp_attrs._get_car_attrs()
        expected_attrs = {
            'car': self.car,
            'car_mark_model': '{mark} {model_group}'.format(mark=self.car_mark.title,
                                                            model_group=self.car_model_group.title),
            'rsa_car_id': self.car_model.rsa_car_id,
            'car_credential': self.credential
        }
        self.assertDictEqual(expected_attrs, attrs)

    def test_without_car_mark(self):
        self.car.car_mark = None
        attrs = self.ftp_attrs._get_car_attrs()
        expected_attrs = {
            'car': self.car,
        }
        self.assertDictEqual(expected_attrs, attrs)

    def test_without_car_model(self):
        self.car.car_model = None
        attrs = self.ftp_attrs._get_car_attrs()
        expected_attrs = {
            'car': self.car,
        }
        self.assertDictEqual(expected_attrs, attrs)
    #
    def test_without_car_group_model(self):
        self.car_model.car_model_group = None
        attrs = self.ftp_attrs._get_car_attrs()
        expected_attrs = {
            'car': self.car,
        }
        self.assertDictEqual(expected_attrs, attrs)
