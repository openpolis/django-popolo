# -*- coding: utf-8 -*-
# Generated by Django 1.11 on 2018-04-06 17:42
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('popolo', '0003_auto_20171228_1336'),
    ]

    operations = [
        migrations.AlterField(
            model_name='classificationrel',
            name='object_id',
            field=models.PositiveIntegerField(db_index=True, null=True),
        ),
        migrations.AlterField(
            model_name='contactdetail',
            name='object_id',
            field=models.PositiveIntegerField(db_index=True, null=True),
        ),
        migrations.AlterField(
            model_name='identifier',
            name='object_id',
            field=models.PositiveIntegerField(db_index=True, null=True),
        ),
        migrations.AlterField(
            model_name='linkrel',
            name='object_id',
            field=models.PositiveIntegerField(db_index=True, null=True),
        ),
        migrations.AlterField(
            model_name='othername',
            name='object_id',
            field=models.PositiveIntegerField(db_index=True, null=True),
        ),
        migrations.AlterField(
            model_name='sourcerel',
            name='object_id',
            field=models.PositiveIntegerField(db_index=True, null=True),
        ),
    ]