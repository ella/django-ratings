from datetime import datetime, timedelta
from decimal import Decimal

from django.db import models, connection
from django.contrib.auth.models import User
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes import generic
from django.conf import settings
from django.utils.translation import ugettext_lazy as _

# ratings - specific settings
ANONYMOUS_KARMA = getattr(settings, 'ANONYMOUS_KARMA', 1)
INITIAL_USER_KARMA = getattr(settings, 'ANONYMOUS_KARMA', 4)
DEFAULT_MODEL_WEIGHT = getattr(settings, 'DEFAULT_MODEL_WEIGHT', 1)
MINIMAL_ANONYMOUS_IP_DELAY = getattr(settings, 'MINIMAL_ANONYMOUS_IP_DELAY', 1800)
RATINGS_COOKIE_NAME = getattr(settings, 'RATINGS_COOKIE_NAME', 'ratings_voted')
RATINGS_MAX_COOKIE_LENGTH = getattr(settings, 'RATINGS_MAX_COOKIE_LENGTH', 20)
RATINGS_MAX_COOKIE_AGE = getattr(settings, 'RATINGS_MAX_COOKIE_AGE', 3600)

PERIOD_CHOICES = (
    ('d', 'day'),
    ('m', 'month'),
    ('w', 'week'),
    ('y', 'year'),
)


MODEL_WEIGHT_CACHE = {}
class ModelWeightManager(models.Manager):
    """
    Manager class that handles one additional method - getweight(model), which will return weight for a given model
    """
    def get_weight(self, model):
        """
        Returns the weight for the given model.

        Params:
            model: model class or instance to work with
        """
        opts = model._meta
        key = (opts.app_label, opts.object_name.lower())

        try:
            weight = MODEL_WEIGHT_CACHE[key]
        except KeyError:
            try:
                mw = self.get(content_type=ContentType.objects.get_for_model(model))
                weight = mw.weight
            except ModelWeight.DoesNotExist:
                weight = DEFAULT_MODEL_WEIGHT

            MODEL_WEIGHT_CACHE[key] = weight

        return weight

    def clear_cache(self):
        """
        Clear out the model-weight cache. This needs to happen during database
        flushes to prevent caching of "stale" model weights IDs (see
        django_ratings.management.create_model_weights and ModelWeight.save() for where
        this gets called).

        Taken from django.contrib.contenttypes.models, thanks.
        """
        global MODEL_WEIGHT_CACHE
        MODEL_WEIGHT_CACHE = {}


class ModelWeight(models.Model):
    """
    Importance of each Model when it comes to computing owner's Karma.
    """
    content_type = models.OneToOneField(ContentType)
    weight = models.IntegerField(_('Weight'), default=DEFAULT_MODEL_WEIGHT)
    owner_field = models.CharField(_('Owner field'), max_length=30, help_text=_('Name of the field on target model that identifies the owner of the object'))

    objects = ModelWeightManager()

    def save(self, **kwargs):
        """
        Clear the cache and do the save()
        """
        ModelWeight.objects.clear_cache()
        return super(ModelWeight, self).save(**kwargs)

    class Meta:
        verbose_name = _('Model weight')
        verbose_name_plural = _('Model weights')
        ordering = ('-weight',)

class TotalRateManager(models.Manager):

    def get_normalized_rating(self, obj, max, step=None):
        """
        Returns rating normalized from min to max rounded to step

        - no score (0) is always avarage (0)
        - worst score gets always min
        - best score gets always max
        - results between 0 and min/max should be uniformly distributed
        """
        total = self.get_total_rating(obj)
        if total == 0:
            return Decimal("0").quantize(step or Decimal("1"))

        # Handle positive and negative score separately
        lt = "<"
        gt = ">"
        ref = max
        if total < 0:
            lt = ">"
            gt = "<"
            ref = -max

        ct_id = ContentType.objects.get_for_model(obj).id
        sql = "SELECT (SELECT count(*) FROM %(table)s WHERE target_ct_id=%%s AND amount %(lt)s= %%s AND amount %(gt)s 0) / (SELECT count(*) FROM %(table)s WHERE target_ct_id=%%s AND amount %(gt)s 0)" \
            % {'table': connection.ops.quote_name(TotalRate._meta.db_table),
               'gt' :gt, 'lt' : lt,}

        cursor = connection.cursor()
        cursor.execute(sql, (ct_id, total, ct_id))
        (percentil,) = cursor.fetchone()

        if percentil is None:
            # First rating
            percentil = Decimal(0)
        cursor.close()

        result = percentil * ref
        if step:
            result = (result / step).quantize(Decimal("1")) * step
        if result < -max:
            result = -max
        if result > max:
            result = max
        return result


    def get_for_object(self, obj):
        """
        Return the agg rating for a given object.

        Params:
                obj: object to work with
        """
        content_type = ContentType.objects.get_for_model(obj)
        try:
            return self.values('amount').get(target_ct=content_type, target_id=obj.pk)['amount']
        except self.model.DoesNotExist:
            return 0


    def get_top_objects(self, count, mods=[]):
        """
        Return count objects with the highest rating.

        Params:
            count: number of objects to return
            mods: if specified, limit the result to given model classes
        """
        qset = self.order_by('-amount')
        kw = {}
        if mods:
            kw['target_ct__in'] = [ContentType.objects.get_for_model(m).pk for m in mods]
        return [o.target for o in qset.filter(**kw)[:count]]

class TotalRate(models.Model):
    """
    save all rating for individual object.
    """
    target_ct = models.ForeignKey(ContentType, db_index=True)
    target_id = models.PositiveIntegerField(_('Object ID'))
    target = generic.GenericForeignKey('target_ct', 'target_id')
    amount = models.DecimalField(_('Amount'), max_digits=10, decimal_places=2)

    objects = TotalRateManager()

    def __unicode__(self):
        return u'%s points for %s' % (self.amount, self.target)

    class Meta:
        verbose_name = _('Total rate')
        verbose_name_plural = _('Total rates')
        unique_together = (('target_ct', 'target_id',),)



class AggManager(models.Manager):

    def copy_agg_to_agg(self, time_limit, time_format, time_period):
        """
        Coppy aggregated Agg data to table Agg

        time_limit: limit for time of transfering data

        time_format: format for destiny DATE_FORMAT

        time_period: is a period of aggregation data
        """

        sql = '''INSERT INTO %(tab)s (detract, period, people, amount, time, target_ct_id, target_id)
                 SELECT 1, %(pe)s, SUM(people), SUM(amount), DATE(time), target_ct_id, target_id
                 FROM %(tab)s
                 WHERE time <= %%(li)s and detract = 0
                 GROUP BY target_ct_id, target_id, DATE_FORMAT(time, %%(format)s)''' % {
            'tab' : connection.ops.quote_name(Agg._meta.db_table),
            'pe' : time_period
        }

        cursor = connection.cursor()
        cursor.execute(sql, {'li' : time_limit,'format' : time_format})

    def agg_assume(self):
        """
        update objects field detract for futhure possibility aggregation
        """
        sql = 'UPDATE %s SET detract = 0' % (
            connection.ops.quote_name(Agg._meta.db_table),
        )
        cursor = connection.cursor()
        cursor.execute(sql, ())

    def agg_to_totalrate(self):
        """
        Transfer aggregation data from table Agg to table TotalRate
        """

        sql = '''INSERT INTO %(tab_tr)s (amount, target_ct_id, target_id)
                 SELECT round(SUM(amount * (karma_get_time_coeficient(DATEDIFF(current_date, DATE(time))))),2), target_ct_id, target_id
                 FROM %(tab_agg)s
                 GROUP BY target_ct_id, target_id''' % {
            'tab_agg' : connection.ops.quote_name(Agg._meta.db_table),
            'tab_tr' : connection.ops.quote_name(TotalRate._meta.db_table)
        }

        cursor = connection.cursor()
        cursor.execute(sql, ())


class Agg(models.Model):
    """
    Aggregation of rating objects.
    """
    target_ct = models.ForeignKey(ContentType, db_index=True)
    target_id = models.PositiveIntegerField(_('Object ID'), db_index=True)
    target = generic.GenericForeignKey('target_ct', 'target_id')

    time = models.DateField(_('Time'))
    people = models.IntegerField(_('People'))
    amount = models.DecimalField(_('Amount'), max_digits=10, decimal_places=2)
    period = models.CharField(_('Period'), max_length="1", choices=PERIOD_CHOICES)
    detract = models.IntegerField(_('Detract'), default=0, max_length=1)

    objects = AggManager()

    def __unicode__(self):
        return u'%s points for %s' % (self.amount, self.target)

    class Meta:
        verbose_name = _('Aggregation')
        verbose_name_plural = _('Aggregations')
        ordering = ('-time',)


class RatingManager(models.Manager):

    def get_for_object(self, obj):
        """
        Return the rating for a given object.

        Params:
            obj: object to work with
        """
        content_type = ContentType.objects.get_for_model(obj)
        aggs = self.filter(target_ct=content_type, target_id=obj.pk).aggregate(amount_sum=models.Sum('amount'))['amount_sum']
        if aggs is None:
            return 0
        return aggs

    def move_rate_to_agg(self, time_limit, time_format, time_period):
        """
        Coppy aggregated Rating to table Agg

        time_limit: limit for time of transfering data

        time_format: format for destiny DATE_FORMAT

        time_period: is a period of aggregation data
        """
        qn = connection.ops.quote_name
        date_trunc = connection.ops.date_trunc_sql

        sql = '''INSERT INTO %(agg_table)s
                    (detract, period, people, amount, time, target_ct_id, target_id)
                 SELECT
                    0, %%s, COUNT(*), SUM(amount), %(truncated_date)s, target_ct_id, target_id
                 FROM %(rating_table)s
                 WHERE time <= %%s
                 GROUP BY target_ct_id, target_id, %(truncated_date)s''' % {
            'rating_table' : qn(Rating._meta.db_table),
            'agg_table' : qn(Agg._meta.db_table),
            'truncated_date': date_trunc(time_format, qn('time')),
        }

        cursor = connection.cursor()
        cursor.execute(sql, (time_period, time_limit,))
        self.filter(time__lte=time_limit).delete()


class Rating(models.Model):
    """
    Rating of an object.
    """
    target_ct = models.ForeignKey(ContentType, db_index=True)
    target_id = models.PositiveIntegerField(_('Object ID'), db_index=True)
    target = generic.GenericForeignKey('target_ct', 'target_id')

    time = models.DateTimeField(_('Time'), default=datetime.now, editable=False)
    user = models.ForeignKey(User, blank=True, null=True)
    amount = models.DecimalField(_('Amount'), max_digits=10, decimal_places=2)
    ip_address = models.CharField(_('IP Address'), max_length="15", blank=True)

    objects = RatingManager()

    def __unicode__(self):
        return u'%s points for %s' % (self.amount, self.target)

    class Meta:
        verbose_name = _('Rating')
        verbose_name_plural = _('Ratings')

    def save(self, **kwargs):
        """
        Modified save() method that checks for duplicit entries.
        """
        if not self.pk:
            # fail silently on inserting duplicate ratings
            if self.user:
                try:
                    Rating.objects.get(target_ct=self.target_ct, target_id=self.target_id, user=self.user)
                    return
                except Rating.DoesNotExist:
                    pass
            elif (self.ip_address and Rating.objects.filter(
                        target_ct=self.target_ct,
                        target_id=self.target_id,
                        user__isnull=True,
                        ip_address=self.ip_address ,
                        time__gte=(self.time or datetime.now()) - timedelta(seconds=MINIMAL_ANONYMOUS_IP_DELAY)
                    ).count() > 0):
                return
            # denormalize the total rate
            cnt = TotalRate.objects.filter(target_ct=self.target_ct, target_id=self.target_id).update(amount=models.F('amount')+self.amount)
            if cnt == 0:
                tr = TotalRate.objects.create(target_ct=self.target_ct, target_id=self.target_id, amount=self.amount)


        super(Rating, self).save(**kwargs)


