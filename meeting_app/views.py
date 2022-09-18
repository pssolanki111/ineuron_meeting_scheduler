from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.contrib.auth.models import User
from meeting_app import models
import pytz
from datetime import datetime
from django.db.models import Q
from dateutil.parser import parse as parse_dt
import google.oauth2.credentials
from django.conf import settings
import google_auth_oauthlib.flow
import os
from googleapiclient.discovery import build
from django.contrib.sites.models import Site
from uuid import uuid4


def dt_to_str(request, dt: datetime):
    tz = pytz.timezone(request.user.profile.time_zone)
    return f"{dt.strftime('%d %b %I:%M %p')}"


GOOGLE_TOKEN_FILE = os.path.join(settings.BASE_DIR, 'token.json')
SCOPES = ['https://www.googleapis.com/auth/calendar']


def normalize_dt(request, dt_str: str) -> datetime:
    tz = pytz.timezone(request.user.profile.time_zone)
    dt = parse_dt(dt_str)
    
    return dt.replace(tzinfo=tz) if (dt.tzinfo is None) or (
            dt.tzinfo.utcoffset(dt) is None) \
        else dt


@login_required(login_url='/login/')
def home(request):
    all_meetings_for_user = models.BookedMeeting.objects.filter(Q(meeting_with=request.user) | 
                                                                Q(user=request.user))
    
    upcoming_meetings = [{'start_time': dt_to_str(request, x.start_time),
                          'end_time': dt_to_str(request, x.end_time), 
                          'with': str(x.meeting_with.username) if request.user == x.user else str(x.user.username),
                          'title': x.title, 'description': x.description, 'id': x.id}
                         for x in all_meetings_for_user]
    upcoming_meetings.sort(key=lambda x: x['start_time'])

    flow = google_auth_oauthlib.flow.Flow.from_client_secrets_file(GOOGLE_TOKEN_FILE, scopes=SCOPES)
    flow.redirect_uri = 'https://ineuron.pssolanki.com/google_cal_oauth2/'
    auth_url, state = flow.authorization_url(access_type='offline', include_granted_scopes='true')
    print(f'created auth url: {auth_url}')
    
    request.session['state'] = state
    
    context = {'upcoming_meetings': upcoming_meetings, 'google_oauth_url': auth_url}
    
    return render(request, 'meeting_app/home.html', context=context)


@login_required(login_url='/login/')
def availability_view(request):
    available_slots = models.AvailableSlot.objects.filter(user=request.user)
    available_slots = [{'start_time': dt_to_str(request, x.start_time),
                        'end_time': dt_to_str(request, x.end_time), 'id': x.id,
                        'start_dt': str(x.start_time), 'end_dt': str(x.end_time)}
                       for x in available_slots]
    
    context = {'available_slots': available_slots}
    return render(request, 'meeting_app/availability.html', context)


@login_required(login_url='/login/')
def links_view(request):
    share_links_for_admin = models.ShareLink.objects.filter(user=request.user)

    domain = Site.objects.get_current().domain
    
    url = 'https://{domain}/links/{slug}'

    share_links = [{'title': x.title, 'description': x.description, 'id': x.id,
                    'full_slug': url.format(domain=domain, slug=x.link)} for x in share_links_for_admin]
    
    # final = []
    # 
    # for link in share_links_for_admin:
    #     internal = []
    #     for x in link.available_slots:
    #         y = models.AvailableSlot.objects.get(id=x)
    #         
    #         internal.append({'start_time': dt_to_str(request, y.start_time),
    #                          'end_time': dt_to_str(request, y.end_time), 'id': y.id,
    #                          'start_dt': str(y.start_time), 'end_dt': str(y.end_time)})
    #         
    #     final.append(internal)
    
    print([x['full_slug'] for x in share_links])
    
    context = {'share_links': share_links}
    return render(request, 'meeting_app/links.html', context)
    

@login_required(login_url='/login/')
def create_link_view(request):
    if request.method != 'POST':
        available_slots = models.AvailableSlot.objects.filter(user=request.user)
        available_slots = [{'start_time': dt_to_str(request, x.start_time),
                            'end_time': dt_to_str(request, x.end_time), 'id': x.id}
                           for x in available_slots]

        context = {'available_slots': available_slots}
        return render(request, 'meeting_app/create_link.html', context)
    
    slots = request.POST.getlist('selected_slots_list', [])
    
    print(f'got slots: {type(slots)} | {slots}')
    
    if not slots:
        messages.error(request, 'You must select at least one availability slot to create a link')
        return render(request, 'meeting_app/create_link.html')
    
    title = request.POST.get('title', '').strip()
    description = request.POST.get('description', '').strip()
    
    if models.ShareLink.objects.filter(user=request.user, title=title).exists():
        messages.error(request, 'You seem to have an existing link with this title. Please enter a different title')
        return render(request, 'meeting_app/create_link.html')
    
    # Create the object
    obj = models.ShareLink(user=request.user, title=title, description=description)
    obj.available_slots = [int(x) for x in slots]
    obj.save()
        
    return redirect('/links/')


@login_required
def add_availability_view(request):
    start_time = request.POST.get('start_time', '')
    end_time = request.POST.get('end_time', '')
    
    if start_time == '' or end_time == '':
        context = {}
        messages.error(request, f'Please select both start and end time')
        return render(request, 'meeting_app/create_slot.html', context=context)
    
    start_time = normalize_dt(request, start_time)
    end_time = normalize_dt(request, end_time)
    
    if models.AvailableSlot.objects.filter(user=request.user, start_time=start_time, end_time=end_time).exists():
        context = {}
        messages.error(request, f'You already have an availability slot in this duration')
        return render(request, 'meeting_app/create_slot.html', context=context)
    
    # slots = [(x.start_time, x.end_time)
    #          for x in models.AvailableSlot.objects.filter(user=request.user)] + [(start_time, end_time)]
    # slots.sort(key=lambda x: x[0])
    # 
    # for index in range(len(slots)):
    #     if slots[index - 1][1] > slots[index][0]:
    #         messages.error(request, f'The duration overlaps with your previous availability '
    #                                 f'slots. Please ensure there are no overlaps')
    #         return render(request, 'meeting_app/create_slot.html', context={})
        
    obj = models.AvailableSlot(user=request.user, start_time=start_time, end_time=end_time)
    obj.save()
    
    messages.info(request, 'Availability slot added successfully')
    return redirect('/availability/')


@login_required
def remove_availability_view(request, slot_id: int):
    try:
        models.AvailableSlot.objects.filter(id=slot_id).delete()
        return redirect('/availability/')
    except:
        return redirect('/availability/')
               
               
@login_required
def remove_link_view(request, link_id: int):
    try:
        models.ShareLink.objects.filter(id=link_id).delete()
        return redirect('/links/')
    except:
        return redirect('/links/')


@login_required
def book_appointment_view(request, link_slug: str):
    if not request.user.profile.is_google_acc_linked:
        messages.error(request, 'You must link your Google calendar to book an appointment')
        return redirect('/')

    if not models.ShareLink.objects.filter(link=link_slug).exists():
        messages.error(request, 'The link you are trying to access no longer exists')
        return render(request, 'meeting_app/book_appointment.html', context={'status': '404'})

    obj = models.ShareLink.objects.get(link=link_slug)

    admin_user = obj.user

    if admin_user == request.user:
        return redirect('/links/')

    slots = [int(x) for x in obj.available_slots]

    if len(slots) < 1:
        obj.delete()
        return redirect('/links/')

    slf = []
    if request.method != 'POST':
        for x in slots:
            x = models.AvailableSlot.objects.get(id=x)

            slf.append({'start_time': dt_to_str(request, x.start_time),
                        'end_time': dt_to_str(request, x.end_time), 'id': x.id,
                        'start_dt': str(x.start_time), 'end_dt': str(x.end_time)})

        context = {'book_with': str(obj.user.username), 'title': obj.title,
                   'description': obj.description, 'slots': slf}

        return render(request, 'meeting_app/book_appointment.html', context=context)

    # Proceed to verify the info before confirming the appointment booking
    name = request.POST.get('name', '')

    if name == '':
        name = request.user.profile.name

    email = request.POST.get('email', '')

    if email == '':
        email = request.user.email

    title = request.POST.get('title', '')

    if title == '':
        title = obj.title

    description = request.POST.get('description', '')

    if description == '':
        description = obj.description

    selected_slot = request.POST.get('slot_selected').split('&&')

    start_time, end_time = normalize_dt(request, selected_slot[0]), normalize_dt(request, selected_slot[1])

    if not models.AvailableSlot.objects.filter(user=admin_user, start_time=start_time, end_time=end_time).exists():
        messages.error(request, 'The selected slot is no longer available. Please select another slot')
        return redirect(f'/links/{link_slug}')

    # All verifications done. Create the appointment
    obj = models.BookedMeeting(user=admin_user, meeting_with=request.user, title=title, description=description,
                               user_name=name, user_email=email, start_time=start_time, end_time=end_time,
                               booked_with_link=obj)
    obj.save()

    # Create Google Calendar Event
    profile = request.user.profile
    credentials = google.oauth2.credentials.Credentials(profile.access_token, profile.refresh_token,
                                                        profile.token_id, profile.token_uri, profile.client_id,
                                                        profile.client_secret, profile.scopes)

    service = build('calendar', 'v3', credentials=credentials)

    event = service.events().insert(calendarId='primary',
                                    body={'summary': title, 'description': description,
                                          'start': {'dateTime': start_time.isoformat()},
                                          'end': {'dateTime': end_time.isoformat()},
                                          "conferenceDataVersion": 1,
                                          "conferenceData": {
                                              "createRequest": {
                                                  "conferenceSolutionKey": {
                                                      "type": "hangoutsMeet"
                                                  },
                                                  "requestId": f'{uuid4().hex}'
                                              }}},
                                    conferenceDataVersion=1, sendNotifications=True).execute()

    print(f'created event: {event.get("htmlLink")} for user {request.user}. ev: {event}')

    return redirect('/')


def google_cal_oauth2_view(request):
    error = request.GET.get('error', None)
    
    if error:
        messages.error(request, 'There was an error while linking your Google account. Please try again later')
        return redirect('/')

    flow = google_auth_oauthlib.flow.Flow.from_client_secrets_file(
        GOOGLE_TOKEN_FILE,
        scopes=SCOPES, state=request.session['state'])
    flow.redirect_uri = 'https://ineuron.pssolanki.com/google_cal_oauth2/'

    flow.fetch_token(authorization_response=request.build_absolute_uri())
    
    creds = flow.credentials
    
    profile = request.user.profile
    profile.access_token = creds.token
    profile.refresh_token = creds.refresh_token
    profile.token_uri = creds.token_uri
    profile.client_id = creds.client_id
    profile.client_secret = creds.client_secret
    profile.scopes = creds.scopes
    profile.is_google_acc_linked = True
    profile.save()
    
    return redirect('/')


def login_view(request):
    if request.user.is_authenticated:
        return redirect('/')
    
    if request.method != 'POST':
        return render(request, 'auth/login.html', context={})
    
    user_name = request.POST.get('u-id', '')
    password = request.POST.get('u-pwd', '')
    user = authenticate(request, username=user_name, password=password)
    
    if user is not None:
        login(request, user)
        return redirect('/')
    
    messages.error(request, 'Invalid username or password')
    return render(request, 'auth/login.html')


def signup_view(request):
    if request.user.is_authenticated:
        return redirect('/')
    
    if request.method != 'POST':
        tz_list = list(pytz.all_timezones).copy()
        tz_list.remove('US/Eastern')
        
        context = {'timezone_lists': tz_list, 'default_tz': 'Asia/Kolkata'}
        return render(request, 'auth/signup.html', context)
    
    name = request.POST['name'].strip()
    email = request.POST['email'].strip()
    username = request.POST['username'].strip()
    password = request.POST['password'].strip()
    time_zone = request.POST['timezone'].strip()
    confirm_password = request.POST['confirm_password'].strip()
    
    if name == '' or email == '' or password == '' or confirm_password == '':
        messages.error(request, 'Invalid Input(s). Please make sure to provide valid inputs for all the fields')
        return redirect('/signup/')
    
    if not (time_zone in pytz.all_timezones_set):
        messages.error(request, 'Invalid timezone. Please choose a valid timezone')
        return redirect('/signup/')
    
    if not password == confirm_password:
        messages.error(request, 'Passwords do not match')
        return redirect('/signup/')
    
    if User.objects.filter(username=username).exists():
        messages.error(request, 'Username already taken. Please choose a different username')
        return redirect('/signup/')
    
    if User.objects.filter(email=email).exists():
        messages.error(request, 'User with that email already exists. Please sign into existing account or use a '
                                'different email address')
        return redirect('/signup/')
    
    user = User.objects.create_user(username, email, password)
    user.save()
    
    profile = models.Profile(user=user, name=name, time_zone=time_zone)
    profile.save()
    
    login(request, user)
    return redirect('/')


def logout_view(request):
    if request.user.is_authenticated:
        logout(request)
        
    return redirect('/login/')


def credentials_to_dict(credentials):
    return {'token': credentials.token,
            'refresh_token': credentials.refresh_token,
            'token_uri': credentials.token_uri,
            'client_id': credentials.client_id,
            'client_secret': credentials.client_secret,
            'scopes': credentials.scopes}

