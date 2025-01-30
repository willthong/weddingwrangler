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

class Starter(models.Model):
    name = models.CharField(max_length=500)

    def __str__(self):
        return self.name


class Main(models.Model):
    name = models.CharField(max_length=500)

    def __str__(self):
        return self.name

class Audience(models.Model):
    # M2M relationship with guests is defined within Guest class
    name = models.CharField(max_length=100)
    positions = models.ManyToManyField(Position, related_name="audience", blank=True)
    rsvp_statuses = models.ManyToManyField(RSVPStatus, related_name="audience", blank=True)

    def __str__(self):
        return self.name



class Email(models.Model):
    subject = models.CharField(max_length=100)
    text = models.CharField(max_length=10000000)
    date_sent = models.DateTimeField(auto_now=False, auto_now_add=False, null=True)
    audience = models.ForeignKey(
        Audience, 
        on_delete=models.CASCADE, 
        related_name="email", 
        null=True
    )

    def __str__(self):
        return self.subject


class Guest(models.Model):
    # Unlinked fields
    first_name = models.CharField(max_length=30)
    surname = models.CharField(max_length=30)
    email_address = models.CharField(max_length=50, blank=True)
    rsvp_link = models.CharField(max_length=15, verbose_name="RSVP Link")
    rsvp_qr = models.BinaryField(
        null=True, blank=True, editable=False, verbose_name="RSVP QR"
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
    starter = models.ForeignKey(
        Starter,
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )
    main = models.ForeignKey(
        Main,
        on_delete=models.CASCADE,
        null=True,
        blank=True
    )

    # Many-to-many fields
    dietaries = models.ManyToManyField(Dietary, related_name="guest", blank=True)
    emails = models.ManyToManyField(Email, related_name="guest", blank=True)
    audiences = models.ManyToManyField(Audience, related_name="guest", blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    rsvp_at = models.DateTimeField(blank=True, null=True)

    # One-to-one field
    partner = models.OneToOneField("self", null=True, blank=True, on_delete=models.SET_NULL)

    def __str__(self):
        return self.first_name + " " + self.surname
