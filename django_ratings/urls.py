try:
    import ella
except ImportError, e:
    pass
else:
    from django.utils.translation import ugettext as _

    from ella.core.custom_urls import dispatcher
    from django_ratings.views import rate

    dispatcher.register(_('rate'),  rate)
