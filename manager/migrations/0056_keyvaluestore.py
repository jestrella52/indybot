# -*- coding: utf-8 -*-
# Generated by Django 1.9.4 on 2017-06-05 17:38
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('manager', '0055_race_headerimgurl'),
    ]

    operations = [
        migrations.CreateModel(
            name='KeyValueStore',
            fields=[
                ('key', models.CharField(db_index=True, max_length=200, primary_key=True, serialize=False, unique=True)),
                ('value', models.TextField()),
            ],
        ),
    ]
