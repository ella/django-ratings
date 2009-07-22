from datetime import date, timedelta, datetime

from django_ratings.models import TotalRate, Rating, Agg

from helpers import SimpleRateTestCase

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

