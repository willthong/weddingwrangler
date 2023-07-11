import django_tables2
from weddingwrangle.models import Guest
from django.urls import reverse
from django.utils.safestring import mark_safe
from weddingwrangle import views

def convert_to_url(self, value):
    url = reverse("guest_update", args=[value])
    return mark_safe(f'<a href="{url}">{value}</a>')


class GuestTable(django_tables2.Table):
    pk = django_tables2.Column(verbose_name="ID")
    rsvp_status = django_tables2.Column(verbose_name="RSVP")
    email_address = django_tables2.Column(orderable=False)

    class Meta:
        model = Guest
        fields = (
            "pk",
            "title",
            "first_name",
            "surname",
            "email_address",
            "position",
            "rsvp_status",
            "dietaries",
        )
    
