# cal/views.py

import json
from django.contrib import messages
from django.utils.dateparse import parse_datetime
from django.shortcuts import render, redirect
from django.http import HttpResponseRedirect
from django.utils.timezone import now
from django.views import generic
from django.utils.safestring import mark_safe
from datetime import timedelta, datetime, date
import calendar
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy, reverse
from django.http import JsonResponse
from django.shortcuts import get_object_or_404

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
    1: "#610928",  # Красный
    2: "#063b14",  # Зеленый
    3: "#092266",  # Синий
    4: "#b8870d",  # Оранжевый
    5: "#4a074a",  # Фиолетовый
}

logger = logging.getLogger(__name__)
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

        # Загружаем события с учетом связей, чтобы избежать лишних запросов
        events_month = Event.objects.filter(
            start_time__month=date.today().month,
            start_time__year=date.today().year
        ).select_related("table")

        # Текущие бронирования
        current_bookings = events_month.filter(start_time__lte=current_time, end_time__gte=current_time)

        # Подготовка списка событий
        event_list = []
        for event in events_month:
            table_id = event.table.id if event.table else None
            color = TABLE_COLORS.get(table_id, "#3498db")
            event_list.append({
                "id": event.id,
                "title": event.title,
                "start": event.start_time.strftime("%Y-%m-%dT%H:%M:%S"),
                "end": event.end_time.strftime("%Y-%m-%dT%H:%M:%S"),
                "description": event.description,
                "color": color,
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
            "events_month": events_month,
            "current_bookings": current_bookings,
            "tables": tables_with_prices,
        }
        return render(request, self.template_name, context)

    def post(self, request, *args, **kwargs):
        form = self.form_class(request.POST)
        if form.is_valid():
            event = form.save(commit=False)
            event.user = request.user

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


# def get_available_tables(self, request):
#     """AJAX-запрос для получения свободных столов"""
#     start_time_str = request.GET.get("start_time")
#     end_time_str = request.GET.get("end_time")
#
#     if not start_time_str or not end_time_str:
#         return JsonResponse({"error": "Invalid date"}, status=400)
#
#     start_time = parse_datetime(start_time_str)
#     end_time = parse_datetime(end_time_str)
#
#     if not start_time or not end_time:
#         return JsonResponse({"error": "Invalid datetime format"}, status=400)
#
#     # Получаем список уже забронированных столов
#     booked_tables = Event.objects.filter(
#         start_time__lt=end_time,
#         end_time__gt=start_time,
#         table__isnull=False  # Убираем пустые столы
#     ).values_list("table_id", flat=True)
#
#     # Фильтруем доступные столы
#     available_tables = Tables.objects.exclude(id__in=booked_tables)
#     tables_data = [{"id": table.id, "name": table.number} for table in available_tables]
#
#     return JsonResponse({"tables": tables_data})


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