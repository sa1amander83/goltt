# Generated by Django 4.2.19 on 2025-04-16 08:56

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('calendarapp', '0006_event_payment_status'),
    ]

    operations = [
        migrations.AddField(
            model_name='event',
            name='payment_id',
            field=models.CharField(blank=True, max_length=100, null=True, verbose_name='ID платежа'),
        ),
    ]
