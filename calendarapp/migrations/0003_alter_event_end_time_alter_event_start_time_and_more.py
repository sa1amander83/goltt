# Generated by Django 5.1.6 on 2025-03-19 21:30

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('calendarapp', '0002_remove_event_cost_remove_event_tables_event_table_and_more'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.AlterField(
            model_name='event',
            name='end_time',
            field=models.DateTimeField(verbose_name='Время окончания брони'),
        ),
        migrations.AlterField(
            model_name='event',
            name='start_time',
            field=models.DateTimeField(verbose_name='Время начала брони'),
        ),
        migrations.AlterField(
            model_name='event',
            name='table',
            field=models.ForeignKey(default=1, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='events', to='calendarapp.tables', verbose_name='Стол'),
        ),
        migrations.AlterField(
            model_name='event',
            name='user',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='events', to=settings.AUTH_USER_MODEL, verbose_name='гость'),
        ),
        migrations.AlterField(
            model_name='tables',
            name='price_per_half_hour',
            field=models.DecimalField(decimal_places=2, default=200, max_digits=6, verbose_name='Цена за пол часа'),
        ),
        migrations.AlterField(
            model_name='tables',
            name='price_per_hour',
            field=models.DecimalField(decimal_places=2, default=300, max_digits=6, verbose_name='Цена за час'),
        ),
        migrations.AlterField(
            model_name='tables',
            name='table_description',
            field=models.CharField(blank=True, max_length=12, null=True, verbose_name='Описание стола'),
        ),
    ]
