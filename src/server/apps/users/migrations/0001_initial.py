# -*- coding: utf-8 -*-
# Generated by Django 1.10.1 on 2017-05-12 21:29
from __future__ import unicode_literals

from django.conf import settings
import django.contrib.auth.models
from django.db import migrations, models
import django.db.models.deletion
import smart_selects.db_fields


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('auth', '0001_initial'),
        ('catalog', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='User',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('password', models.CharField(max_length=128, verbose_name='password')),
                ('last_login', models.DateTimeField(blank=True, null=True, verbose_name='last login')),
                ('username', models.CharField(db_index=True, max_length=40, unique=True)),
                ('email', models.EmailField(blank=True, max_length=100)),
                ('fullname', models.CharField(max_length=100, verbose_name='Full Name')),
                ('address', models.CharField(max_length=250)),
                ('date_joined', models.DateField(auto_now=True)),
                ('is_staff', models.BooleanField(default=False)),
                ('is_active', models.BooleanField(default=True)),
                ('is_superuser', models.BooleanField(default=False)),
            ],
            options={
                'abstract': False,
            },
            managers=[
                ('objects', django.contrib.auth.models.UserManager()),
            ],
        ),
        migrations.CreateModel(
            name='Experiment',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('experiment_number', models.IntegerField(blank=True, help_text='HFIR Experiment Number (expXXX)', null=True)),
            ],
        ),
        migrations.CreateModel(
            name='Ipts',
            fields=[
                ('group_ptr', models.OneToOneField(auto_created=True, on_delete=django.db.models.deletion.CASCADE, parent_link=True, primary_key=True, serialize=False, to='auth.Group')),
                ('instrument', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='ipts_instruments', related_query_name='ipts_instrument', to='catalog.Instrument')),
            ],
            options={
                'verbose_name': 'Integrated Proposal Tracking System (IPTS) number',
                'verbose_name_plural': 'IPTSs',
            },
            bases=('auth.group',),
        ),
        migrations.CreateModel(
            name='UserProfile',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('home_institution', models.CharField(blank=True, max_length=200)),
                ('experiment', smart_selects.db_fields.ChainedForeignKey(auto_choose=True, blank=True, chained_field='ipts', chained_model_field='ipts', null=True, on_delete=django.db.models.deletion.CASCADE, to='users.Experiment')),
                ('facility', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='catalog.Facility')),
                ('instrument', smart_selects.db_fields.ChainedForeignKey(auto_choose=True, chained_field='facility', chained_model_field='facility', on_delete=django.db.models.deletion.CASCADE, to='catalog.Instrument')),
                ('ipts', smart_selects.db_fields.ChainedForeignKey(auto_choose=True, blank=True, chained_field='instrument', chained_model_field='instrument', null=True, on_delete=django.db.models.deletion.CASCADE, to='users.Ipts')),
                ('user', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='profile', related_query_name='profile', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name': 'Profile',
            },
        ),
        migrations.AddField(
            model_name='experiment',
            name='ipts',
            field=models.ForeignKey(blank=True, help_text='This IPTS will be used to find your data on ICat. If you leave it empty the ICat lookup will not work!', null=True, on_delete=django.db.models.deletion.CASCADE, related_name='experiment_iptss', related_query_name='experiment_ipts', to='users.Ipts', verbose_name='Integrated Proposal Tracking System (IPTS) number'),
        ),
        migrations.AddField(
            model_name='user',
            name='groups',
            field=models.ManyToManyField(blank=True, help_text='The groups this user belongs to. A user will get all permissions granted to each of their groups.', related_name='user_set', related_query_name='user', to='auth.Group', verbose_name='groups'),
        ),
        migrations.AddField(
            model_name='user',
            name='user_permissions',
            field=models.ManyToManyField(blank=True, help_text='Specific permissions for this user.', related_name='user_set', related_query_name='user', to='auth.Permission', verbose_name='user permissions'),
        ),
    ]
