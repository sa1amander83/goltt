# calendarapp/utils.py
from calendar import HTMLCalendar
from .models import Event


class Calendar(HTMLCalendar):
    def __init__(self, year=None, month=None):
        self.year = year
        self.month = month
        super(Calendar, self).__init__()

    # formats a day as a td
    # filter events by day
    def formatday(self, day, events):
        events_per_day = events.filter(start_time__day=day)
        d = ""
        for event in events_per_day:
            d += f"<li> {event.get_html_url} </li>"
        if day != 0:
            return f"<td><span class='date'>{day}</span><ul> {d} </ul></td>"
        return "<td></td>"

    # formats a week as a tr
    def formatweek(self, theweek, events):
        week = ""
        for d, weekday in theweek:
            week += self.formatday(d, events)
        return f"<tr> {week} </tr>"

    # formats a month as a table
    # filter events by year and month
    def formatmonth(self, withyear=True):
        events = Event.objects.filter(
            start_time__year=self.year, start_time__month=self.month
        )
        cal = (
            '<table border="0" cellpadding="0" cellspacing="0" class="calendar">\n'
        )  # noqa
        cal += (
            f"{self.formatmonthname(self.year, self.month, withyear=withyear)}\n"
        )  # noqa
        cal += f"{self.formatweekheader()}\n"
        for week in self.monthdays2calendar(self.year, self.month):
            cal += f"{self.formatweek(week, events)}\n"
        return cal


# calendarapp/management/commands/check_payments.py
from django.core.management.base import BaseCommand
from calendarapp.models import Event
import logging

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Check pending payments status'

    def handle(self, *args, **options):
        pending_events = Event.objects.filter(payment_status='pending').exclude(payment_id__isnull=True)

        for event in pending_events:
            try:
                if event.update_payment_status():
                    logger.info(f"Updated payment status for event {event.id}")
                else:
                    logger.warning(f"Failed to update payment status for event {event.id}")
            except Exception as e:
                logger.error(f"Error checking payment for event {event.id}: {str(e)}")