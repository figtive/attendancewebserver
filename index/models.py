from django.db import models

# Create your models here.

class Students(models.Model):
    serial_number = models.CharField(max_length=50)
    name = models.CharField(max_length=30)
    npm = models.IntegerField(max_length=10)

class Course(models.model):
    name = models.CharField(max_length=50)

class Classes(models.Model):
    class_name = models.ForeignKey(Course, on_delete=models.CASCADE)
    time_start = models.TimeField()
    time_end = models.TimeField()

class Attendance(models.Model):
    atendee = models.ForeignKey(Students, on_delete=models.CASCADE)
    class_attend = models.ForeignKey(Classes, on_delete=models.CASCADE)