from django.contrib import admin

# Register your models here.

from .models import Country, Location, Organization, UserHome, Action, Gathering, Gathering_Witness

admin.site.register(Country)
admin.site.register(Location)
admin.site.register(Organization)
admin.site.register(UserHome)
admin.site.register(Action)
admin.site.register(Gathering)
admin.site.register(Gathering_Witness)
