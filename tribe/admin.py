from django.contrib import admin

# Register your models here.

from .models import Country, Location, Revent, Person, Role, ContactInfo, ReventNote

admin.site.register(Country)
admin.site.register(Location)
admin.site.register(Revent)
admin.site.register(Person)
admin.site.register(Role)
admin.site.register(ContactInfo)
admin.site.register(ReventNote)
