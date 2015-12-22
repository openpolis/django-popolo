# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import model_utils.fields
import django.utils.text
import popolo.behaviors.models
import autoslug.fields
import django.utils.timezone
import django.core.validators


class Migration(migrations.Migration):

    dependencies = [
        ('contenttypes', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Area',
            fields=[
                ('object_id', models.CharField(max_length=256, null=True, blank=True)),
                ('start_date', models.CharField(validators=[django.core.validators.RegexValidator(regex=b'^[0-9]{4}(-[0-9]{2}){0,2}$', message=b'Date has wrong format'), popolo.behaviors.models.validate_partial_date], max_length=10, blank=True, help_text='The date when the validity of the item starts', null=True, verbose_name='start date')),
                ('end_date', models.CharField(validators=[django.core.validators.RegexValidator(regex=b'^[0-9]{4}(-[0-9]{2}){0,2}$', message=b'Date has wrong format'), popolo.behaviors.models.validate_partial_date], max_length=10, blank=True, help_text='The date when the validity of the item ends', null=True, verbose_name='end date')),
                ('created_at', model_utils.fields.AutoCreatedField(default=django.utils.timezone.now, verbose_name='creation time', editable=False)),
                ('updated_at', model_utils.fields.AutoLastModifiedField(default=django.utils.timezone.now, verbose_name='last modification time', editable=False)),
                ('id', autoslug.fields.AutoSlugField(populate_from=popolo.behaviors.models.get_slug_source, serialize=False, editable=False, primary_key=True)),
                ('name', models.CharField(help_text='A primary name', max_length=256, verbose_name='name', blank=True)),
                ('identifier', models.CharField(help_text='An issued identifier', max_length=512, verbose_name='identifier', blank=True)),
                ('classification', models.CharField(help_text='An area category, e.g. city', max_length=512, verbose_name='identifier', blank=True)),
                ('geom', models.TextField(help_text='A geometry', null=True, verbose_name='geom', blank=True)),
                ('inhabitants', models.IntegerField(help_text='The total number of inhabitants', null=True, verbose_name='inhabitants', blank=True)),
                ('content_type', models.ForeignKey(blank=True, to='contenttypes.ContentType', null=True)),
                ('parent', models.ForeignKey(related_name='children', blank=True, to='popolo.Area', help_text='The area that contains this area', null=True)),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='AreaI18Name',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(max_length=255, verbose_name='name')),
                ('area', models.ForeignKey(related_name='i18n_names', to='popolo.Area')),
            ],
            options={
                'verbose_name': 'I18N Name',
                'verbose_name_plural': 'I18N Names',
            },
        ),
        migrations.CreateModel(
            name='ContactDetail',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('object_id', models.CharField(max_length=256, null=True, blank=True)),
                ('start_date', models.CharField(validators=[django.core.validators.RegexValidator(regex=b'^[0-9]{4}(-[0-9]{2}){0,2}$', message=b'Date has wrong format'), popolo.behaviors.models.validate_partial_date], max_length=10, blank=True, help_text='The date when the validity of the item starts', null=True, verbose_name='start date')),
                ('end_date', models.CharField(validators=[django.core.validators.RegexValidator(regex=b'^[0-9]{4}(-[0-9]{2}){0,2}$', message=b'Date has wrong format'), popolo.behaviors.models.validate_partial_date], max_length=10, blank=True, help_text='The date when the validity of the item ends', null=True, verbose_name='end date')),
                ('created_at', model_utils.fields.AutoCreatedField(default=django.utils.timezone.now, verbose_name='creation time', editable=False)),
                ('updated_at', model_utils.fields.AutoLastModifiedField(default=django.utils.timezone.now, verbose_name='last modification time', editable=False)),
                ('label', models.CharField(help_text='A human-readable label for the contact detail', max_length=512, verbose_name='label', blank=True)),
                ('contact_type', models.CharField(help_text="A type of medium, e.g. 'fax' or 'email'", max_length=12, verbose_name='type', choices=[(b'ADDRESS', 'Address'), (b'EMAIL', 'Email'), (b'URL', 'Url'), (b'MAIL', 'Snail mail'), (b'TWITTER', 'Twitter'), (b'FACEBOOK', 'Facebook'), (b'PHONE', 'Telephone'), (b'MOBILE', 'Mobile'), (b'TEXT', 'Text'), (b'VOICE', 'Voice'), (b'FAX', 'Fax'), (b'CELL', 'Cell'), (b'VIDEO', 'Video'), (b'PAGER', 'Pager'), (b'TEXTPHONE', 'Textphone')])),
                ('value', models.CharField(help_text='A value, e.g. a phone number or email address', max_length=512, verbose_name='value')),
                ('note', models.CharField(help_text='A note, e.g. for grouping contact details by physical location', max_length=512, verbose_name='note', blank=True)),
                ('content_type', models.ForeignKey(blank=True, to='contenttypes.ContentType', null=True)),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='Identifier',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('object_id', models.CharField(max_length=256, null=True, blank=True)),
                ('identifier', models.CharField(help_text='An issued identifier, e.g. a DUNS number', max_length=512, verbose_name='identifier')),
                ('scheme', models.CharField(help_text='An identifier scheme, e.g. DUNS', max_length=128, verbose_name='scheme', blank=True)),
                ('content_type', models.ForeignKey(blank=True, to='contenttypes.ContentType', null=True)),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='Language',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('dbpedia_resource', models.CharField(help_text='DbPedia URI of the resource', unique=True, max_length=255)),
                ('iso639_1_code', models.CharField(max_length=2)),
                ('name', models.CharField(help_text='English name of the language', max_length=128)),
            ],
        ),
        migrations.CreateModel(
            name='Link',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('object_id', models.CharField(max_length=256, null=True, blank=True)),
                ('url', models.URLField(help_text='A URL', max_length=350, verbose_name='url')),
                ('note', models.CharField(help_text="A note, e.g. 'Wikipedia page'", max_length=512, verbose_name='note', blank=True)),
                ('content_type', models.ForeignKey(blank=True, to='contenttypes.ContentType', null=True)),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='Membership',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('start_date', models.CharField(validators=[django.core.validators.RegexValidator(regex=b'^[0-9]{4}(-[0-9]{2}){0,2}$', message=b'Date has wrong format'), popolo.behaviors.models.validate_partial_date], max_length=10, blank=True, help_text='The date when the validity of the item starts', null=True, verbose_name='start date')),
                ('end_date', models.CharField(validators=[django.core.validators.RegexValidator(regex=b'^[0-9]{4}(-[0-9]{2}){0,2}$', message=b'Date has wrong format'), popolo.behaviors.models.validate_partial_date], max_length=10, blank=True, help_text='The date when the validity of the item ends', null=True, verbose_name='end date')),
                ('created_at', model_utils.fields.AutoCreatedField(default=django.utils.timezone.now, verbose_name='creation time', editable=False)),
                ('updated_at', model_utils.fields.AutoLastModifiedField(default=django.utils.timezone.now, verbose_name='last modification time', editable=False)),
                ('label', models.CharField(help_text='A label describing the membership', max_length=512, verbose_name='label', blank=True)),
                ('role', models.CharField(help_text='The role that the person fulfills in the organization', max_length=512, verbose_name='role', blank=True)),
                ('area', models.ForeignKey(related_name='memberships', blank=True, to='popolo.Area', help_text='The geographic area to which the post is related', null=True)),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='Organization',
            fields=[
                ('start_date', models.CharField(validators=[django.core.validators.RegexValidator(regex=b'^[0-9]{4}(-[0-9]{2}){0,2}$', message=b'Date has wrong format'), popolo.behaviors.models.validate_partial_date], max_length=10, blank=True, help_text='The date when the validity of the item starts', null=True, verbose_name='start date')),
                ('end_date', models.CharField(validators=[django.core.validators.RegexValidator(regex=b'^[0-9]{4}(-[0-9]{2}){0,2}$', message=b'Date has wrong format'), popolo.behaviors.models.validate_partial_date], max_length=10, blank=True, help_text='The date when the validity of the item ends', null=True, verbose_name='end date')),
                ('created_at', model_utils.fields.AutoCreatedField(default=django.utils.timezone.now, verbose_name='creation time', editable=False)),
                ('updated_at', model_utils.fields.AutoLastModifiedField(default=django.utils.timezone.now, verbose_name='last modification time', editable=False)),
                ('slug', autoslug.fields.AutoSlugField(editable=False, populate_from=popolo.behaviors.models.get_slug_source, unique=True, slugify=django.utils.text.slugify)),
                ('id', autoslug.fields.AutoSlugField(populate_from=popolo.behaviors.models.get_slug_source, serialize=False, editable=False, primary_key=True)),
                ('name', models.CharField(help_text='A primary name, e.g. a legally recognized name', max_length=512, verbose_name='name')),
                ('summary', models.CharField(help_text='A one-line description of an organization', max_length=1024, verbose_name='summary', blank=True)),
                ('description', models.TextField(help_text='An extended description of an organization', verbose_name='biography', blank=True)),
                ('classification', models.CharField(help_text='An organization category, e.g. committee', max_length=512, verbose_name='classification', blank=True)),
                ('founding_date', models.CharField(validators=[django.core.validators.RegexValidator(regex=b'^[0-9]{4}(-[0-9]{2}){0,2}$', message=b'founding date must follow the given pattern: ^[0-9]{4}(-[0-9]{2}){0,2}$', code=b'invalid_founding_date')], max_length=10, blank=True, help_text='A date of founding', null=True, verbose_name='founding date')),
                ('dissolution_date', models.CharField(validators=[django.core.validators.RegexValidator(regex=b'^[0-9]{4}(-[0-9]{2}){0,2}$', message=b'dissolution date must follow the given pattern: ^[0-9]{4}(-[0-9]{2}){0,2}$', code=b'invalid_dissolution_date')], max_length=10, blank=True, help_text='A date of dissolution', null=True, verbose_name='dissolution date')),
                ('image', models.URLField(help_text='A URL of an image, to identify the organization visually', null=True, verbose_name='image', blank=True)),
                ('area', models.ForeignKey(related_name='organizations', blank=True, to='popolo.Area', help_text='The geographic area to which this organization is related', null=True)),
                ('parent', models.ForeignKey(related_name='children', blank=True, to='popolo.Organization', help_text='The organization that contains this organization', null=True)),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='OtherName',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('object_id', models.CharField(max_length=256, null=True, blank=True)),
                ('start_date', models.CharField(validators=[django.core.validators.RegexValidator(regex=b'^[0-9]{4}(-[0-9]{2}){0,2}$', message=b'Date has wrong format'), popolo.behaviors.models.validate_partial_date], max_length=10, blank=True, help_text='The date when the validity of the item starts', null=True, verbose_name='start date')),
                ('end_date', models.CharField(validators=[django.core.validators.RegexValidator(regex=b'^[0-9]{4}(-[0-9]{2}){0,2}$', message=b'Date has wrong format'), popolo.behaviors.models.validate_partial_date], max_length=10, blank=True, help_text='The date when the validity of the item ends', null=True, verbose_name='end date')),
                ('name', models.CharField(help_text='An alternate or former name', max_length=512, verbose_name='name')),
                ('note', models.CharField(help_text="A note, e.g. 'Birth name'", max_length=1024, verbose_name='note', blank=True)),
                ('content_type', models.ForeignKey(blank=True, to='contenttypes.ContentType', null=True)),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='Person',
            fields=[
                ('start_date', models.CharField(validators=[django.core.validators.RegexValidator(regex=b'^[0-9]{4}(-[0-9]{2}){0,2}$', message=b'Date has wrong format'), popolo.behaviors.models.validate_partial_date], max_length=10, blank=True, help_text='The date when the validity of the item starts', null=True, verbose_name='start date')),
                ('end_date', models.CharField(validators=[django.core.validators.RegexValidator(regex=b'^[0-9]{4}(-[0-9]{2}){0,2}$', message=b'Date has wrong format'), popolo.behaviors.models.validate_partial_date], max_length=10, blank=True, help_text='The date when the validity of the item ends', null=True, verbose_name='end date')),
                ('created_at', model_utils.fields.AutoCreatedField(default=django.utils.timezone.now, verbose_name='creation time', editable=False)),
                ('updated_at', model_utils.fields.AutoLastModifiedField(default=django.utils.timezone.now, verbose_name='last modification time', editable=False)),
                ('id', autoslug.fields.AutoSlugField(populate_from=popolo.behaviors.models.get_slug_source, serialize=False, editable=False, primary_key=True)),
                ('name', models.CharField(help_text="A person's preferred full name", max_length=512, verbose_name='name')),
                ('family_name', models.CharField(help_text='One or more family names', max_length=128, verbose_name='family name', blank=True)),
                ('given_name', models.CharField(help_text='One or more primary given names', max_length=128, verbose_name='given name', blank=True)),
                ('additional_name', models.CharField(help_text='One or more secondary given names', max_length=128, verbose_name='additional name', blank=True)),
                ('honorific_prefix', models.CharField(help_text="One or more honorifics preceding a person's name", max_length=128, verbose_name='honorific prefix', blank=True)),
                ('honorific_suffix', models.CharField(help_text="One or more honorifics following a person's name", max_length=128, verbose_name='honorific suffix', blank=True)),
                ('patronymic_name', models.CharField(help_text='One or more patronymic names', max_length=128, verbose_name='patronymic name', blank=True)),
                ('sort_name', models.CharField(help_text='A name to use in an lexicographically ordered list', max_length=128, verbose_name='sort name', blank=True)),
                ('email', models.EmailField(help_text='A preferred email address', max_length=254, null=True, verbose_name='email', blank=True)),
                ('gender', models.CharField(help_text='A gender', max_length=128, verbose_name='gender', blank=True)),
                ('birth_date', models.CharField(help_text='A date of birth', max_length=10, verbose_name='birth date', blank=True)),
                ('death_date', models.CharField(help_text='A date of death', max_length=10, verbose_name='death date', blank=True)),
                ('image', models.URLField(help_text='A URL of a head shot', null=True, verbose_name='image', blank=True)),
                ('summary', models.CharField(help_text="A one-line account of a person's life", max_length=1024, verbose_name='summary', blank=True)),
                ('biography', models.TextField(help_text="An extended account of a person's life", verbose_name='biography', blank=True)),
                ('national_identity', models.CharField(help_text='A national identity', max_length=128, null=True, verbose_name='national identity', blank=True)),
            ],
            options={
                'verbose_name_plural': 'People',
            },
        ),
        migrations.CreateModel(
            name='Post',
            fields=[
                ('start_date', models.CharField(validators=[django.core.validators.RegexValidator(regex=b'^[0-9]{4}(-[0-9]{2}){0,2}$', message=b'Date has wrong format'), popolo.behaviors.models.validate_partial_date], max_length=10, blank=True, help_text='The date when the validity of the item starts', null=True, verbose_name='start date')),
                ('end_date', models.CharField(validators=[django.core.validators.RegexValidator(regex=b'^[0-9]{4}(-[0-9]{2}){0,2}$', message=b'Date has wrong format'), popolo.behaviors.models.validate_partial_date], max_length=10, blank=True, help_text='The date when the validity of the item ends', null=True, verbose_name='end date')),
                ('created_at', model_utils.fields.AutoCreatedField(default=django.utils.timezone.now, verbose_name='creation time', editable=False)),
                ('updated_at', model_utils.fields.AutoLastModifiedField(default=django.utils.timezone.now, verbose_name='last modification time', editable=False)),
                ('id', autoslug.fields.AutoSlugField(populate_from=popolo.behaviors.models.get_slug_source, serialize=False, editable=False, primary_key=True)),
                ('label', models.CharField(help_text='A label describing the post', max_length=512, verbose_name='label', blank=True)),
                ('other_label', models.CharField(help_text='An alternate label, such as an abbreviation', max_length=512, null=True, verbose_name='other label', blank=True)),
                ('role', models.CharField(help_text='The function that the holder of the post fulfills', max_length=512, verbose_name='role', blank=True)),
                ('area', models.ForeignKey(related_name='posts', blank=True, to='popolo.Area', help_text='The geographic area to which the post is related', null=True)),
                ('organization', models.ForeignKey(related_name='posts', to='popolo.Organization', help_text='The organization in which the post is held')),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='Source',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('object_id', models.CharField(max_length=256, null=True, blank=True)),
                ('url', models.URLField(help_text='A URL', verbose_name='url')),
                ('note', models.CharField(help_text="A note, e.g. 'Parliament website'", max_length=512, verbose_name='note', blank=True)),
                ('content_type', models.ForeignKey(blank=True, to='contenttypes.ContentType', null=True)),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.AddField(
            model_name='membership',
            name='on_behalf_of',
            field=models.ForeignKey(related_name='memberships_on_behalf_of', blank=True, to='popolo.Organization', help_text='The organization on whose behalf the person is a party to the relationship', null=True),
        ),
        migrations.AddField(
            model_name='membership',
            name='organization',
            field=models.ForeignKey(related_name='memberships', blank=True, to='popolo.Organization', help_text='The organization that is a party to the relationship', null=True),
        ),
        migrations.AddField(
            model_name='membership',
            name='person',
            field=models.ForeignKey(related_name='memberships', to='popolo.Person', help_text='The person who is a party to the relationship'),
        ),
        migrations.AddField(
            model_name='membership',
            name='post',
            field=models.ForeignKey(related_name='memberships', blank=True, to='popolo.Post', help_text='The post held by the person in the organization through this membership', null=True),
        ),
        migrations.AddField(
            model_name='areai18name',
            name='language',
            field=models.ForeignKey(to='popolo.Language'),
        ),
        migrations.AlterUniqueTogether(
            name='areai18name',
            unique_together=set([('area', 'language', 'name')]),
        ),
    ]
