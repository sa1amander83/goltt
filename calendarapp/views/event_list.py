from datetime import timezone
from decimal import Decimal
from django.contrib.auth.mixins import LoginRequiredMixin

from django.contrib.admin.views.decorators import staff_member_required
from django.db.models import Sum, F
from django.shortcuts import render
from django.utils.decorators import method_decorator
from django.views import View
from django.views.generic import ListView

from calendarapp.models import Event
from calendarapp.models.event import Tables

class AllEventsListView(LoginRequiredMixin, ListView):
    model = Event
    template_name = 'calendarapp/events_list.html'
    context_object_name = 'events'
    paginate_by = 20

    def get_queryset(self):
        queryset = super().get_queryset()
        
        # Фильтрация по статусу
        status = self.request.GET.get('status')
        if status == 'running':
            queryset = queryset.filter(
                start_time__lte=timezone.now(),
                end_time__gte=timezone.now(),
                is_canceled=False
            )
        elif status == 'upcoming':
            queryset = queryset.filter(
                start_time__gt=timezone.now(),
                is_canceled=False
            )
        elif status == 'completed':
            queryset = queryset.filter(
                end_time__lt=timezone.now(),
                is_canceled=False
            )
        
        # Для админов - все события, для обычных пользователей - только свои
        if not self.request.user.is_superuser:
            queryset = queryset.filter(user=self.request.user)
            
        return queryset.select_related('table', 'user').order_by('-start_time')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['current_status'] = self.request.GET.get('status', 'all')
        return context


class RunningEventsListView(ListView):
    """ Running events list view """
    template_name = "calendarapp/events_list.html"
    model = Event

    def get_queryset(self):
        return Event.objects.get_running_events(user=self.request.user)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['status_choices'] = dict(Event.PAYMENT_STATUS_CHOICES)
        context['current_status'] = 'running'
        return context


class UpcomingEventsListView(ListView):
    """ Upcoming events list view """
    template_name = "calendarapp/events_list.html"
    model = Event

    def get_queryset(self):
        return Event.objects.get_upcoming_events(user=self.request.user)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['status_choices'] = dict(Event.PAYMENT_STATUS_CHOICES)
        context['current_status'] = 'upcoming'
        return context


class CompletedEventsListView(ListView):
    """ Completed events list view """
    template_name = "calendarapp/events_list.html"
    model = Event

    def get_queryset(self):
        return Event.objects.get_completed_events(user=self.request.user)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['status_choices'] = dict(Event.PAYMENT_STATUS_CHOICES)
        context['current_status'] = 'completed'
        return context

from django.views.generic import TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin
from calendarapp.models.event import Event, Tables
from django.db.models import Sum
from django.utils.timezone import now
from decimal import Decimal


class AdminStatsView(LoginRequiredMixin, TemplateView):
    template_name = "calendarapp/admin_stats.html"

    def get(self, request, *args, **kwargs):
        today = now().date()
        current_month = int(request.GET.get('month', today.month))
        current_year = int(request.GET.get('year', today.year))

        # Получение доступных месяцев и годов
        months = list(range(1, 13))
        years = list(range(today.year - 1, today.year + 1))  # например, с прошлого года до текущего

        tables = Tables.objects.all()
        table_stats = []

        total_daily_income = 0
        total_monthly_income = 0
        total_past_month_income = 0

        for table in tables:
            # Вычисление дохода за день и количество бронирований за день
            daily_bookings = Event.objects.filter(
                table=table, start_time__date=today
            )
            daily_income = daily_bookings.aggregate(total_daily_income=Sum('total_cost'))['total_daily_income'] or Decimal(0)
            daily_booking_count = daily_bookings.count()

            # Вычисление дохода за месяц и количество бронирований за месяц
            monthly_bookings = Event.objects.filter(
                table=table,
                start_time__month=current_month,
                start_time__year=current_year
            )
            monthly_income = monthly_bookings.aggregate(total_monthly_income=Sum('total_cost'))['total_monthly_income'] or Decimal(0)
            monthly_booking_count = monthly_bookings.count()

            # Вычисление дохода за прошедший месяц по событиям, которые уже состоялись
            past_month = current_month - 1 if current_month > 1 else 12
            past_year = current_year if current_month > 1 else current_year - 1

            past_month_bookings = Event.objects.filter(
                table=table,
                start_time__month=past_month,
                start_time__year=past_year,
                end_time__lt=now()  # События, которые уже завершились
            )
            past_month_income = past_month_bookings.aggregate(total_past_month_income=Sum('total_cost'))['total_past_month_income'] or Decimal(0)

            total_daily_income += float(daily_income)
            total_monthly_income += float(monthly_income)
            total_past_month_income += float(past_month_income)

            table_stats.append({
                "table_number": table.id,
                "daily_income": daily_income,
                "monthly_income": monthly_income,
                "past_month_income": past_month_income,
                "total_bookings_today": daily_booking_count,
                "total_bookings_month": monthly_booking_count,
            })

        context = {
            "table_stats": table_stats,
            "total_daily_income": total_daily_income,
            "total_monthly_income": total_monthly_income,
            "total_past_month_income": total_past_month_income,
            "months": months,
            "years": years,
            "current_month": current_month,
            "current_year": current_year,
        }
        return self.render_to_response(context)