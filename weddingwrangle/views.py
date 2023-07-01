from django.views import View
from django.views.generic.edit import UpdateView, CreateView, UpdateView, DeleteView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import render, get_object_or_404, redirect
from django_tables2 import SingleTableView
from django.urls import reverse_lazy
from weddingwrangle.models import Guest
from weddingwrangle.tables import GuestTable
from weddingwrangle.forms import RSVPForm, GuestForm


class GuestListView(LoginRequiredMixin, SingleTableView):
    model = Guest
    table_class = GuestTable
    template_name = "guest_list.html"


class RSVPView(UpdateView):
    model = Guest
    form_class = RSVPForm
    success_url = reverse_lazy("guest_list")
    # TODO: this should redirect to a link thanking the guest and offering an RSVP for
    # their partner
    template_name = "weddingwrangle/rsvp.html"

    # Overriding get_object so that the RSVP link captured by the URL dispatcher is used
    # to find the object. self.kwargs is a dictionary containing captured URL parameters.
    def get_object(self):
        return self.model.objects.get(rsvp_link=self.kwargs["rsvp_link"])


class GuestCreate(LoginRequiredMixin, CreateView):
    model = Guest
    form_class = GuestForm
    success_url = reverse_lazy("guest_list")
    template_name_suffix = "_create"


class GuestUpdate(LoginRequiredMixin, UpdateView):
    model = Guest
    form_class = GuestForm
    success_url = reverse_lazy("guest_list")
    template_name_suffix = "_update"


class GuestDelete(LoginRequiredMixin, DeleteView):
    model = Guest
    template_name_suffix = "_delete"
    success_url = reverse_lazy("guest_list")
