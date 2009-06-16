"""
Creates model weights for all installed models.
It will try and identify the field containing the foreign key to the owner.
"""

from django.dispatch import dispatcher
from django.db.models import get_apps, get_models, signals
from django.db import connection
from django.conf import settings

def create_model_weights(app, created_models, verbosity=2):
    """
    Create ModelWeight objects for models in one django application.
    This function goes through all the models and checks for existance of ModelWeight objects.
    If the objects do not exist, it will create them and fill them with proper values.

    The owner field is identified as a ForeignKey to django.contrib.auth.models.User.
    If multiple exist, one called "owner" or "author" is used, the first one otherwise

    Params:
        app: app_label to process
        created_models: ignored
        verbosity: controls verbosity of the output, if verbosity >= 2, each object saved will be printed out.
    """
    from django_ratings.models import ModelWeight
    from django.contrib.contenttypes.models import ContentType
    from django.contrib.auth.models import User

    ModelWeight.objects.clear_cache()

    app_models = get_models(app)
    if not app_models:
        return
    for klass in app_models:
        opts = klass._meta
        ct = ContentType.objects.get_for_model(klass)
        try:
            ModelWeight.objects.get(content_type=ct)
        except ModelWeight.DoesNotExist:
            # find all the foreign keys to User
            user_fields = [ f for f in opts.fields if f.rel and f.rel.to == User ]

            # we found more user fields, try to locate one named owner
            if len(user_fields) > 1:
                owner_field = None
                for f in user_fields:
                    if f.name == 'owner' or f.name == 'author':
                        # found it
                        owner_field = f
                        break
                else:
                    # didn't find it - take the first one
                    owner_field = user_fields[0]
            elif user_fields:
                # only one field found
                owner_field = user_fields[0]
            else:
                # no FK to User, continue with next Model
                continue

            mw = ModelWeight(content_type=ct, owner_field=owner_field.name)
            mw.save()
            if verbosity >= 2:
                print "Adding model weight for '%s | %s' with owner field %s" % (ct.app_label, ct.model, owner_field.name)

def create_all_model_weights(verbosity=2):
    """
    Create ModelWeight objects for all models created by the syncdb command.

    Params:
        verbosity: controls verbosity of the output, if verbosity >= 2, each object saved will be printed out.
    """
    for app in get_apps():
        create_model_weights(app, None, verbosity)


#dispatcher.connect(create_model_weights, signal=signals.post_syncdb)


if __name__ == "__main__":
    create_all_model_weights()

