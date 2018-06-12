
import factory
from factory.django import DjangoModelFactory


class CompanyFactory(DjangoModelFactory):
    is_free = True

    class Meta:
        model = Company


class UserFactory(DjangoModelFactory):
    class Meta:
        model = User

    username = factory.Faker('user_name')
    first_name = factory.Faker('first_name')
    last_name = factory.Faker('last_name')
    company = factory.SubFactory(CompanyFactory)
