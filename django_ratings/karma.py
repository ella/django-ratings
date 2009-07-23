from django.core.exceptions import ImproperlyConfigured
from django.contrib.contenttypes.models import ContentType

class KarmaSources(object):
    """
    Registry for models that have an owner associated with them. Every model
    that should be involved in calculating user's karma must be register
    afunction that, when given a Model instance will either return it's owner
    or None if not applicable.
    """
    def __init__(self):
        self._registry = {}
    
    def register(self, model, owner_getter, weight=1):
        "Register a model class with it's owner_getter."
        if model in self._registry and self._registry[model] != (owner_getter, weight):
            raise ImproperlyConfigured('Cannot register %s model twice with different getters.')

        self._registry[model] = (owner_getter, weight)

    def get_owner(self, instance):
        """
        Get the owner of given model, return None if there is no owner or the
        model class is not registered.
        """
        if instance.__class__ in self._registry:
            owner_getter, weight = self._registry[instance.__class__]
            return owner_getter(instance), weight

        return None

    def registered_content_types(self):
        return map(ContentType.objects.get_for_model, self._registry.keys())


# global registry of karma sources
sources = KarmaSources()
