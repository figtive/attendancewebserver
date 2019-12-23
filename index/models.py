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

MEETING_TYPE = (
    ('0', 'normal'),
    ('1', 'substitute')
)

class Student(models.Model):
    serial_number = models.CharField(max_length=50)
    name = models.CharField(max_length=50)
    npm = models.IntegerField()
    class Meta:
        unique_together = ["npm"]
    def __str__(self):
        return 'Student {}'.format(self.name)

class Lecturer(models.Model):
    serial_number = models.CharField(max_length=50)
    name = models.CharField(max_length=50)
    npm = models.IntegerField()
    class Meta:
        unique_together = ["npm"]
    def __str__(self):
        return 'Lecturer {}'.format(self.name)

class Course(models.Model):
    code = models.CharField(max_length=30)
    name = models.CharField(max_length=50)
    lecturer = models.ForeignKey(Lecturer, on_delete=models.CASCADE, related_name="lecturer")
    class Meta:
        unique_together = ["code"]
    def __str__(self):
        return 'Course {}'.format(self.name)

class CourseClass(models.Model):
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name="course")
    day = models.CharField(max_length=1, choices=DAYS_OF_WEEK)
    start_time = models.TimeField()
    end_time = models.TimeField()
    class Meta:
        unique_together = ["course", "day", "start_time"]
    def __str__(self):
        return 'Class {} {}'.format(self.course.name, \
            DAYS_OF_WEEK[int(self.day)][1])

class Record(models.Model):
    date_time = models.DateTimeField(auto_now_add=True)
    payload = models.TextField()
    def __str__(self):
        return 'Record {} {}'.format(self.date_time, self.payload)

class Meeting(models.Model):
    course_class = models.ForeignKey(CourseClass, on_delete=models.CASCADE, related_name="course_class")
    record = models.ForeignKey(Record, on_delete=models.CASCADE)
    meeting_type = models.CharField(max_length=1, choices=MEETING_TYPE, \
        default='0')
    def __str__(self):
        return 'Meeting {} {} {}'.format(self.course_class.course.name, \
            MEETING_TYPE[int(self.meeting_type)][1], self.record.date_time)

class Registration(models.Model):
    course = models.ForeignKey(Course, on_delete=models.CASCADE)
    student = models.ForeignKey(Student, on_delete=models.CASCADE)

class Attendance(models.Model):
    student = models.ForeignKey(Student, on_delete=models.CASCADE)
    meeting = models.ForeignKey(Meeting, on_delete=models.CASCADE, related_name="meeting")
    record = models.ForeignKey(Record, on_delete=models.CASCADE)
    def __str__(self):
        return 'Attendance {} {} {}'.format(self.student.name, \
            self.meeting.course_class.course.name, self.record.date_time)
