# -*- coding: utf-8 -*-
# Generated by Django 1.9.4 on 2016-04-28 17:45
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('manager', '0030_auto_20160426_2210'),
    ]

    operations = [
        migrations.AddField(
            model_name='season',
            name='races',
            field=models.IntegerField(default=0),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name='race',
            name='season',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.PROTECT, to='manager.Season'),
        ),
    ]
