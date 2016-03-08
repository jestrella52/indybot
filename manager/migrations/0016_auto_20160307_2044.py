# -*- coding: utf-8 -*-
# Generated by Django 1.9.4 on 2016-03-08 01:44
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('manager', '0015_remove_result_course'),
    ]

    operations = [
        migrations.CreateModel(
            name='Winner',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('year', models.IntegerField()),
            ],
            options={
                'db_table': 'winner',
            },
        ),
        migrations.AlterField(
            model_name='course',
            name='country',
            field=models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='manager.Country'),
        ),
        migrations.AlterField(
            model_name='driver',
            name='country',
            field=models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='manager.Country'),
        ),
        migrations.AddField(
            model_name='winner',
            name='course',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='manager.Course'),
        ),
        migrations.AddField(
            model_name='winner',
            name='driver',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='manager.Driver'),
        ),
    ]
