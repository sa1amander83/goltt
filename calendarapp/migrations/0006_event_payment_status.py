# Generated by Django 4.2.19 on 2025-04-15 12:25

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('calendarapp', '0005_event_is_paid'),
    ]

    operations = [
        migrations.AddField(
            model_name='event',
            name='payment_status',
            field=models.CharField(choices=[('pending', 'Ожидает оплаты'), ('paid', 'Оплачено'), ('canceled', 'Отменено')], default='pending', max_length=20),
        ),
    ]
