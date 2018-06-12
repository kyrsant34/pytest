# -*- coding: utf8 -*-

from __future__ import unicode_literals

import factory
from factory.django import DjangoModelFactory
from mock import patch


class ProlongationFactory(DjangoModelFactory):
    class Meta:
        model = Prolongation


class DeductibleTypeFactory(DjangoModelFactory):
    code = factory.Sequence('DeductibleType #{}'.format)

    class Meta:
        model = DeductibleType


class FranchiseFactory(DjangoModelFactory):
    title = factory.Sequence('Title #{}'.format)
    group = factory.SubFactory(DeductibleTypeFactory)

    class Meta:
        model = Franchise


class RecordFactory(DjangoModelFactory):
    deductible_value = factory.SubFactory(FranchiseFactory)

    class Meta:
        model = Record


@patch('apps.billing.models.DayResource')
def MockedRecordFactory(mocked_obj, *args, **kwargs):
    return RecordFactory(*args, **kwargs)


class ResultFactory(factory.DjangoModelFactory):
    record = factory.SubFactory(RecordFactory)
    insurance_company = factory.SubFactory(InsuranceCompanyFactory)

    class Meta:
        model = Result


class RecordOptionalEquipmentFactory(DjangoModelFactory):
    cost = 300000
    type = factory.SubFactory(OptionalEquipmentFactory)
    insurance_amount = 50000
    record = factory.SubFactory(RecordFactory)

    class Meta:
        model = RecordOptionalEquipment
