from django import forms
from weddingwrangle.models import Guest, RSVPStatus
from weddingwrangle.scripts import csv_import
from django.utils import timezone


def rsvp_time_update(self, form_instance):
    """If the saved form is being changed to "Accepted", set the RSVP time to the
    current time."""
    if (
        # The form response has an rsvp_status of "Accepted" but the original record
        # had something else
        (form_instance.rsvp_status.id == 4 or form_instance.rsvp_status.id == 5) and 
        (form_instance.rsvp_status.id != self.initial.get("rsvp_status"))
    ):
        form_instance.rsvp_at = timezone.now()
    return form_instance



class CustomModelChoiceField(forms.ModelChoiceField):
    def label_from_instance(self, obj):
        return obj.verbose_name


class RSVPForm(forms.ModelForm):
    """Extends ModelForm in order to customise field types and RSVP status display"""

    def __init__(self, *args, **kwargs):
        """When initialising RSVP Form, use the verbose_name as label rather than the
        normal name. By default, the labels are defined by looking up the string
        representation of objects in the foreign table"""

        super().__init__(*args, **kwargs)
        self.fields["rsvp_status"].label_from_instance = lambda obj: obj.verbose_name

    def save(self, commit=True):
        # Override ModelForm's save method
        form_instance = super().save(commit=False)
        form_instance = rsvp_time_update(self, form_instance)
        if commit:
            form_instance.save()
        return form_instance
    class Meta:
        model = Guest
        fields = ["email_address", "rsvp_status", "dietaries"]
        widgets = {"dietaries": forms.CheckboxSelectMultiple}
        labels = {
            "dietaries": "Please don't feed me...",
            "rsvp_status": "RSVP",
        }


class GuestForm(forms.ModelForm):
    """Extends ModelForm in order to customise field types and add an RSVP link"""

    class Meta:
        model = Guest
        fields = [
            "title",
            "first_name",
            "surname",
            "rsvp_status",
            "email_address",
            "position",
            "dietaries",
        ]
        widgets = {"dietaries": forms.CheckboxSelectMultiple}

    def save(self, commit=True):
        # Override ModelForm's save method
        form_instance = super().save(commit=False)
        if form_instance.rsvp_link == "":
            form_instance.rsvp_link = csv_import.generate_key()
        form_instance = rsvp_time_update(self, form_instance)
        if commit:
            form_instance.save()
        return form_instance


