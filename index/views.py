from django.shortcuts import render
from .models import Attendance
# Create your views here.

def index(request):
    attendees = Attendance.objects.all()
    return render(request, 'index.html',{'attendees':attendees})