from djangosanetesting.cases import DatabaseTestCase

from django.contrib.contenttypes.models import ContentType

from django_ratings.models import TotalRate, Rating
from django_ratings import aggregation

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
        self.assert_equals(10, TotalRate.objects.get_for_object(self.obj))

        
    def test_rating_propagates_to_total_rate_even_for_existing_totalrate(self):
        TotalRate.objects.create(
                target_ct=ContentType.objects.get_for_model(self.obj),
                target_id=self.obj.pk,
                amount=100
            )
        Rating.objects.create(
                target_ct=ContentType.objects.get_for_model(self.obj),
                target_id=self.obj.pk,
                amount=10
            )
        self.assert_equals(110, TotalRate.objects.get_for_object(self.obj))

class TestTopObjects(DatabaseTestCase):
    def setUp(self):
        super(TestTopObjects, self).setUp()
        self.ratings = []
        meta_ct = ContentType.objects.get_for_model(ContentType)
        for ct in ContentType.objects.all():
            self.ratings.append(
                Rating.objects.create(
                        target_ct=meta_ct,
                        target_id=ct.pk,
                        amount=ct.pk
                    )
                )

    def test_only_return_count_objects(self):
        self.assert_equals(1, len(TotalRate.objects.get_top_objects(1)))

    def test_return_top_rated_objects(self):
        self.assert_equals(list(ContentType.objects.order_by('-pk')[:3]), TotalRate.objects.get_top_objects(3))

        
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
        