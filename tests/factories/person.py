from factory import DjangoModelFactory, SubFactory, Faker

from tests.factories.account import UserFactory


class PersonFactory(DjangoModelFactory):
    creator = SubFactory(UserFactory)

    class Meta:
        model = Person


class NaturalPersonFactory(DjangoModelFactory):
    creator = SubFactory(UserFactory)
    first_name = Faker('first_name')
    last_name = Faker('last_name')

    class Meta:
        model = NaturalPerson
