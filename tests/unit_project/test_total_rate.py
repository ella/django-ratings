from djangosanetesting.cases import DatabaseTestCase

from django.contrib.contenttypes.models import ContentType

from djangoratings.models import TotalRate, Rating

class TestTotalRate(DatabaseTestCase):
    def setUp(self):
        super(TestTotalRate, self).setUp()
        self.obj = ContentType.objects.get_for_model(ContentType)

    def test_default_rating_of_an_object(self):
        self.assert_equals(0, TotalRate.objects.get_for_object(self.obj))
        
    def test_rating_propagates_to_total_rate(self):
        Rating.objects.create(
                target_ct=ContentType.objects.get_for_model(self.obj),
                target_id=self.obj.pk,
                amount=10
            )
        self.assert_equals(10, TotalRate.objects.get_total_rating(self.obj))
        
class TestRating(DatabaseTestCase):
    def setUp(self):
        super(TestRating, self).setUp()
        self.obj = ContentType.objects.get_for_model(ContentType)

    def test_default_rating_of_an_object(self):
        self.assert_equals(0, Rating.objects.get_for_object(self.obj))
        
    def test_rating_shows_in_get_for_model(self):
        Rating.objects.create(
                target_ct=ContentType.objects.get_for_model(self.obj),
                target_id=self.obj.pk,
                amount=10
            )

        self.assert_equals(10, Rating.objects.get_for_object(self.obj))
        
