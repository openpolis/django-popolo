# -*- coding: utf-8 -*-
# Generated by Django 1.11.20 on 2019-05-08 16:21
from __future__ import unicode_literals

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('popolo', '0019_auto_20190306_1140'),
    ]

    operations = [
        migrations.AlterUniqueTogether(
            name='link',
            unique_together=set([('url', 'note')]),
        ),
        migrations.AlterUniqueTogether(
            name='source',
            unique_together=set([('url', 'note')]),
        ),
    ]