# Generated by Django 5.2a1 on 2025-03-01 11:42

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('calendarapp', '0002_alter_event_tables'),
    ]

    operations = [
        migrations.AddField(
            model_name='event',
            name='total_time',
            field=models.FloatField(default=0),
        ),
    ]
