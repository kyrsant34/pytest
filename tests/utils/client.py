from django.test import Client
from rest_framework.authtoken.models import Token


class AuthorizedClient(Client):
    JsonFormatter = 'JsonFormatter'

    def __init__(self, user, *args, **kwargs):
        self.user = user
        self.token, _ = Token.objects.get_or_create(user=user)
        kwargs.update({
            'HTTP_AUTHORIZATION': 'Token {token}'.format(token=self.token.key),
        })
        super(AuthorizedClient, self).__init__(*args, **kwargs)

    @classmethod
    def get_client(cls, formatter=None):
        if formatter == cls.JsonFormatter:
            return AuthorizedJsonClient
        else:
            return AuthorizedClient


class AuthorizedJsonClient(AuthorizedClient):
    def get(self, path, data=None, follow=False, **extra):
        content_type = accept = 'application/json'
        return super(AuthorizedClient, self).get(path, content_type=content_type, accept=accept, **extra)
