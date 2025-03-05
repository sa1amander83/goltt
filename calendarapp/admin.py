from django.contrib import admin
from calendarapp import models
from .models.event import Tables


@admin.register(models.Event)
class EventAdmin(admin.ModelAdmin):
    model = models.Event
    list_display = [
        "id",
        "title",
        "user",
        "is_active",
        "is_deleted",
        "created_at",
        "updated_at",
        'table',
        'total_time'

    ]
    list_filter = ["is_active", "is_deleted", 'table']
    search_fields = ["title"]


@admin.register(models.EventMember)
class EventMemberAdmin(admin.ModelAdmin):
    model = models.EventMember
    list_display = ["id", "event", "user", "created_at", "updated_at", ]
    list_filter = ["event"]


from django.contrib import admin
from .models import Event

@admin.register(Tables)
class TableAdmin(admin.ModelAdmin):
    list_display = ('number', 'price_per_hour', 'price_per_half_hour', 'table_description')
    list_filter = ('number', 'price_per_hour', 'price_per_half_hour')

# @admin.register(Event)
# class EventAdmin(admin.ModelAdmin):
#     list_display = ('title', 'start_time', 'end_time')
#     filter_horizontal = ('tables',)


from django.contrib.admin.views.decorators import staff_member_required
from django.utils.decorators import method_decorator
from django.views import View
from django.shortcuts import render
from django.db.models import Count, Sum
from calendarapp.models.event import Event, Tables

