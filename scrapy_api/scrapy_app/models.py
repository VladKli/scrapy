from django.db import models
from django.utils import timezone
from django.contrib.postgres.fields import ArrayField


class Chemicals(models.Model):
    """
    Model representing chemicals information.
    """

    datetime = models.DateTimeField(default=timezone.now)
    availability = models.BooleanField(default=False)
    company_name = models.CharField(max_length=255)
    product_url = models.CharField(max_length=255)
    numcas = models.CharField(max_length=255)
    name = models.CharField(max_length=255)
    qt_list = ArrayField(models.FloatField())
    unit_list = ArrayField(models.CharField())
    currency_list = ArrayField(models.CharField())
    price_pack_list = ArrayField(models.CharField())

    class Meta:
        """
        Meta class for specifying model options.
        """

        ordering = ["-datetime"]

    def __str__(self):
        """
        String representation of the Chemicals object.
        """
        return self.name
