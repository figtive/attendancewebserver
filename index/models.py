from django.db import models

# Create your models here.

class Students(models.Model):
    serial_number = models.CharField(max_length=50)
    name = models.CharField(max_length=30)
    npm = models.IntegerField()
    def __str__(self):
        return 'Student: ' + self.name

class Courses(models.Model):
    name = models.CharField(max_length=50)
    def __str__(self):
        return 'Course: ' + self.name

class Classes(models.Model):
    class_name = models.ForeignKey(Courses, on_delete=models.CASCADE)
    time_start = models.TimeField()
    time_end = models.TimeField()
    def __str__(self):
        return 'Class: ' + str(self.class_name)
 
class Attendance(models.Model):
    atendee = models.ForeignKey(Students, on_delete=models.CASCADE)
    class_attend = models.ForeignKey(Classes, on_delete=models.CASCADE)
    attendtime = models.DateTimeField(auto_now_add=True)
    def __str__(self):
        return 'Attendance: ' + str(self.atendee) + ' at ' + str(self.class_attend)