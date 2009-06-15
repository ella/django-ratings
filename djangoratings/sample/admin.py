from django.contrib import admin
from djangoratings.sample.models import Spam, Type

admin.site.register([Spam, Type])

