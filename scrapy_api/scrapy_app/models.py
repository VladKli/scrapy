from django.db import models
from django.utils import timezone
from django.contrib.postgres.fields import ArrayField


class Product(models.Model):
    datetime = models.DateTimeField(default=timezone.now)
    availability = models.BooleanField(default=False)
    company_name = models.CharField(max_length=255)
    product_url = models.URLField()
    numcas = models.CharField(max_length=255)
    name = models.CharField(max_length=255)
    qt_list = ArrayField(models.IntegerField())
    unit_list = ArrayField(models.CharField())
    currency_list = ArrayField(models.CharField())
    price_pack_list = ArrayField(models.IntegerField())

    def __str__(self):
        return self.name
