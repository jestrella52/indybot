# -*- coding: utf-8 -*-
# Generated by Django 1.9.4 on 2016-05-04 19:37
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('manager', '0033_auto_20160504_1536'),
    ]

    operations = [
        migrations.AddField(
            model_name='season',
            name='champion',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='season_champion', to='manager.Driver'),
        ),
    ]
