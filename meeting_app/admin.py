from django.contrib import admin
from meeting_app import models

# Register your models here.
admin.site.register(models.Profile)
admin.site.register(models.BookedMeeting)
admin.site.register(models.ShareLink)
admin.site.register(models.AvailableSlot)

