# Generated by Django 2.1.7 on 2019-03-06 10:40

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('popolo', '0018_auto_20190218_1653'),
    ]

    operations = [
        migrations.AlterField(
            model_name='electoralresult',
            name='event',
            field=models.ForeignKey(help_text='The generating electoral event', limit_choices_to={'event_type': 'ELE'}, on_delete=django.db.models.deletion.CASCADE, related_name='results', to='popolo.KeyEvent', verbose_name='Electoral event'),
        ),
        migrations.AlterField(
            model_name='membership',
            name='electoral_event',
            field=models.ForeignKey(blank=True, help_text='The electoral event that assigned this membership', limit_choices_to={'event_type__contains': 'ELE'}, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='memberships_assigned', to='popolo.KeyEvent', verbose_name='Electoral event'),
        ),
        migrations.AlterField(
            model_name='roletype',
            name='classification',
            field=models.ForeignKey(help_text='The OP_FORMA_GIURIDICA classification this role type is related to', limit_choices_to={'scheme': 'FORMA_GIURIDICA_OP'}, on_delete=django.db.models.deletion.CASCADE, related_name='role_types', to='popolo.Classification'),
        ),
    ]