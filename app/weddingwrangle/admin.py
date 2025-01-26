from django.contrib import admin
from weddingwrangle.models import (
    Title,
    Position,
    RSVPStatus,
    Starter,
    Main,
    Dietary,
    Audience,
    Email,
    Guest,
)

# Register your models here.

admin.site.register(Guest)
admin.site.register(Title)
admin.site.register(Position)
admin.site.register(RSVPStatus)
admin.site.register(Starter)
admin.site.register(Main)
admin.site.register(Dietary)
admin.site.register(Audience)
admin.site.register(Email)
