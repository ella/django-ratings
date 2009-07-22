from djangosanetesting.cases import DatabaseTestCase

from django.contrib.contenttypes.models import ContentType

from django_ratings.models import Rating

class SimpleRateTestCase(DatabaseTestCase):
    def setUp(self):
        super(SimpleRateTestCase, self).setUp()
        self.obj = ContentType.objects.get_for_model(ContentType)
        self.kw = {
                'target_ct': ContentType.objects.get_for_model(self.obj),
                'target_id': self.obj.pk
        }

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

