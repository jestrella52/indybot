# -*- coding: utf-8 -*-
# Generated by Django 1.9.4 on 2016-06-02 14:27
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('manager', '0039_auto_20160515_1203'),
    ]

    operations = [
        migrations.AddField(
            model_name='race',
            name='hashtag',
            field=models.CharField(blank=True, max_length=20, null=True),
        ),
    ]
