from django.db import models

# Create your models here.

class Students(models.Model):
    serial_number = models.CharField(max_length=50)
    name = models.CharField(max_length=30)
    npm = models.IntegerField()
    def __str__(self):
        return 'Student: ' + self.name

class Lecturer(models.Model):
    lecturer_uid = models.CharField(max_length=50)
    lecturer_name = models.CharField(max_length=30)
    def __str__(self):
        return 'Lecturer: ' + str(self.lecturer_name)

class Courses(models.Model):
    name = models.CharField(max_length=50)
    course_id = models.CharField(max_length=30)
    lecturer = models.ForeignKey(Lecturer,on_delete=models.CASCADE)

    def __str__(self):
        return 'Course: ' + self.name

class Classes(models.Model):
    class_name = models.ForeignKey(Courses, on_delete=models.CASCADE)
    time_start = models.TimeField()
    time_end = models.TimeField()
    def __str__(self):
        return 'Class: ' + str(self.class_name)

class Attendance(models.Model):
    student = models.ForeignKey(Students, on_delete=models.CASCADE)
    class_attend = models.ForeignKey(Classes, on_delete=models.CASCADE)
    time_attend = models.TimeField()
    def __str__(self):
        return 'Attendance: ' + str(self.student) + ' at ' + str(self.class_attend)