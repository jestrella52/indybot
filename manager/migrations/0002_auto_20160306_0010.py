# -*- coding: utf-8 -*-
# Generated by Django 1.9.4 on 2016-03-06 05:10
from __future__ import unicode_literals

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('manager', '0001_initial'),
    ]

    operations = [
        migrations.AlterModelTable(
            name='country',
            table='country',
        ),
        migrations.AlterModelTable(
            name='driver',
            table='driver',
        ),
        migrations.AlterModelTable(
            name='start',
            table='start',
        ),
    ]
