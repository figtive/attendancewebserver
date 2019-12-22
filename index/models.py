from django.db import models

DAYS_OF_WEEK = (
    ('0', 'Monday'),
    ('1', 'Tuesday'),
    ('2', 'Wednesday'),
    ('3', 'Thursday'),
    ('4', 'Friday'),
    ('5', 'Saturday'),
    ('6', 'Sunday'),
)

class Student(models.Model):
    serial_number = models.CharField(max_length=50)
    name = models.CharField(max_length=50)
    npm = models.IntegerField()
    def __str__(self):
        return 'Student {}'.format(self.name)

class Lecturer(models.Model):
    serial_number = models.CharField(max_length=50)
    name = models.CharField(max_length=50)
    def __str__(self):
        return 'Lecturer {}'.format(self.name)

class Course(models.Model):
    code = models.CharField(max_length=30)
    name = models.CharField(max_length=50)
    lecturer = models.ForeignKey(Lecturer, on_delete=models.CASCADE)
    def __str__(self):
        return 'Course {}'.format(self.name)

class CourseClass(models.Model):
    course = models.ForeignKey(Course, on_delete=models.CASCADE)
    day = models.CharField(max_length=1, choices=DAYS_OF_WEEK)
    start_time = models.TimeField()
    end_time = models.TimeField()
    def __str__(self):
        return 'Class {} {}'.format(self.course.name, DAYS_OF_WEEK[int(self.day)][1])

class Meeting(models.Model):
    course_class = models.ForeignKey(CourseClass, on_delete=models.CASCADE)
    start_date_time = models.DateTimeField(auto_now_add=True)
    def __str__(self):
        return 'Meeting {} {}'.format(self.course_class.course.name,
            self.start_date_time)

class Record(models.Model):
    date_time = models.DateTimeField(auto_now_add=True)
    payload = models.TextField()
    def __str__(self):
        return 'Record {} {}'.format(self.date_time, self.payload)

class Attendance(models.Model):
    student = models.ForeignKey(Student, on_delete=models.CASCADE)
    meeting = models.ForeignKey(Meeting, on_delete=models.CASCADE)
    record = models.ForeignKey(Record, on_delete=models.CASCADE)
    def __str__(self):
        return 'Attendance {} {} {}'.format(self.student.name, \
            self.meeting.course_class.course.name, self.record.date_time)
