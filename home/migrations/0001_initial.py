# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('wagtailcore', '0002_auto_20150624_1517'),
    ]

    operations = [
        migrations.CreateModel(
            name='DummyHomePage',
            fields=[
                ('page_ptr', models.OneToOneField(primary_key=True, to='wagtailcore.Page', parent_link=True, auto_created=True, serialize=False)),
            ],
            options={
                'abstract': False,
            },
            bases=('wagtailcore.page',),
        ),
        migrations.CreateModel(
            name='EventIndexPageGeo',
            fields=[
                ('page_ptr', models.OneToOneField(primary_key=True, to='wagtailcore.Page', parent_link=True, auto_created=True, serialize=False)),
                ('location_name', models.CharField(blank=True, max_length=255)),
            ],
            options={
                'abstract': False,
            },
            bases=('wagtailcore.page', models.Model),
        ),
        migrations.CreateModel(
            name='EventPageGeo',
            fields=[
                ('page_ptr', models.OneToOneField(primary_key=True, to='wagtailcore.Page', parent_link=True, auto_created=True, serialize=False)),
                ('location_name', models.CharField(blank=True, max_length=255)),
                ('text', models.CharField(max_length=255)),
            ],
            options={
                'abstract': False,
            },
            bases=('wagtailcore.page', models.Model),
        ),
        migrations.CreateModel(
            name='Location',
            fields=[
                ('id', models.AutoField(auto_created=True, serialize=False, verbose_name='ID', primary_key=True)),
                ('name', models.CharField(blank=True, max_length=255)),
                ('latitude', models.FloatField()),
                ('longitude', models.FloatField()),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.AddField(
            model_name='eventpagegeo',
            name='location',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to='home.Location', editable=False, related_name='+', blank=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='eventindexpagegeo',
            name='location',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to='home.Location', editable=False, related_name='+', blank=True),
            preserve_default=True,
        ),
    ]
