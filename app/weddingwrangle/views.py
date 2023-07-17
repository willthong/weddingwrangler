import csv
from io import StringIO
import os, shutil
from plotly.offline import plot
import plotly.graph_objs as graph_objs
from re import sub, search
from datetime import timedelta, datetime, time
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


class HomePage(LoginRequiredMixin, TemplateView):
    template_name = "weddingwrangle/home.html"

    # CR: here's a cleaner way to generate all the dates, using Python's list
    # comprehensions
    def get_all_guest_dates(self):
        start_date = Guest.objects.aggregate(Min("created_at"))["created_at__min"].date()
        days = (date.now() - start_date).days
        return [start_date + timedelta(day = day) for day in range(0, days + 1)]

    def get_all_guest_dates(self):
        start_date = Guest.objects.aggregate(Min("created_at"))["created_at__min"]
        start_date = datetime.combine(
            start_date.date(), time.min, tzinfo=timezone.get_default_timezone()
        )
        guest_number_dates = []
        while start_date <= timezone.now():
            guest_number_dates.append(start_date)
            start_date = start_date + timedelta(days=1)

        return guest_number_dates

    # CR: I know this is a function that Django needs you to have, but if you put
    # all the logic (apart form the bit that builds the context dict) in
    # 'get_plot_data' (or something similar) and call that from here it's more
    # obvious what this view is doing
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # CR: each of these little comment headers would be more clear if they
        # were a function, as I've changed here
        # CR: I'd probably just rename this variable 'dates'?  Especially if you
        # move all the logic into child functions
        guest_number_dates = self.get_all_guest_dates()

        # CR: it might be overkill for small code like this, but I prefer to have
        # one container with a namedtuple or something, so you'd write:

        # Somewhere above
        class AttendingStats(collections.namedtuple('AttendingStats', ['attending', 'declined']):
            # It's better if you calculate derived data instead of storing it,
            # that way it's harder for you to write a bug that
            # makes it out of sync with the data it's derived
            # from
            def total(self):
                return self.attending + self.declined

            # You could consider having some load from database function here that
            # takes a date, either as a static method or a toplevel function.

        # Then you use it like so:
        counts = [load_attending_stats(date) for date in guest_number_dates]
        attending_bar = graph_objs.Bar(
            ...
            y=[x.attending for x in counts],
            ...
        )


        attending_numbers = []
        declined_numbers = []
        total_guests = []
        for query_date in guest_number_dates:
            # CR: if django database models support a less than or equal mode I'd
            # use that instead, it's a little clearer
            query_date = query_date + timedelta(days=1)

            # CR: 'attending_count' isn't much longer but it is clearer
            att_count = (
                Guest.objects.filter(rsvp_at__lt=query_date)
                # CR: you should avoid magic numbers if possible, ie reading this
                # I don't know what 4 means. It's also not obvious from the
                # definition in models.
                #
                # Python has an enum library that's useful for this:
                #
                #   class Rsvp(Enum):
                #     ATTENDING = 4
                #     DECLINED = 5
                #     ...
                # And then in code you just write Rsvp.ATTENDING. Much clearer!
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

    # CR: one thing that isn't a big deal is that you can have partial success
    # here: if one of the emails fail I think you'll have sent all the emails from
    # before but none of the ones from after
    def post(self, request, *args, **kwargs):
        """Override post() method in order to set the email's date_sent to now, mark the
        email as sent on the guest's record, send the email
        and redirect the browser. This must be done with HttpResponseRedirect because
        the form won't validate (it has no data)"""
        self.object = self.get_object()
        self.object.date_sent = datetime.now()
        self.object.save()

        # CR: can you use [self.object] instead of calling [self.get_object()]
        # again?
        for guest in self.get_object().audience.guest.all():
            if guest.email_address == "":
                continue
            guest.emails.add(self.object)
            first_name = guest.first_name
            rsvp_link = guest.rsvp_link
            rsvp_url = self.request.build_absolute_uri(
                reverse("rsvp", args=[rsvp_link])
            )
            # CR: I'm not sure single quotes are valid HTML, unlike in Python
            rsvp_url_html = "<a href='" + rsvp_url + "'>" + rsvp_url + "</a>"

            # CR: I think it makes sense to pop the message generation in a function
            merged_message = self.object.text
            if search("{{ rsvp_qr_code }}", self.object.text):
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

            # https://stackoverflow.com/a/49894619/3161714
            rendered_message = render_to_string(
                "weddingwrangle/email_template.html", {"email_text": merged_message}
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
            "Content-Disposition": f"attachment; filename='guest_export_{date}.csv'"
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
            "Partner",
            "Dietaries",
        ]
    )
    for guest in Guest.objects.all():
        partner, rsvp_at = "", ""
        if guest.partner != None:
            partner = guest.partner.first_name + " " + guest.partner.surname
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
                partner,
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
