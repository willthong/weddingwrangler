import csv
import random
import string
from weddingwrangle.models import (
    Title,
    Position,
    RSVPStatus,
    Dietary,
    Guest,
)

def generate_key():
    while True:
        key="".join(
            random.choices(
                string.ascii_uppercase + string.ascii_lowercase + string.digits, k=10
            )
        )
        # Check randomness
        try:
            Guest.objects.get(rsvp_link=key)
        except Guest.DoesNotExist:
            break
        pass
    return key

def csv_import_base(file_handler):
    reader = csv.reader(file_handler)
    next(reader)  # Skip header row

    Guest.objects.all().delete()

    for row in reader:
        print(row)

        # Generate a unique 10-character string for the guest
        rsvp_link = generate_key()

        guest, created = Guest.objects.get_or_create(
            title=Title.objects.get(name=row[0]),
            first_name=row[1],
            surname=row[2],
            email_address=row[3],
            position=Position.objects.get(name=row[5]),
            rsvp_status=RSVPStatus.objects.get(name="Pending"),
            rsvp_link=rsvp_link,
        )

        # Process dietaries
        dietary_list = row[4].split(",")
        try:
            for dietary in dietary_list:
                dietary = dietary.strip()
                dietary_id=Dietary.objects.get(name=dietary)
                guest.dietaries.add(dietary_id)
        except Dietary.DoesNotExist:
            pass

        guest.save()

def run():
   file_handler = open("weddingwrangle/import_data.csv")
   csv_import_base(file_handler)

