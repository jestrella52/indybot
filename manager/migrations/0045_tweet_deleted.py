# -*- coding: utf-8 -*-
# Generated by Django 1.9.4 on 2016-06-10 22:36
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('manager', '0044_auto_20160610_1731'),
    ]

    operations = [
        migrations.AddField(
            model_name='tweet',
            name='deleted',
            field=models.BooleanField(default=False),
        ),
    ]
