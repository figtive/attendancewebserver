from django.db import models
from students.py import Student

class attendance(models.Model):
    attendee = models.ForeignKey(Student.npm)