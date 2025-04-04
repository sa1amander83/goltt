# cal/views.py

import json
from django.contrib import messages
from django.db.models import Sum, DurationField, F, Avg
from django.db.models.functions import Cast
from django.utils import timezone
from django.utils.dateparse import parse_datetime, parse_date
from django.shortcuts import render, redirect
from django.http import HttpResponseRedirect
from django.utils.timezone import now
from django.views import generic
from django.utils.safestring import mark_safe
from datetime import timedelta, datetime, date, time
import calendar
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy, reverse
from django.http import JsonResponse
from django.shortcuts import get_object_or_404

from accounts.models import User
from calendarapp.models import EventMember, Event
from calendarapp.models.event import Tables
from calendarapp.utils import Calendar
from calendarapp.forms import EventForm, AddMemberForm


def get_date(req_day):
    if req_day:
        year, month = (int(x) for x in req_day.split("-"))
        return date(year, month, day=1)
    return datetime.today()


def prev_month(d):
    first = d.replace(day=1)
    prev_month = first - timedelta(days=1)
    month = "month=" + str(prev_month.year) + "-" + str(prev_month.month)
    return month


def next_month(d):
    days_in_month = calendar.monthrange(d.year, d.month)[1]
    last = d.replace(day=days_in_month)
    next_month = last + timedelta(days=1)
    month = "month=" + str(next_month.year) + "-" + str(next_month.month)
    return month


class CalendarView(LoginRequiredMixin, generic.ListView):
    login_url = "accounts:signin"
    model = Event
    template_name = "calendar.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        d = get_date(self.request.GET.get("month", None))
        cal = Calendar(d.year, d.month)
        html_cal = cal.formatmonth(withyear=True)
        context["calendar"] = mark_safe(html_cal)
        context["prev_month"] = prev_month(d)
        context["next_month"] = next_month(d)
        return context


@login_required(login_url="signup")
def create_event(request):
    form = EventForm(request.POST or None)
    if request.POST and form.is_valid():
        title = form.cleaned_data["title"]
        description = form.cleaned_data["description"]
        start_time = form.cleaned_data["start_time"]
        end_time = form.cleaned_data["end_time"]
        total_time = form.cleaned_data["total_time"]

        table = form.cleaned_data["table"]

        Event.objects.get_or_create(
            user=request.user,
            title=title,
            description=description,
            start_time=start_time,
            end_time=end_time,
            table=table,
            total_time=total_time
        )
        return HttpResponseRedirect(reverse("calendarapp:calendar"))
    return render(request, "event.html", {"form": form})


class EventEdit(generic.UpdateView):
    model = Event
    fields = ["title", "description", "start_time", "end_time", "table"]
    template_name = "event.html"


@login_required(login_url="signup")
def event_details(request, event_id):
    event = Event.objects.get(id=event_id)
    eventmember = EventMember.objects.filter(event=event)
    context = {"event": event, "eventmember": eventmember}
    return render(request, "event-details.html", context)


def add_eventmember(request, event_id):
    forms = AddMemberForm()
    if request.method == "POST":
        forms = AddMemberForm(request.POST)
        if forms.is_valid():
            member = EventMember.objects.filter(event=event_id)
            event = Event.objects.get(id=event_id)
            if member.count() <= 9:
                user = forms.cleaned_data["user"]
                EventMember.objects.create(event=event, user=user)
                return redirect("calendarapp:calendar")
            else:
                print("--------------User limit exceed!-----------------")
    context = {"form": forms}
    return render(request, "add_member.html", context)


class EventMemberDeleteView(generic.DeleteView):
    model = EventMember
    template_name = "event_delete.html"
    success_url = reverse_lazy("calendarapp:calendar")


from django.http import JsonResponse
from django.utils.dateparse import parse_datetime
from django.shortcuts import render, redirect
from django.contrib import messages
import json
import logging
from django.views import generic
from django.contrib.auth.mixins import LoginRequiredMixin

TABLE_COLORS = {
    1: "#3498db",  # Синий
    2: "#2ecc71",  # Зеленый
    3: "#e74c3c",  # Красный
    4: "#9b59b6",  # Фиолетовый
    5: "#f1c40f",  # Желтый
    'user': "#2ecc71",  # Зеленый для своих событий
    'other': "#cccccc",  # Серый для чужих событий
    'default': "#3498db",  # Синий по умолчанию
}

logger = logging.getLogger(__name__)
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator


class CalendarViewNew(generic.View):
    # class CalendarViewNew(LoginRequiredMixin, generic.View):
    login_url = "accounts:signin"
    template_name = "calendarapp/calendar.html"
    form_class = EventForm

    def get(self, request, *args, **kwargs):
        form = self.form_class()
        current_time = now()
        today_start = datetime.combine(date.today(), datetime.min.time())
        today_end = today_start + timedelta(days=1)
        if request.GET.get('ajax') == 'get_available_tables':
            return self.get_available_tables(request)
        # Загружаем события с учетом связей, чтобы избежать лишних запросов
        # events_month = Event.objects.filter(
        #     start_time__month=date.today().month,
        #     start_time__year=date.today().year
        # ).select_related("table")
        events_all = Event.objects.all().select_related("table")
        # Текущие бронирования
        current_bookings = events_all.filter(start_time__lte=current_time, end_time__gte=current_time)

        # Подготовка списка событий
        event_list = []
        for event in events_all:
            is_owner = request.user.is_authenticated and event.user == request.user

            table_id = event.table.id if event.table else None
            color = TABLE_COLORS.get(table_id, "#3498db")
            event_list.append({
                "id": event.id,
                "title": event.title,
                "start": event.start_time.strftime("%Y-%m-%dT%H:%M:%S"),
                "end": event.end_time.strftime("%Y-%m-%dT%H:%M:%S"),
                "description": event.description,
                "color": self.get_event_color(event, request.user, is_owner),
                "backgroundColor": self.get_event_color(event, request.user, is_owner),
                "borderColor": self.get_event_color(event, request.user, is_owner),
                "table_number": table_id,
                "table_description": event.table.table_description,
                "total_time": event.total_time
            })

        # Загружаем все столы с ценами
        tables_with_prices = list(Tables.objects.values(
            "id", "number", "table_description", "price_per_hour", "price_per_half_hour"
        ))

        context = {
            "form": form,
            "events": json.dumps(event_list),
            "events_month": events_all,
            "current_bookings": current_bookings,
            "tables": tables_with_prices,
            "is_admin": request.user.is_superuser,
            "user_id": request.user.id if request.user.is_authenticated else None,
            "is_authenticated": request.user.is_authenticated,

            "user_events_count": Event.objects.filter(
                user=request.user).count() if request.user.is_authenticated else 0,
            "max_events": 3,
        }
        return render(request, self.template_name, context)

    # @method_decorator(login_required, name='dispatch') # Раскомментируйте для требования авторизации
    def post(self, request, *args, **kwargs):

        if not request.user.is_authenticated:
            messages.error(request, "Для создания события необходимо войти в систему.")
            return redirect("accounts:signin")
        form = self.form_class(request.POST)
        if form.is_valid():

            if not request.user.is_superuser:
                user_events_count = Event.objects.filter(user=request.user).count()
                if user_events_count >= 3:
                    messages.error(request, "Вы можете иметь не более 3 бронирований одновременно.")
                    return redirect("calendarapp:calendar")


            start_time = parse_datetime(request.POST.get("start_time"))
            end_time = parse_datetime(request.POST.get("end_time"))

            # Проверка продолжительности бронирования
            duration = end_time - start_time
            if not request.user.is_superuser:
                duration = end_time - start_time
                if duration.total_seconds() > 3 * 3600:
                    messages.error(request, "Максимальная продолжительность бронирования - 3 часа.")
                    return redirect("calendarapp:calendar")
            event = form.save(commit=False)


            # Проверка что время не в прошлом
            if start_time < timezone.now():
                messages.error(request, "Нельзя создавать события в прошлом!")
                return redirect("calendarapp:calendar")

            # Проверка что для сегодняшнего дня время не раньше текущего
            if start_time.date() == timezone.now().date() and start_time < timezone.now():
                messages.error(request, "На сегодня можно бронировать только время после текущего момента!")
                return redirect("calendarapp:calendar")
            # Проверка аутентификации пользователя
            if not request.user.is_authenticated:
                messages.error(request, "Для создания события необходимо войти в систему.")
                return redirect("calendarapp:calendar")

            event.user = request.user  # Устанавливаем пользователя

            try:
                table_id = request.POST.get("table")
                table = get_object_or_404(Tables, id=int(table_id)) if table_id else Tables.objects.first()
                start_time = parse_datetime(request.POST.get("start_time"))
                end_time = parse_datetime(request.POST.get("end_time"))
                total_time = float(request.POST.get("total_time", 0))
                total_cost = float(request.POST.get("total_cost", 0))

                if not start_time or not end_time:
                    messages.error(request, "Ошибка: Неверный формат даты или времени.")
                    return redirect("calendarapp:calendar")

            except (ValueError, TypeError) as e:
                logger.error(f"Ошибка парсинга данных: {e}")
                messages.error(request, "Ошибка в данных о времени или стоимости")
                return redirect("calendarapp:calendar")

            # Проверка на пересечение бронирований
            if Event.objects.filter(
                    table=table,
                    start_time__lt=end_time,
                    end_time__gt=start_time
            ).exists():
                messages.error(request, "Выбранный стол уже забронирован на указанное время!")
                return redirect("calendarapp:calendar")

            # Устанавливаем значения и сохраняем
            event.table = table
            event.total_time = total_time
            event.total_cost = total_cost
            event.save()

            return redirect("calendarapp:calendar")

        logger.warning(f"Форма невалидна: {form.errors}")
        messages.error(request, "Ошибка при заполнении формы")
        return render(request, self.template_name, {"form": form})

    def get_available_tables(self, request):
        """AJAX-запрос для получения свободных столов"""
        start_time_str = request.GET.get("start_time")
        end_time_str = request.GET.get("end_time")

        if not start_time_str or not end_time_str:
            return JsonResponse({"error": "Invalid date"}, status=400)

        try:
            start_time = parse_datetime(start_time_str)
            end_time = parse_datetime(end_time_str)
        except (ValueError, TypeError):
            return JsonResponse({"error": "Invalid datetime format"}, status=400)

        # Получаем забронированные столы
        booked_tables = Event.objects.filter(
            start_time__lt=end_time,
            end_time__gt=start_time
        ).exclude(table=None).values_list("table_id", flat=True)

        # Получаем доступные столы с ценами
        available_tables = Tables.objects.exclude(id__in=booked_tables).values(
            "id", "number", "price_per_hour", "price_per_half_hour", 'table_description'
        )

        return JsonResponse({
            "tables": list(available_tables)
        }, safe=False)


    def get_event_color(self, event, user, is_owner):
        """
        Определяет цвет события в зависимости от:
        - Является ли пользователь админом
        - Принадлежит ли событие текущему пользователю
        - Номера стола
        """
        if not user.is_authenticated:
            return TABLE_COLORS['other']

        if is_owner:
            return TABLE_COLORS['user']

        if user.is_superuser:
            table_id = event.table.id if event.table else None
            return TABLE_COLORS.get(table_id, TABLE_COLORS['default'])

        return TABLE_COLORS['other']


def delete_event(request, event_id):
    event = get_object_or_404(Event, id=event_id)
    if request.method == 'POST':
        event.delete()
        return JsonResponse({'message': 'Событие успешно удалено!'})
    else:
        return JsonResponse({'message': 'Ошибка при удалении события!'}, status=400)


def next_week(request, event_id):
    event = get_object_or_404(Event, id=event_id)
    if request.method == 'POST':
        next = event
        next.id = None
        next.start_time += timedelta(days=7)
        next.end_time += timedelta(days=7)
        next.save()
        return JsonResponse({'message': 'Бронь успешно добавлена!'})
    else:
        return JsonResponse({'message': 'Ошибка при добавлении брони!'}, status=400)


def next_day(request, event_id):
    event = get_object_or_404(Event, id=event_id)
    if request.method == 'POST':
        next = event
        next.id = None
        next.start_time += timedelta(days=1)
        next.end_time += timedelta(days=1)
        next.save()
        return JsonResponse({'message': 'Бронь  на следующий день успешно добавлена!'})

    else:
        return JsonResponse({'message': 'Ошибка при добавлении брони!'}, status=400)


def change_event(request, event_id):
    event = get_object_or_404(Event, id=event_id)

    if request.method == 'GET':
        data = {
            'title': event.title,
            'description': event.description,
            'start_time': event.start_time.strftime('%Y-%m-%dT%H:%M:%S'),
            'end_time': event.end_time.strftime('%Y-%m-%dT%H:%M:%S'),
            'table_id': event.table_id,
            'total_cost': event.total_cost,
            'total_time': event.total_time,
        }
        return JsonResponse(data)

    elif request.method == 'POST':
        form = EventForm(request.POST, instance=event)
        if form.is_valid():
            form.save()
            return JsonResponse({'message': 'Бронь успешно изменена!'})
        else:
            # Логируем ошибки формы
            print(form.errors)
            return JsonResponse({'message': 'Ошибка при изменении брони!', 'errors': form.errors}, status=400)

    return JsonResponse({'message': 'Метод не поддерживается!'}, status=405)


from django.utils.dateparse import parse_date


def get_table_statistics(request):
    table_id = request.GET.get('table_id', '')  # Получаем ID стола
    date_str = request.GET.get('date', '')  # Получаем дату

    # Проверяем дату
    date_booking = parse_date(date_str)
    if not date_booking:
        return JsonResponse({'error': 'Некорректная дата'}, status=400)

    start_of_day = datetime.combine(date_booking, time.min)
    end_of_day = datetime.combine(date_booking, time.max)

    # Фильтруем события
    filters = {"start_time__gte": start_of_day, "start_time__lte": end_of_day}

    if table_id:
        filters["table_id"] = table_id  # Добавляем фильтр по столу

    events = Event.objects.filter(**filters)

    if not events.exists():
        return JsonResponse({
            "table_number": table_id if table_id else "",
            "total_events": 0,
            "total_income": 0,
            # "average_booking_time": 0,
            'sum_time': 0

        })
    # Подсчёт статистики
    total_income = sum(event.total_cost for event in events)
    total_events = events.count()
    # avg_time = round(events.aggregate(avg_time=Avg('total_time'))['avg_time'], 2) or 0
    sum_time = sum(event.total_time for event in events) or 0

    return JsonResponse({
        "table_number": table_id if table_id else "всех столов",
        "total_events": total_events,
        "total_income": total_income,
        # "average_booking_time": avg_time,
        "sum_time": sum_time
    })


class UserEventsCountView(generic.View):
    def get(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return JsonResponse({'error': 'Not authenticated'}, status=403)

        return JsonResponse({
            'count': Event.objects.filter(user=request.user).count(),
            'is_admin': request.user.is_superuser,
            'max_events': 3 if not request.user.is_superuser else None
        })

from django.db.models import Count, Sum, Q
class UserStatsView(generic.View):
    template_name = 'calendarapp/user_stats.html'

    def get(self, request, *args, **kwargs):
        if not request.user.is_superuser:
            return JsonResponse({'error': 'Доступ запрещен'}, status=403)

        # Получаем статистику по пользователям
        users_stats = User.objects.filter(
            events__isnull=False
        ).annotate(
            total_events=Count('events'),
            paid_events=Count('events', filter=Q(events__payment_status='paid')),
            total_payments=Sum('events__total_cost', filter=Q(events__payment_status='paid'))
        ).order_by('-total_payments')

        context = {
            'users_stats': users_stats
        }
        return render(request, self.template_name, context)
