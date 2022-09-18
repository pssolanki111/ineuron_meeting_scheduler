from django.db import models
from django.contrib.auth.models import User
import secrets

# Create your models here.


def generate_random_string():
    return secrets.token_urlsafe(16)
    

class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    name = models.CharField(max_length=256, blank=True, null=True, default='')
    time_zone = models.CharField(max_length=256, blank=True, null=True, default='Asia/Kolkata')
    is_google_acc_linked = models.BooleanField(default=False)
    
    # Google calendar API
    access_token = models.CharField(max_length=256, blank=True, null=True, default='')
    refresh_token = models.CharField(max_length=256, blank=True, null=True, default='')
    token_uri = models.CharField(max_length=256, blank=True, null=True, default='')
    client_id = models.CharField(max_length=256, blank=True, null=True, default='')
    client_secret = models.CharField(max_length=256, blank=True, null=True, default='')
    scopes = models.CharField(max_length=256, blank=True, null=True, default='')
    
    objects = models.Manager()
    
    def __str__(self):
        return f'Profile of {self.user}'


class AvailableSlot(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='available_slots')
    start_time = models.DateTimeField()
    end_time = models.DateTimeField()

    objects = models.Manager()
    
    class Meta:
        verbose_name_plural = 'Available Slots'
        verbose_name = 'Available Slot'
        
    def __str__(self):
        return f'user {self.user} available from {self.start_time} to {self.end_time}'


class ShareLink(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='booking_sharing_links')
    link = models.CharField(max_length=256, unique=True, default=generate_random_string)
    title = models.CharField(max_length=256, blank=True, null=True, default='')
    description = models.TextField(blank=True, null=True, default='')
    available_slots = models.JSONField(default=list)

    objects = models.Manager()

    class Meta:
        verbose_name_plural = 'Share Links'
        verbose_name = 'Share Link'

    def __str__(self):
        return f'{self.user} | {self.title}'
    
    
class BookedMeeting(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='booked_meetings')
    meeting_with = models.ForeignKey(User, on_delete=models.CASCADE)
    title = models.CharField(max_length=256, blank=True, null=True, default='')
    user_name = models.CharField(max_length=256, blank=True, null=True, default='')
    user_email = models.CharField(max_length=256, blank=True, null=True, default='')
    description = models.TextField(blank=True, null=True, default='')
    start_time = models.DateTimeField()
    end_time = models.DateTimeField()
    booked_with_link = models.ForeignKey(ShareLink, on_delete=models.PROTECT)
    
    objects = models.Manager()
    
    class Meta:
        verbose_name_plural = 'Booked Meetings'
        verbose_name = 'Booked Meeting'
    
    def __str__(self):
        return f'{self.user} with {self.meeting_with} from ' \
               f'{self.start_time} to {self.end_time}'
    
