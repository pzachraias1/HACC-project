from django.db import models
from datetime import date

from django.utils.timezone import now


# Create your models here.
class Url(models.Model):
    longLink = models.CharField(max_length=1000)
    shortCode = models.CharField(max_length=30)
    creationDate = models.DateField(default=date.today)
    clicks = models.IntegerField(default=0)
    status = models.CharField(max_length=10, default="Pending")
    verification = models.BooleanField(default=False)

class IP_Adresses(models.Model):
    shortCode = models.ForeignKey(Url, on_delete=models.CASCADE)
    ip_address = models.GenericIPAddressField(default='192.168.0.1')
    visitedDate = models.DateTimeField(default=now)
    city = models.CharField(max_length=50, default='Na', null=True)
    region = models.CharField(max_length=50, default='Na', null=True)
    country = models.CharField(max_length=50, default='Na', null=True)
    longitude = models.CharField(max_length=50, default='Na', null=True)
    latitude = models.CharField(max_length=50, default='Na', null=True)

class Verification_Table(models.Model):
    shortCode = models.ForeignKey(Url, on_delete=models.CASCADE)
    password = models.CharField(max_length=100)
