# Generated by Django 4.2.2 on 2023-06-23 15:28

import django.contrib.postgres.fields
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("scrapy_app", "0001_initial"),
    ]

    operations = [
        migrations.AlterField(
            model_name="product",
            name="price_pack_list",
            field=django.contrib.postgres.fields.ArrayField(
                base_field=models.CharField(), size=None
            ),
        ),
        migrations.AlterField(
            model_name="product",
            name="product_url",
            field=models.CharField(max_length=255),
        ),
    ]
