from django import forms
from weddingwrangle.models import Guest, RSVPStatus
from weddingwrangle.scripts import csv_import


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
        if commit:
            form_instance.save()
        return form_instance


