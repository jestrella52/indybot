# -*- coding: utf-8 -*-
# Generated by Django 1.9.4 on 2016-03-06 06:01
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('manager', '0005_type'),
    ]

    operations = [
        migrations.CreateModel(
            name='Course',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.TextField()),
                ('location', models.TextField()),
                ('length', models.FloatField()),
                ('url', models.TextField()),
                ('fastyear', models.IntegerField(blank=True, null=True)),
                ('fastlap', models.FloatField(blank=True, null=True)),
                ('gps', models.TextField()),
                ('shortname', models.CharField(max_length=20)),
                ('country', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='manager.Country')),
                ('coursetype', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='manager.Type')),
                ('fastdriver', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='manager.Driver')),
            ],
            options={
                'db_table': 'course',
            },
        ),
    ]
