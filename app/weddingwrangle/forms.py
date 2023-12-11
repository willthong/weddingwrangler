from django import forms
from weddingwrangle.models import Guest, Audience, Email
from weddingwrangle.scripts import csv_import
from django.utils import timezone
from weddingwrangle.humanize import naturalsize
from weddingwrangle.scripts import sync


def rsvp_time_update(self, form_instance):
    """If the saved form is being changed to "Accepted", set the RSVP time to the
    current time."""
    if (
        # The form response has an rsvp_status of "Accepted" but the original record
        # had something else
        (form_instance.rsvp_status.id == 4 or form_instance.rsvp_status.id == 5)
        and (form_instance.rsvp_status.id != self.initial.get("rsvp_status"))
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
        form_instance = audience_update(self, form_instance)
        if commit:
            form_instance.save()
            self.save_m2m()
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
    """Extends ModelForm in order to customise field types and add an RSVP link,
    audience and partner relationship if appropriate"""

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
            "partner",
        ]
        widgets = {"dietaries": forms.CheckboxSelectMultiple}

    def save(self, commit=True):
        # Override ModelForm's save method
        form_instance = super().save(commit=False)

        # Autogenerate RSVP link if blank
        if form_instance.rsvp_link == "":
            form_instance.rsvp_link = csv_import.generate_key()
        form_instance = rsvp_time_update(self, form_instance)

        if (
            # The form response rsvp_status is different to the the original record
            (form_instance.rsvp_status.id != self.initial.get("rsvp_status"))
            or (form_instance.position.id != self.initial.get("position"))
        ):
            form_instance = sync.sync_audience(form_instance)

        # Autogenerate reciprocal partner relationship
        form_instance = sync.sync_partner(form_instance)

        if commit:
            form_instance.save()
            self.save_m2m()
        return form_instance


class NewEmailForm(forms.ModelForm):
    """Extends ModelForm in order to customise field types"""

    class Meta:
        model = Email
        fields = [
            "subject",
            "audience",
            "text",
        ]
        widgets = {"audience": forms.RadioSelect, "text": forms.Textarea}


class CSVForm(forms.Form):
    upload_limit = 2 * 1024 * 1024
    upload_limit_text = naturalsize(upload_limit)

    # Call this 'picture' so it gets copied from the form to the in-memory model
    # It will not be the "bytes", it will be the "InMemoryUploadedFile"
    # because we need to pull out things like content_type
    csv = forms.FileField(required=True, label="File to Upload <= " + upload_limit_text)
    upload_field_name = "csv"

    # Data currently exists as request.FILES["csv"]

    # Validate the size of the file
    def clean(self):
        cleaned_data = super().clean()
        file = cleaned_data.get("csv")
        if file is None:
            return
        if len(file) > self.upload_limit:
            self.add_error("csv", "File must be < " + self.upload_limit_text + " bytes")
