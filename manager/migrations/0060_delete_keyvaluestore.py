# -*- coding: utf-8 -*-
# Generated by Django 1.9.4 on 2017-08-01 01:42
from __future__ import unicode_literals

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('manager', '0059_keyvaluestore'),
    ]

    operations = [
        migrations.DeleteModel(
            name='KeyValueStore',
        ),
    ]
