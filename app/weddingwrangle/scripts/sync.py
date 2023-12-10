from weddingwrangle.models import (
    Guest,
    Audience,
)

def sync_audience(guest):
    """Add the guest to the relevant Audience."""
    # Pick an appropriate audience
    potential = Audience.objects.get(name="All potential guests (excludes Declined)")
    no_response = Audience.objects.get(name="All guests yet to RSVP")
    attending = Audience.objects.get(name="All attending guests")
    guest.audiences.clear()
    if guest.position.name != "Guest":
        return guest
    elif guest.rsvp_status.name == "Accepted":
        guest.audiences.add(attending, potential)
    elif guest.rsvp_status.name == "Declined":
        guest.audiences.clear()
    elif guest.rsvp_status.name == "Pending":
        guest.audiences.add(no_response, potential)
    return guest
            
def sync_partner(guest):
    if guest.partner is not None and guest.partner.partner is None:
        guest.partner.partner = guest
        guest.partner.save()
    return guest

def run():
    for guest in Guest.objects.all(): 
        guest = sync_audience(guest)
        guest = sync_partner(guest)
