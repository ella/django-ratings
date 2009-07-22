from django.core.exceptions import ImproperlyConfigured

class KarmaSources(object):
    """
    Registry for models that have an owner associated with them. Every model
    that should be involved in calculating user's karma must be register
    afunction that, when given a Model instance will either return it's owner
    or None if not applicable.
    """
    def __init__(self):
        self._registry = {}
    
    def register(self, model, owner_getter):
        "Register a model class with it's owner_getter."
        if model in self._registry and self._registry[model] != owner_getter:
            raise ImproperlyConfigured('Cannot register %s model twice with different getters.')

        self._registry[model] = owner_getter

    def get_owner(self, instance):
        """
        Get the owner of given model, return None if there is no owner or the
        model class is not registered.
        """
        if instance.__class__ in self._registry:
            return self._registry[instance.__class__](instance)

        return None

# global registry of karma sources
sources = KarmaSources()
