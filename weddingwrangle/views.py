from django.db.models import Min, Count, Q
from django.views.generic.base import TemplateView
from django.views.generic.edit import UpdateView, CreateView, UpdateView, DeleteView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import render, get_object_or_404, redirect
from django_tables2 import SingleTableView
from django.urls import reverse_lazy, reverse
from django.utils import timezone
from plotly.offline import plot
import plotly.graph_objs as graph_objs
from datetime import timedelta, datetime, time
from weddingwrangle.models import Guest
from weddingwrangle.tables import GuestTable
from weddingwrangle.forms import RSVPForm, GuestForm


class GuestList(LoginRequiredMixin, SingleTableView):
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

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        rsvp_link = self.get_object().rsvp_link
        context["qr_url"] = self.request.build_absolute_uri(
            reverse("rsvp", args=[rsvp_link])
        )
        return context


class GuestDelete(LoginRequiredMixin, DeleteView):
    model = Guest
    template_name_suffix = "_delete"
    success_url = reverse_lazy("guest_list")


class HomePage(LoginRequiredMixin, TemplateView):
    template_name = "weddingwrangle/home.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["some context"] = 100

        # Build a list of dates
        start_date = Guest.objects.aggregate(Min("created_at"))["created_at__min"]
        start_date = datetime.combine(
            start_date.date(), time.min, tzinfo=timezone.get_default_timezone()
        )
        guest_number_dates = []
        while start_date <= timezone.now():
            guest_number_dates.append(start_date)
            start_date = start_date + timedelta(days=1)
        print(guest_number_dates)

        # Build a list of attending, declined and total guests
        attending_numbers = []
        declined_numbers = []
        total_guests = []
        for query_date in guest_number_dates:
            query_date = query_date + timedelta(days=1)
            att_count = (
                Guest.objects.filter(rsvp_at__lt=query_date)
                .filter(rsvp_status=4)
                .count()
            )
            attending_numbers.append(att_count)
            decl_count = (
                Guest.objects.filter(rsvp_at__lt=query_date)
                .filter(rsvp_status=5)
                .count()
            )
            declined_numbers.append(decl_count)
            guest_count = Guest.objects.filter(created_at__lt=query_date).count()
            total_guests.append(guest_count)

        # Decided to use Plotly Figure rather than Express + Dash
        # https://www.codingwithricky.com/2019/08/28/easy-django-plotly/
        # https://plotly.com/python-api-reference/generated/plotly.graph_objects.Bar.html
        # https://plotly.com/python/bar-charts/#bar-chart-with-relative-barmode

        figure = graph_objs.Figure(
            layout_title_text="Guests",
        )

        attend_bar = graph_objs.Bar(
            name="Attending",
            x=guest_number_dates,
            y=attending_numbers,
            opacity=1,
            marker_color="green",
            hovertemplate=" %{x|%d %B %Y} <extra> %{y} attending </extra>",
        )

        decl_bar = graph_objs.Bar(
            name="Declined",
            x=guest_number_dates,
            y=declined_numbers,
            opacity=1,
            marker_color="red",
            hovertemplate=" %{x|%d %B %Y} <extra> %{y} declined </extra>",
        )

        line = graph_objs.Scatter(
            name="Invited",
            x=guest_number_dates,
            y=total_guests,
            opacity=1,
            marker_color="blue",
            mode="lines",
            hovertemplate=" %{x|%d %B %Y} <extra> %{y} guests invited </extra>",
        )

        figure.update_xaxes(
            tickformat="%d/%m",
            tickvals=guest_number_dates,
            type="date",
        )

        figure.add_trace(line)
        figure.add_trace(attend_bar)
        figure.add_trace(decl_bar)
        figure.update_layout(barmode="relative")
        plot_div = plot(figure, output_type="div", include_plotlyjs=False)

        context["plot_div"] = plot_div
        return context
