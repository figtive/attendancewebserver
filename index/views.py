from django.shortcuts import render, redirect
from django.views.generic import TemplateView
from .models import Attendance, Course

def index(request):
    attendances = Attendance.objects.all()
    return render(request, 'index.html', {
        'attendances': attendances,
    })


