# -*- coding: utf-8 -*-
# Generated by Django 1.9.4 on 2016-04-25 20:46
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('manager', '0025_driver_dob'),
    ]

    operations = [
        migrations.AddField(
            model_name='driver',
            name='died',
            field=models.DateField(blank=True, null=True),
        ),
    ]
