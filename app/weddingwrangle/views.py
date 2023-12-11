import csv
from datetime import timedelta, datetime, time
from io import StringIO
import os, shutil
from plotly.offline import plot
import plotly.graph_objs as graph_objs
from re import sub, search
from typing import NamedTuple
from zipfile import ZipFile
from django.conf import settings
from django.contrib.auth import logout
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.decorators import login_required
from django.contrib.sites.shortcuts import get_current_site
from django.core.mail import send_mail
from django.db.models import Min
from django.http import HttpResponseRedirect, HttpResponse, HttpRequest
from django.shortcuts import render
from django_tables2 import SingleTableView
from django.template.loader import render_to_string
from django.urls import reverse_lazy, reverse
from django.utils import timezone
from django.utils.safestring import mark_safe
from django.views import View
from django.views.generic.base import TemplateView
from django.views.generic.detail import DetailView
from django.views.generic.edit import UpdateView, CreateView, DeleteView
from weddingwrangle.forms import RSVPForm, GuestForm, NewEmailForm, CSVForm
from weddingwrangle.models import Guest, Email
from weddingwrangle.tables import GuestTable
from qr_code.qrcode.serve import make_qr_code_url
from qr_code.qrcode.maker import QRCodeOptions, make_qr_code_image
from weddingwrangle.scripts import csv_import


class GuestList(LoginRequiredMixin, SingleTableView):
    model = Guest
    table_class = GuestTable
    template_name = "guest_list.html"


class RSVPView(UpdateView):
    model = Guest
    form_class = RSVPForm
    template_name = "weddingwrangle/rsvp.html"

    # Override get_success_url method to use the RSVP link
    def get_success_url(self):
        url = reverse_lazy("rsvp_thank", args=[self.object.rsvp_link])
        return url

    # Overriding get_object so that the RSVP link captured by the URL dispatcher is used
    # to find the object. self.kwargs is a dictionary containing captured URL parameters.
    def get_object(self):
        return self.model.objects.get(rsvp_link=self.kwargs["rsvp_link"])


class RSVPThank(DetailView):
    model = Guest
    template_name = "weddingwrangle/rsvp_thanks.html"

    def get_object(self):
        return self.model.objects.get(rsvp_link=self.kwargs["rsvp_link"])


class RSVPPartner(UpdateView):
    model = Guest
    form_class = RSVPForm
    success_url = reverse_lazy("rsvp_thank_partner")
    template_name = "weddingwrangle/rsvp_partner.html"

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


# Cleaner date generation with list comprehension
def get_all_dates():
    start_date = Guest.objects.aggregate(Min("created_at"))["created_at__min"]
    days = (timezone.now() - start_date).days
    return [start_date + timedelta(days=day) for day in range(0, days + 1)]


# Load stats from database for a given date.
def load_attending_stats(date):
    # Defining a named tuple rather than multiple lists
    class AttendingStats(NamedTuple):
        date: datetime.date
        attending: int
        declined: int
        pending: int
        total: int

    # Uses less than / equal to (lte) rather than previous approach of incrementing query_date
    attending = (
        Guest.objects.filter(rsvp_at__lte=date)
        .filter(rsvp_status__name="Accepted")
        .count()
    )
    declined = (
        Guest.objects.filter(rsvp_at__lte=date)
        .filter(rsvp_status__name="Declined")
        .count()
    )
    pending = (
        Guest.objects.filter(created_at__lte=date)
        .filter(rsvp_status__name="Pending")
        .count()
    )
    total = attending + declined + pending
    return AttendingStats(date, attending, declined, pending, total)


def prepare_plot_data(attending_stats):
    """Generate plot data for home page graph"""
    # Decided to use Plotly Figure rather than Express + Dash
    # https://www.codingwithricky.com/2019/08/28/easy-django-plotly/
    # https://plotly.com/python-api-reference/generated/plotly.graph_objects.Bar.html
    # https://plotly.com/python/bar-charts/#bar-chart-with-relative-barmode

    figure = graph_objs.Figure(
        layout_title_text="Guests",
    )
    line = graph_objs.Scatter(
        name="Invited",
        x=[date.date for date in attending_stats],
        y=[date.total for date in attending_stats],
        opacity=1,
        marker_color="blue",
        mode="lines",
        hovertemplate=" %{x|%d %B %Y} <extra> %{y} guests invited </extra>",
    )
    attending_bar = graph_objs.Bar(
        name="Attending",
        x=[date.date for date in attending_stats],
        y=[date.attending for date in attending_stats],
        opacity=1,
        marker_color="green",
        hovertemplate=" %{x|%d %B %Y} <extra> %{y} attending </extra>",
    )
    declined_bar = graph_objs.Bar(
        name="Declined",
        x=[date.date for date in attending_stats],
        y=[date.declined for date in attending_stats],
        opacity=1,
        marker_color="red",
        hovertemplate=" %{x|%d %B %Y} <extra> %{y} declined </extra>",
    )
    figure.update_xaxes(
        tickformat="%d/%m",
        tickvals=[date.date for date in attending_stats],
        type="date",
    )

    figure.add_trace(line)
    figure.add_trace(attending_bar)
    figure.add_trace(declined_bar)
    figure.update_layout(barmode="relative")
    plot_div = plot(figure, output_type="div", include_plotlyjs=False)
    return plot_div


class HomePage(LoginRequiredMixin, TemplateView):
    template_name = "weddingwrangle/home.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        dates = get_all_dates()

        # Load named tuple into each date
        attending_stats = [load_attending_stats(date) for date in dates]
        # Put all logic into prepare_plot_data function
        context["plot_div"] = prepare_plot_data(attending_stats)
        return context


class EmailList(LoginRequiredMixin, CreateView):
    model = Email
    form_class = NewEmailForm
    template_name_suffix = "_create"

    # Retrieve list of emails
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["emails"] = Email.objects.filter(date_sent__isnull=False)
        for email in context["emails"]:
            email.count = email.guest.all().count()
        return context

    # Override get_success_url method to use the newly-created object's PK
    def get_success_url(self):
        url = reverse_lazy("email_confirm", args=[self.object.pk])
        return url


def generate_message(self, first_name, rsvp_url, rsvp_url_html):
    """Turn a request into an email message"""
    merged_message = self.object.text
    if search("{{ rsvp_qr_code }}", merged_message):
        qr_options = QRCodeOptions(image_format="png", size="s")
        qr_url = make_qr_code_url(rsvp_url, qr_options)
        qr_url = self.request.build_absolute_uri(qr_url)
        merged_message = sub(
            "{{ rsvp_qr_code }}",
            f'<img src="{qr_url}" alt="{rsvp_url}" title="QR Code" width="200"'
            f'height="200" style="display:block">',
            merged_message,
        )
    merged_message = sub("{{ first_name }}", first_name, merged_message)
    merged_message = sub("{{ rsvp_link }}", rsvp_url_html, merged_message)
    merged_message = mark_safe(merged_message)

    # https://stackoverflow.com/a/49894618/3161714
    rendered_message = render_to_string(
        "weddingwrangle/email_template.html", {"email_text": merged_message}
    )
    return merged_message, rendered_message


class EmailConfirm(LoginRequiredMixin, UpdateView):
    model = Email
    template_name_suffix = "_confirm"
    success_url = reverse_lazy("email_create")
    fields = "__all__"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["uncontactable_guests"] = False
        for guest in self.get_object().audience.guest.all():
            if guest.email_address == "":
                context["uncontactable_guests"] = True
        return context

    def post(self, request, *args, **kwargs):
        """Override post() method in order to set the email's date_sent to now, mark the
        email as sent on the guest's record, send the email
        and redirect the browser. This must be done with HttpResponseRedirect because
        the form won't validate (it has no data)"""
        self.object = self.get_object()
        self.object.date_sent = datetime.now()
        self.object.save()
        for guest in self.object.audience.guest.all():
            if guest.email_address == "":
                continue
            guest.emails.add(self.object)
            first_name = guest.first_name
            rsvp_link = guest.rsvp_link
            rsvp_url = self.request.build_absolute_uri(
                reverse("rsvp", args=[rsvp_link])
            )
            rsvp_url_html = "<a href='" + rsvp_url + "'>" + rsvp_url + "</a>"
            merged_message, rendered_message = generate_message(
                self, first_name, rsvp_url, rsvp_url_html
            )

            # https://docs.djangoproject.com/en/4.2/topics/email/
            send_mail(
                self.object.subject,
                message=merged_message,
                from_email=settings.FROM_EMAIL,
                recipient_list=[guest.email_address],
                fail_silently=False,
                html_message=rendered_message,
            )

        return HttpResponseRedirect(self.get_success_url())


class EmailDetail(LoginRequiredMixin, DetailView):
    model = Email
    template_name = "weddingwrangle/email_detail.html"


class GuestUpload(LoginRequiredMixin, View):
    template_name = "weddingwrangle/guest_upload.html"
    success_url = reverse_lazy("guest_list")

    def get(self, request):
        form = CSVForm()
        return render(request, self.template_name, {"form": form})

    def post(self, request):
        form = CSVForm(request.POST, request.FILES)
        if form.is_valid():
            file = StringIO(request.FILES["csv"].read().decode("utf-8"))
            csv_import.csv_import_base(file)
            return HttpResponseRedirect(self.success_url)
        return render(request, self.template_name, {"form": form})


@login_required
def export_csv(response):
    """Exports a CSV file of the guestlist"""

    # https://docs.djangoproject.com/en/4.2/howto/outputting-csv/
    date = datetime.today().strftime("%Y-%m-%d")
    response = HttpResponse(
        content_type="text/csv",
        headers={
            "Content-Disposition": f"attachment; filename=guest_export_{date}.csv"
        },
    )

    writer = csv.writer(response)
    writer.writerow(
        [
            "ID",
            "Title",
            "First name",
            "Surname",
            "Email address",
            "Position",
            "RSVP",
            "RSVP at",
            "Partner first name",
            "Partner surname",
            "Dietaries",
        ]
    )
    for guest in Guest.objects.all():
        rsvp_at = ""
        if guest.partner != None:
            partner_first = guest.partner.first_name
            partner_surname = guest.partner.surname
        if guest.rsvp_at != None:
            rsvp_at = guest.rsvp_at.strftime("%Y-%m-%d %H:%M")

        dietaries = [dietary.name for dietary in guest.dietaries.all()]

        writer.writerow(
            [
                guest.pk,
                guest.title.name,
                guest.first_name,
                guest.surname,
                guest.email_address,
                guest.position.name,
                guest.rsvp_status.name,
                rsvp_at,
                partner_first,
                partner_surname,
                dietaries,
            ]
        )

    return response


@login_required
def export_qr(request):
    """Exports QR codes in a zip file; each QR code is named after the appropriate guest"""

    folder = "weddingwrangle/qr_codes/"
    zip_filename = "weddingwrangle_qr_code_export"
    zip_full_filename = zip_filename + ".zip"

    for filename in os.listdir(folder):
        file_path = os.path.join(folder, filename)
        try:
            if os.path.isfile(file_path) or os.path.islink(file_path):
                os.unlink(file_path)
            elif os.path.isdir(file_path):
                shutil.rmtree(file_path)
        except Exception as e:
            print("Failed to delete %s. Reason: %s" % (file_path, e))

    for guest in Guest.objects.all():
        filename = (
            folder
            + guest.first_name.lower()
            + "_"
            + guest.surname.lower()
            + "_"
            + "qr.png"
        )
        qr_options = QRCodeOptions(image_format="png", size="s")
        current_site = get_current_site(request)
        protocol = "https" if request.is_secure() else "http"
        path = reverse("rsvp", args=[guest.rsvp_link])
        rsvp_url = f"{protocol}://{current_site}{path}"
        file = open(filename, "wb")
        file.write(make_qr_code_image(rsvp_url, qr_options))
        file.close()

    shutil.make_archive(zip_filename, "zip", folder)

    response = HttpResponse(
        open(zip_full_filename, "rb").read(),
        content_type="application/zip",
        headers={"Content-Disposition": f"attachment; filename={zip_filename}"},
    )

    return response
