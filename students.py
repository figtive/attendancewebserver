from django.db import models

class Student(models.Model):
    serial_number = models.CharField()
    name = models.CharField( 
        max_length=25,
    )
    npm = models.IntegerField(
        max_length=10)