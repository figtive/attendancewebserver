from django.db import models

# Create your models here.

class Classes(models.Model):
    class_start = models.DateTimeField()
    class_end = models.DateTimeField()
