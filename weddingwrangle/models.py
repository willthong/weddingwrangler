from django.db import models


class Title(models.Model):
    name = models.CharField(max_length=10)


class Position(models.Model):
    name = models.CharField(max_length=5)


class RSVPStatus(models.Model):
    name = models.CharField(max_length=5)


class Partnership(models.Model):
    pass


class Dietary(models.Model):
    name = models.CharField(max_length=30)


class Audience(models.Model):
    name = models.CharField(max_length=30)
    # M2M relationship with guests is defined within Guest class


class Email(models.Model):
    subject = models.CharField(max_length=100)
    sent = models.BooleanField(default=False)
    audiences = models.ManyToManyField(Audience, related_name="email")


class Guest(models.Model):
    # Unlinked fields
    first_name = models.CharField(max_length=30)
    surname = models.CharField(max_length=30)
    email_address = models.CharField(max_length=50)
    rsvp_link = models.CharField(max_length=15)
    rsvp_qr = models.BinaryField(null=True, blank=True, editable=True)

    # One-to-many fields
    title = models.ForeignKey(Title, on_delete=models.CASCADE, related_name="guest")
    position = models.ForeignKey(
        Position, on_delete=models.CASCADE, blank=True, related_name="guest"
    )
    rsvp_status = models.ForeignKey(
        RSVPStatus, on_delete=models.CASCADE, related_name="guest"
    )
    partnership = models.ForeignKey(
        RSVPStatus,
        on_delete=models.CASCADE,
        blank=True,
        related_name="partnership_guest",
    )

    # Many-to-many fields
    dietaries = models.ManyToManyField(Dietary, related_name="guest")
    emails = models.ManyToManyField(Email, related_name="guest")
    audiences = models.ManyToManyField(Audience, related_name="guest")

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        self.full_name = self.first_name + " " + self.surname
        return self.full_name
