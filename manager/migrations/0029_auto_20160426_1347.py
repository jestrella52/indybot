# -*- coding: utf-8 -*-
# Generated by Django 1.9.4 on 2016-04-26 17:47
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('manager', '0028_auto_20160426_1206'),
    ]

    operations = [
        migrations.AlterField(
            model_name='race',
            name='leadchanges',
            field=models.IntegerField(blank=True, null=True),
        ),
    ]
