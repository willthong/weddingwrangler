from django.db import models


class Title(models.Model):
    name = models.CharField(max_length=10)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name_plural = "Titles"


class Position(models.Model):
    name = models.CharField(max_length=5)

    def __str__(self):
        return self.name


class RSVPStatus(models.Model):
    name = models.CharField(max_length=11)
    verbose_name = models.CharField(max_length=50)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "RSVP Status"
        verbose_name_plural = "RSVP Statuses"


class Dietary(models.Model):
    name = models.CharField(max_length=30)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name_plural = "Dietaries"


class DietaryOther(models.Model):
    name = models.CharField(max_length=30)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name_plural = "Dietaries (Other)"


class Audience(models.Model):
    name = models.CharField(max_length=30)

    def __str__(self):
        return self.name

    # M2M relationship with guests is defined within Guest class


class Email(models.Model):
    subject = models.CharField(max_length=100)
    sent = models.BooleanField(default=False)
    audiences = models.ManyToManyField(Audience, related_name="email")

    def __str__(self):
        return self.subject


class Guest(models.Model):
    # Unlinked fields
    first_name = models.CharField(max_length=30)
    surname = models.CharField(max_length=30)
    email_address = models.CharField(max_length=50, blank=True)
    rsvp_link = models.CharField(max_length=15, verbose_name="RSVP Link")
    rsvp_qr = models.BinaryField(
        null=True, blank=True, editable=True, verbose_name="RSVP QR"
    )

    # One-to-many fields
    title = models.ForeignKey(Title, on_delete=models.CASCADE, related_name="guest")
    position = models.ForeignKey(
        Position, on_delete=models.CASCADE, related_name="guest"
    )
    rsvp_status = models.ForeignKey(
        RSVPStatus,
        on_delete=models.CASCADE,
        related_name="guest",
        verbose_name="RSVP Status",
    )
    partner = models.ForeignKey(
        "self",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )

    # Many-to-many fields
    dietaries = models.ManyToManyField(Dietary, related_name="guest", blank=True)
    emails = models.ManyToManyField(Email, related_name="guest", blank=True)
    audiences = models.ManyToManyField(Audience, related_name="guest", blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        self.full_name = self.first_name + " " + self.surname
        return self.full_name
