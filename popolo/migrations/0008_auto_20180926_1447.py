# -*- coding: utf-8 -*-
# Generated by Django 1.11.15 on 2018-09-26 12:47
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('popolo', '0007_auto_20180921_1719'),
    ]

    operations = [
        migrations.AlterField(
            model_name='keyevent',
            name='event_type',
            field=models.CharField(choices=[('ELE', 'Election round'), ('ELE-POL', 'National election'), ('ELE-EU', 'European election'), ('ELE-REG', 'Regional election'), ('ELE-METRO', 'Metropolitan election'), ('ELE-PROV', 'Provincial election'), ('ELE-COM', 'Comunal election'), ('ITL', 'IT legislature'), ('EUL', 'EU legislature'), ('XAD', 'External administration')], default='ELE', help_text='The electoral type, e.g.: election, legislature, ...', max_length=12, verbose_name='event type'),
        ),
    ]
