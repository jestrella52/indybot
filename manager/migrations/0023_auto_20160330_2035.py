# -*- coding: utf-8 -*-
# Generated by Django 1.9.4 on 2016-03-31 00:35
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('manager', '0022_auto_20160330_2017'),
    ]

    operations = [
        migrations.AddField(
            model_name='race',
            name='subpostrace',
            field=models.CharField(blank=True, max_length=10, null=True),
        ),
        migrations.AddField(
            model_name='race',
            name='subpractice',
            field=models.CharField(blank=True, max_length=10, null=True),
        ),
    ]
