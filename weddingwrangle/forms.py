from django import forms
from weddingwrangle.models import Guest, Email, Audience
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


def audience_update(self, form_instance):
    """If the RSVP Status or Position changes, add the guest to the relevant
    Audience."""
    if (
        # The form response rsvp_status is different to the the original record
        (form_instance.rsvp_status.id != self.initial.get("rsvp_status")) or
        (form_instance.position.id != self.initial.get("position")) 
    ):
        # Pick an appropriate audience
        potential = Audience.objects.get(id=4)
        no_response = Audience.objects.get(id=3)
        attending = Audience.objects.get(id=2)
        if form_instance.position.name != "Guest":
            return form_instance
        elif form_instance.rsvp_status.name == "Accepted":
            form_instance.audiences.add(attending)
            form_instance.audiences.add(potential)
        elif form_instance.rsvp_status.name == "Declined":
            form_instance.audiences.clear()
        elif form_instance.rsvp_status.name == "Pending":
            form_instance.audiences.add(no_response)
            form_instance.audiences.add(potential)
        return form_instance
    else:
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
        form_instance = audience_update(self, form_instance)
        if commit:
            print(form_instance.dietaries.all())
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

        
