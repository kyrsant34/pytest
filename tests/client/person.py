# -*- coding: utf8 -*-

from __future__ import unicode_literals
from datetime import date

from django.contrib.contenttypes.models import ContentType
from django.test import TestCase
from rest_framework import serializers

from tests.factories.account import UserFactory
from tests.factories.person import NaturalPersonFactory, LegalPersonFactory


class CreatorFieldTests(TestCase):
    def setUp(self):
        self.user = UserFactory()
        self.np = NaturalPersonFactory(creator=self.user)
        self.np.save()

    def test_credential_creator_field(self):
        cred_type = CredentialTypeFactory()
        cred_type.save()
        cred = CredentialFactory(content_object=self.np, credential_type=cred_type, creator=self.user)
        cred.save()

        serializer = CredentialSerializer(Credential.objects.all(), many=True)

        expected = [
            {
                'id': 1,
                'creator': self.user.id,
                'content_type': ContentType.objects.get_for_model(NaturalPerson).id,
                'object_id': self.np.id,
                'external_id': None,
                'number': u'',
                'series': u'',
                'credential_type': cred_type.id,
                'issue_date': None,
                'issue_point': None,
                'expiration_date': None
            },
        ]
        self.assertEqual(serializer.data, expected)

    def test_contact_creator_field(self):
        contact_type = ContactTypeFactory()
        contact_type.save()
        data = '123456'
        contact = ContactFactory(content_object=self.np, contact_type=contact_type, creator=self.user, data=data)
        contact.save()

        serializer = ContactSerializer(Contact.objects.all(), many=True)

        expected = [
            {
                'creator': self.user.id,
                'id': 1,
                'notes': None,
                'content_type': ContentType.objects.get_for_model(NaturalPerson).id,
                'object_id': self.np.id,
                'contact_type': contact_type.id,
                'data': data
            },
        ]
        self.assertEqual(serializer.data, expected)


class PersonsValidationTests(TestCase):

    @classmethod
    def setUpClass(cls):
        cls.today = date.today()
        super(PersonsValidationTests, cls).setUpClass()

    def setUp(self):
        self.user = UserFactory()

    def test_get_beneficiary_by_natural_person(self):
        np = NaturalPersonFactory()
        person = np.person_set.create(creator=self.user, beneficiary='банк')
        s = NaturalPersonListSerializer(instance=np)
        self.assertEqual(s.data['beneficiary'], person.beneficiary)

    def test_get_beneficiary_by_legal_person(self):
        le = LegalPersonFactory()
        person = le.person_set.create(creator=self.user, beneficiary='банк')
        s = LegalPersonListSerializer(instance=le)
        self.assertEqual(s.data['beneficiary'], person.beneficiary)

    def test_inn_length_success(self):
        inn = '0' * 10
        attrs = dict(inn=inn)
        self.assertEqual(attrs, LegalPersonListSerializer().validate_inn(attrs, 'inn'))

    def test_inn_length_fail(self):
        inn = '0' * 8
        s = LegalPersonListSerializer()
        with self.assertRaises(serializers.ValidationError) as cm:
            s.validate_inn(dict(inn=inn), 'inn')
        self.assertEqual(s.ERROR_MESSAGES['INVALID_INN_LENGTH'].format(10), cm.exception.message)

    def test_beneficiary_natural_person(self):
        np = NaturalPersonFactory()
        person = np.person_set.create(creator=self.user, beneficiary='банк')
        s = DeepNaturalPersonSerializer(instance=np)
        self.assertEqual(s.data['beneficiary'], person.beneficiary)

    def test_beneficiary_legal_person(self):
        le = LegalPersonFactory()
        person = le.person_set.create(creator=self.user, beneficiary='банк')
        s = DeepLegalPersonSerializer(instance=le)
        self.assertEqual(s.data['beneficiary'], person.beneficiary)

    def test_driving_expitience_by_deep_natural_person_serializer(self):
        np = NaturalPersonFactory(driving_experience=2)
        s = DeepNaturalPersonSerializer(instance=np)
        self.assertEqual(s.data['driving_experience'], np.driving_experience)

    def test_driving_expitience_natural_person_list_serializer(self):
        np = NaturalPersonFactory(driving_experience=2)
        s = NaturalPersonListSerializer(instance=np)
        self.assertEqual(s.data['driving_experience'], np.driving_experience)
