from django.shortcuts import render, redirect
from django.views.generic import TemplateView
from .models import Attendance, Courses

def index(request):
    attendees = Attendance.objects.all()
    return render(request, 'index.html', {
        'attendees' :attendees,
    })


