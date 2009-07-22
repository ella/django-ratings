from django.contrib.contenttypes.models import ContentType

from django_ratings.models import TotalRate, Rating

from helpers import SimpleRateTestCase, MultipleRatedObjectsTestCase

class TestTotalRate(SimpleRateTestCase):
    def test_default_rating_of_an_object(self):
        self.assert_equals(0, TotalRate.objects.get_for_object(self.obj))
        
    def test_rating_propagates_to_total_rate(self):
        Rating.objects.create(amount=10, **self.kw)
        self.assert_equals(10, TotalRate.objects.get_for_object(self.obj))

    def test_rating_doesnt_propagate_to_total_rate_on_update(self):
        r = Rating.objects.create(amount=10, **self.kw)
        r.amount = 100
        r.save()
        self.assert_equals(10, TotalRate.objects.get_for_object(self.obj))

        
    def test_rating_propagates_to_total_rate_even_for_existing_totalrate(self):
        r = Rating.objects.create(amount=10, **self.kw)
        r = Rating.objects.create(amount=100, **self.kw)
        self.assert_equals(110, TotalRate.objects.get_for_object(self.obj))

class TestNormalizedRating(MultipleRatedObjectsTestCase):
    def test_distribution_in_smaller_universum(self):
        objs = []
        top = len(self.objs)
        for ct in self.objs:
            objs.append((TotalRate.objects.get_for_object(ct), TotalRate.objects.get_normalized_rating(ct, top)))
        self.assert_equals([(ct.pk*10, (ct.pk-1)) for ct in self.objs], objs)

    def test_distribution_in_same_sized_universum(self):
        objs = []
        top = len(self.objs) * 10
        for ct in self.objs:
            objs.append((TotalRate.objects.get_for_object(ct), TotalRate.objects.get_normalized_rating(ct, top)))
        self.assert_equals([(ct.pk*10, (ct.pk-1)*10) for ct in self.objs], objs)

class TestTopObjects(MultipleRatedObjectsTestCase):
    def test_only_return_count_objects(self):
        self.assert_equals(1, len(TotalRate.objects.get_top_objects(1)))

    def test_return_top_rated_objects(self):
        self.assert_equals(list(ContentType.objects.order_by('-pk')[:3]), TotalRate.objects.get_top_objects(3))

    def test_return_only_given_model_type(self):
        Rating.objects.create(
                target_ct=ContentType.objects.get_for_model(Rating),
                target_id=self.ratings[0].pk,
                amount=1
            )
        self.assert_equals(self.ratings[:1], TotalRate.objects.get_top_objects(10, mods=[Rating]))

    def test_return_only_given_model_type_even_if_no_ratings(self):
        self.assert_equals(0, len(TotalRate.objects.get_top_objects(10, mods=[TotalRate])))

        
class TestRating(SimpleRateTestCase):
    def test_default_rating_of_an_object(self):
        self.assert_equals(0, Rating.objects.get_for_object(self.obj))
        
    def test_rating_shows_in_get_for_model(self):
        Rating.objects.create(amount=10, **self.kw)
        self.assert_equals(10, Rating.objects.get_for_object(self.obj))
        

