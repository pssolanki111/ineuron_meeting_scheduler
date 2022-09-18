"""ineuron URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/3.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""

from django.urls import path
from meeting_app import views

urlpatterns = [
    path('', views.home, name='home'),
    path('login/', views.login_view, name='login'),
    path('signup/', views.signup_view, name='signup'),
    path('logout/', views.logout_view, name='logout'),
    path('availability/', views.availability_view, name='availability'),
    path('add_availability/', views.add_availability_view, name='add_availability'),
    path('remove_availability/<int:slot_id>', views.remove_availability_view, name='remove_availability'),
    path('links/', views.links_view, name='links'),
    path('create_new_link/', views.create_link_view, name='create_new_link'),
    path('links/<str:link_slug>/', views.book_appointment_view, name='book_appointment'),
    path('remove_link/<int:link_id>', views.remove_link_view, name='remove_link'),
    path('google_cal_oauth2/', views.google_cal_oauth2_view, name='google_oauth_handler'),
]
