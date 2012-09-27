import uuid

from django.db import models

class Server(models.Model):
    name        = models.CharField(max_length=255)
    address     = models.IPAddressField()
    port        = models.IntegerField()
    timestamp   = models.DateTimeField(auto_now=True, auto_now_add=True)
