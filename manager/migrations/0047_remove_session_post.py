# -*- coding: utf-8 -*-
# Generated by Django 1.9.4 on 2016-06-14 14:58
from __future__ import unicode_literals

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('manager', '0046_merge'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='session',
            name='post',
        ),
    ]
