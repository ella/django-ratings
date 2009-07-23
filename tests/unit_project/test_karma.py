from django.contrib.auth.models import User, UNUSABLE_PASSWORD
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import ImproperlyConfigured

from django_ratings import karma
from django_ratings.models import TotalRate, UserKarma

from helpers import SimpleRateTestCase

class KarmaTestCase(SimpleRateTestCase):
    def setUp(self):
        super(KarmaTestCase, self).setUp()
        self.user = User.objects.create(
                username='some_username',
                password=UNUSABLE_PASSWORD
            )

    def tearDown(self):
        super(KarmaTestCase, self).tearDown()
        karma.sources = karma.KarmaSources()

class TestKarmaCalculation(KarmaTestCase):
    def setUp(self):
        super(TestKarmaCalculation, self).setUp()
        karma.sources.register(ContentType, lambda u: self.user)

    def test_karma_doesnt_get_created_when_no_applicable_ratings(self):
        UserKarma.objects.total_rate_to_karma()
        self.assert_equals(0, UserKarma.objects.count())

    def test_karma_gets_created_with_weight_for_appropriate_total_rate(self):
        karma.sources.register(User, lambda u: self.user, 2)
        TotalRate.objects.create(amount=100, target_ct=ContentType.objects.get_for_model(User), target_id=self.user.pk)
        UserKarma.objects.total_rate_to_karma()

        self.assert_equals(1, UserKarma.objects.count())
        k = UserKarma.objects.all()[0]
        self.assert_equals(self.user, k.user)
        self.assert_equals(200,  k.karma)

    def test_karma_gets_created_for_appropriate_total_rate(self):
        TotalRate.objects.create(amount=100, **self.kw)
        UserKarma.objects.total_rate_to_karma()

        self.assert_equals(1, UserKarma.objects.count())
        k = UserKarma.objects.all()[0]
        self.assert_equals(self.user, k.user)
        self.assert_equals(100,  k.karma)

    def test_calculate_can_cope_with_existing_karmas(self):
        UserKarma.objects.create(user=self.user, karma=10000)
        TotalRate.objects.create(amount=100, **self.kw)
        UserKarma.objects.total_rate_to_karma()

        self.assert_equals(1, UserKarma.objects.count())
        k = UserKarma.objects.all()[0]
        self.assert_equals(self.user, k.user)
        self.assert_equals(100,  k.karma)


class TestKarmaSources(KarmaTestCase):

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

    def test_get_contenttypes_is_empty_on_empty_sources(self):
        self.assert_equals([], karma.sources.registered_content_types())

    def test_get_contenttypes_returns_registered_models(self):
        karma.sources.register(User, lambda u:u)
        karma.sources.register(ContentType, lambda u:u)
        self.assert_equals(
                sorted([
                        ContentType.objects.get_for_model(User),
                        ContentType.objects.get_for_model(ContentType)
                        ]),
                sorted(karma.sources.registered_content_types())
            )

