# -*- coding: utf-8 -*-
# Generated by Django 1.11.16 on 2019-05-01 12:56
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('app_api', '0007_auto_20190501_1223'),
    ]

    operations = [
        migrations.AlterField(
            model_name='userdetailmsg',
            name='birthday',
            field=models.DateField(blank=True, null=True, verbose_name='生日'),
        ),
    ]