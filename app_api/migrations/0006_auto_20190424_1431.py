# -*- coding: utf-8 -*-
# Generated by Django 1.11.16 on 2019-04-24 14:31
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('app_api', '0005_floorcomments_replied_comment'),
    ]

    operations = [
        migrations.AlterField(
            model_name='postbars',
            name='name',
            field=models.CharField(max_length=30, verbose_name='吧名'),
        ),
        migrations.AlterField(
            model_name='postfloor',
            name='post',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='post_floor', to='app_api.Post', verbose_name='帖子'),
        ),
    ]
