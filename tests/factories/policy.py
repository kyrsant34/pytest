import factory
from factory import DjangoModelFactory
from mock import patch

from .account import UserFactory
from .record import ResultFactory


class ResultPolicyFactory(DjangoModelFactory):
    valid_to = factory.Faker('future_date')
    result = factory.SubFactory(ResultFactory)
    creator = factory.SubFactory(UserFactory)

    class Meta:
        model = ResultPolicy

@patch('apps.policy.models.Backend.synchronize')
def MockedResultPolicyFactory(mocked_obj, *args, **kwargs):
    return ResultPolicyFactory(*args, **kwargs)
