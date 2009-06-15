from django import forms
from django.utils.translation import ugettext as _
from django.contrib.contenttypes.models import ContentType
from django.db import models

CONTENT_TYPE_CT = ContentType.objects.get_for_model(ContentType)
class RateForm(forms.Form):
    content_type = forms.IntegerField(widget=forms.HiddenInput)
    target = forms.IntegerField(widget=forms.HiddenInput)

    def clean_content_type(self):
        try:
            value = ContentType.objects.get(pk=self.cleaned_data['content_type'])
        except models.ObjectDoesNotExist:
            raise forms.ValidationError, _('The given ContentType object does not exist.')
        return value

    def clean_target(self):
        try:
            value = self.cleaned_data['content_type'].get_object_for_this_type(pk=self.cleaned_data['content_type'])
        except models.ObjectDoesNotExist:
            raise forms.ValidationError, _('The given target object does not exist.')
        return value

