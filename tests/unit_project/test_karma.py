from djangosanetesting import DatabaseTestCase

from django.contrib.auth.models import User, UNUSABLE_PASSWORD
from django.core.exceptions import ImproperlyConfigured

from django_ratings import karma

class TestKarmaSources(DatabaseTestCase):
    def setUp(self):
        super(TestKarmaSources, self).setUp()
        self.user, created = User.objects.get_or_create(
                username='some_username',
                defaults={'password': UNUSABLE_PASSWORD}
            )

    def tearDown(self):
        super(TestKarmaSources, self).tearDown()
        karma.sources = karma.KarmaSources()

    def test_return_none_for_non_registered_model(self):
        self.assert_equals(None, karma.sources.get_owner(self.user))

    def test_returns_owner_for_registered_model(self):
        karma.sources.register(User, lambda u:u)
        self.assert_equals(self.user, karma.sources.get_owner(self.user))

    def test_raises_error_on_double_registration(self):
        karma.sources.register(User, lambda u:u)
        self.assert_raises(ImproperlyConfigured, karma.sources.register, User, lambda u: u.pk)

