# -*- coding: utf-8 -*-
# Generated by Django 1.11.15 on 2019-01-17 08:00
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('popolo', '0015_auto_20190117_0854'),
    ]

    operations = [
        migrations.AlterField(
            model_name='roletype',
            name='label',
            field=models.CharField(help_text='A label describing the post, better keep it unique and put the classification descr into it', max_length=512, verbose_name='label'),
        ),
    ]
