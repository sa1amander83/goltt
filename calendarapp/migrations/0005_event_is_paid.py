# Generated by Django 4.2.19 on 2025-04-08 14:25

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('calendarapp', '0004_remove_event_payment_status'),
    ]

    operations = [
        migrations.AddField(
            model_name='event',
            name='is_paid',
            field=models.BooleanField(default=False),
        ),
    ]
