# -*- coding: utf-8 -*-
# Generated by Django 1.9.4 on 2016-06-14 20:58
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('manager', '0048_auto_20160614_1633'),
    ]

    operations = [
        migrations.AddField(
            model_name='session',
            name='tvendtime',
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='session',
            name='tvstarttime',
            field=models.DateTimeField(blank=True, null=True),
        ),
    ]