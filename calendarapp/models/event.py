from datetime import datetime

from django.core.validators import MinValueValidator, MaxValueValidator
from django.db import models
from django.urls import reverse

from calendarapp.models import EventAbstract
from accounts.models import User


class EventManager(models.Manager):
    """ Event manager """

    def get_all_events(self, user):
        events = Event.objects.filter(user=user, is_active=True, is_deleted=False)
        return events

    def get_running_events(self, user):
        running_events = Event.objects.filter(
            user=user,
            is_active=True,
            is_deleted=False,
            end_time__gte=datetime.now(),
            start_time__lte=datetime.now()
        ).order_by("start_time")
        return running_events
    
    def get_completed_events(self, user):
        completed_events = Event.objects.filter(
            user=user,
            is_active=True,
            is_deleted=False,
            end_time__lt=datetime.now().date(),
        )
        return completed_events

    def get_upcoming_events(self, user):
        upcoming_events = Event.objects.filter(
            user=user,
            is_active=True,
            is_deleted=False,
            start_time__gt=datetime.now(),
            end_time__gt=datetime.now(),
        )
        return upcoming_events


class Tables(models.Model):
    number = models.IntegerField(unique=True, choices=[
        (1, 'Стол 1'),
        (2, 'Стол 2'),
        (3, 'Стол 3'),
        (4, 'Стол 4'),
    ])
    price_per_hour = models.DecimalField(max_digits=6, decimal_places=2, default=300)
    price_per_half_hour = models.DecimalField(max_digits=6, decimal_places=2, default=200)

    def __str__(self):
        return f"Стол {self.number}"

    class Meta:
        verbose_name = 'Стол'
        verbose_name_plural = 'Столы'
class Event(EventAbstract):
    """ Event model """

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="events")
    title = models.CharField(max_length=200)
    description = models.TextField()
    start_time = models.DateTimeField()
    end_time = models.DateTimeField()
    cost=models.IntegerField(default=300)
    objects = EventManager()
    tables = models.ForeignKey(Tables, on_delete=models.CASCADE, related_name="events", null=True)

    def __str__(self):
        return self.title

    def get_absolute_url(self):
        return reverse("calendarapp:event-detail", args=(self.id,))

    @property
    def get_html_url(self):
        url = reverse("calendarapp:event-detail", args=(self.id,))
        return f'<a href="{url}"> {self.title} </a>'
