# -*- coding: utf-8 -*-
# Generated by Django 1.9.4 on 2016-05-02 02:13
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('manager', '0031_auto_20160428_1345'),
    ]

    operations = [
        migrations.AlterField(
            model_name='race',
            name='channel',
            field=models.CharField(blank=True, max_length=15, null=True),
        ),
    ]