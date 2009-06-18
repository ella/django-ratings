from datetime import datetime, timedelta, date
from djangosanetesting.cases import DatabaseTestCase

from django.contrib.contenttypes.models import ContentType

from django_ratings.models import TotalRate, Rating, Agg
from django_ratings import aggregation

class SimpleRateTestCase(DatabaseTestCase):
    def setUp(self):
        super(SimpleRateTestCase, self).setUp()
        self.obj = ContentType.objects.get_for_model(ContentType)
        self.kw = {
                'target_ct': ContentType.objects.get_for_model(self.obj),
                'target_id': self.obj.pk
        }

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

class MultipleRatedObjectsTestCase(DatabaseTestCase):
    def setUp(self):
        super(MultipleRatedObjectsTestCase, self).setUp()
        self.ratings = []
        meta_ct = ContentType.objects.get_for_model(ContentType)
        self.objs = list(ContentType.objects.order_by('pk'))
        for ct in self.objs:
            self.ratings.append(
                Rating.objects.create(
                        target_ct=meta_ct,
                        target_id=ct.pk,
                        amount=ct.pk*10
                    )
                )

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
        

class TestAggregation(SimpleRateTestCase):
    def test_totalrate_from_aggregation(self):
        now = date.today()
        for i in range(1,4):
            Agg.objects.create(people=i, amount=4-i, time=now, period='d', detract=0, **self.kw)
        Agg.objects.agg_to_totalrate()
        self.assert_equals(6, TotalRate.objects.get_for_object(self.obj))

    def test_aggregation_from_aggegates(self):
        now = date.today()
        self.kw['period'] = 'd'
        self.kw['detract'] = 0
        Agg.objects.create(people=8, amount=1, time=now, **self.kw)
        Agg.objects.create(people=4, amount=2, time=now, **self.kw)

        before = now - timedelta(days=40)
        Agg.objects.create(people=2, amount=4, time=before, **self.kw)
        Agg.objects.create(people=1, amount=8, time=before, **self.kw)

        Agg.objects.move_agg_to_agg(now, 'month', 'm')
        expected = [
                (before.replace(day=1), 3,  12  ),
                (now.replace(day=1),    12, 3   ),
            ]

        self.assert_equals(2, Agg.objects.count())
        self.assert_equals(expected, [(a.time, a.people, a.amount) for a in Agg.objects.order_by('time')])

    def test_aggregation_from_ratings_works_for_days(self):
        now = datetime.now()
        Rating.objects.create(amount=1, time=now, **self.kw)
        Rating.objects.create(amount=2, time=now, **self.kw)

        yesterday = now - timedelta(days=1)
        Rating.objects.create(amount=4, time=yesterday, **self.kw)
        Rating.objects.create(amount=8, time=yesterday, **self.kw)

        Rating.objects.move_rate_to_agg(now, 'day', 'd')

        self.assert_equals(0, Rating.objects.count())
        self.assert_equals(2, Agg.objects.count())
        expected = [
                (yesterday.date(),  2,  12  ),
                (now.date(),        2,  3   ),
            ]
        self.assert_equals(expected, [(a.time, a.people, a.amount) for a in Agg.objects.order_by('time')])

