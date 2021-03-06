# -*- coding: utf-8 -*-
# Generated by Django 1.9.4 on 2016-04-27 02:10
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('manager', '0029_auto_20160426_1347'),
    ]

    operations = [
        migrations.CreateModel(
            name='Season',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('year', models.IntegerField()),
                ('seriesname', models.CharField(max_length=100)),
            ],
            options={
                'db_table': 'season',
            },
        ),
        migrations.AddField(
            model_name='race',
            name='season',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.PROTECT, to='manager.Country'),
        ),
    ]
