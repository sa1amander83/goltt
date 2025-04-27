from datetime import datetime

from django.core.validators import MinValueValidator, MaxValueValidator
from django.db import models
from django.template.defaultfilters import title
from django.urls import reverse

from calendarapp.models import EventAbstract
from accounts.models import User
from yookassa import Configuration, Payment
import logging

logger = logging.getLogger(__name__)


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
    price_per_hour = models.DecimalField(max_digits=6, decimal_places=2, default=300, verbose_name='Цена за час')
    price_per_half_hour = models.DecimalField(max_digits=6, decimal_places=2, default=200, verbose_name='Цена за пол часа')
    table_description = models.CharField(blank=True, null=True, max_length=12, verbose_name='Описание стола')

    def __str__(self):
        return f"Стол {self.number}"

    class Meta:
        verbose_name = 'Стол'
        verbose_name_plural = 'Столы'
class Event(EventAbstract):
    """ Event model """
    PAYMENT_STATUS_CHOICES = [
        ('pending', 'Ожидает оплаты'),
        ('paid', 'Оплачено'),
        ('canceled', 'Отменено'),
    ]
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="events",verbose_name='гость')
    title = models.CharField(max_length=200)
    description = models.TextField()
    start_time = models.DateTimeField(verbose_name='Время начала брони')
    end_time = models.DateTimeField(verbose_name='Время окончания брони')
    total_cost=models.FloatField(default=300)
    objects = EventManager()
    is_canceled = models.BooleanField('Отменено', default=False)
    cancel_reason = models.TextField('Причина отмены', blank=True, null=True)
    payment_status = models.CharField(
        max_length=20,
        choices=PAYMENT_STATUS_CHOICES,
        default='pending'
    )
    payment_id = models.CharField('ID платежа', max_length=100, blank=True, null=True)

    table = models.ForeignKey(Tables, on_delete=models.CASCADE, related_name="events", null=True, default=1, verbose_name='Стол')
    total_time=models.FloatField(default=0)
    is_paid = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Дата создания')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='Дата обновления')

    def __str__(self):
        return self.title

    def get_absolute_url(self):
        return reverse("calendarapp:event-detail", args=(self.id,))

    def update_payment_status(self):
        """Обновляет статус платежа из ЮKassa"""
        if not self.payment_id:
            return False

        try:
            payment = Payment.find_one(self.payment_id)
            self.payment_status = payment.status
            self.is_paid = (payment.status == 'succeeded')
            self.save()
            return True
        except Exception as e:
            logger.error(f"Error updating payment status: {str(e)}")
            return False


    @property
    def get_html_url(self):
        url = reverse("calendarapp:event-detail", args=(self.id,))
        return f'<a href="{url}"> {self.title} </a>'


class UserEventStats(EventAbstract):
    """ User event stats """

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="event_stats")
    table = models.ForeignKey(Tables, on_delete=models.CASCADE, related_name="event_stats")
    total_time = models.FloatField(default=0)
    total_cost = models.FloatField(default=0)
    total_events = models.IntegerField(default=0)

    def __str__(self):
        return str(self.user)


