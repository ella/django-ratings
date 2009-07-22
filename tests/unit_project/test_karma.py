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
        self.assert_equals((self.user, 1), karma.sources.get_owner(self.user))

    def test_raises_error_on_double_registration_with_different_weights(self):
        f = lambda u:u
        karma.sources.register(User, f, 100)
        self.assert_raises(ImproperlyConfigured, karma.sources.register, User, f, 10)

    def test_raises_error_on_double_registration_with_different_getters(self):
        karma.sources.register(User, lambda u:u)
        self.assert_raises(ImproperlyConfigured, karma.sources.register, User, lambda u: u.pk)

    def test_weight_gets_matched_correctly(self):
        karma.sources.register(User, lambda u:u, 100)
        self.assert_equals((self.user, 100), karma.sources.get_owner(self.user))

    def test_double_registration_works_for_same_values(self):
        f = lambda u:u
        karma.sources.register(User, f, 100)
        karma.sources.register(User, f, 100)
        self.assert_equals((self.user, 100), karma.sources.get_owner(self.user))

