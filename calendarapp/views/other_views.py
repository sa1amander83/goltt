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
        total_time= form.cleaned_data["total_time"]

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

from django.views import generic
from django.contrib.auth.mixins import LoginRequiredMixin
TABLE_COLORS = {
    1: "#610928",  # Красный
    2: "#063b14",  # Зеленый
    3: "#092266",  # Синий
    4: "#b8870d",  # Оранжевый
    5: "#4a074a",  # Фиолетовый
}
class CalendarViewNew(LoginRequiredMixin, generic.View):
    login_url = "accounts:signin"
    template_name = "calendarapp/calendar.html"
    form_class = EventForm

    def get(self, request, *args, **kwargs):
        forms = self.form_class()
        current_time = now()
        current_bookings = Event.objects.filter(start_time__lte=current_time, end_time__gte=current_time)
        today_start = datetime.combine(datetime.today(), datetime.min.time())
        today_end = today_start + timedelta(days=1)

        # Фильтруем события за сегодняшний день
        events = Event.objects.filter(start_time__gte=today_start, start_time__lt=today_end)
        # Получаем все события за месяц (для всех пользователей)
        events_month = Event.objects.filter(start_time__month=date.today().month, start_time__year=date.today().year)

        # events = Event.objects.get_all_events(user=request.user)
        # events_month = Event.objects.get_running_events()
        # events_month = Event.objects.get_running_events(user=request.user)
        event_list = []

        all_tables = Tables.objects.all()
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
                "total_time": event.total_time
            })

        # События для текущего дня (если нужны отдельные события для сегодняшнего дня)
        for event in events:
            table_id = event.table.id if event.table else None
            color = TABLE_COLORS.get(table_id, "#0d377a")
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
        context = {
            "form": forms,
            "events": json.dumps(event_list),
            "events_month": events_month,
            "current_bookings": current_bookings,
            "tables": all_tables  # Изначально показываем все столы
        }
        return render(request, self.template_name, context)

    def post(self, request, *args, **kwargs):
        forms = self.form_class(request.POST)
        if forms.is_valid():
            form = forms.save(commit=False)
            form.user = request.user
            table_id = request.POST.get("table")
            start_time = parse_datetime(request.POST.get("start_time"))
            end_time = parse_datetime(request.POST.get("end_time"))

            if not table_id:
                form.table = Tables.objects.get(id=1)
            else:
                form.table = Tables.objects.get(id=int(table_id))
            print(request.POST)
            # Проверяем пересечение бронирований
            overlapping_reservations = Event.objects.filter(
                table=form.table,
                start_time__lt=end_time,
                end_time__gt=start_time
            )

            if overlapping_reservations.exists():
                messages.error(request, "Выбранный стол уже забронирован на указанное время!")
                return redirect("calendarapp:calendar")

            form.total_time = request.POST.get("total_time")
            form.total_cost = request.POST.get("total_cost")

            form.save()


            return redirect("calendarapp:calendar")
        print("Form is not valid:", forms.errors)  # 🔹 Если форма не проходит
        context = {"form": forms}
        return render(request, self.template_name, context)

    def get_available_tables(self, request):
        """AJAX-запрос для получения свободных столов"""
        start_time_str = request.GET.get("start_time")
        end_time_str = request.GET.get("end_time")

        if not start_time_str or not end_time_str:
            return JsonResponse({"error": "Invalid date"}, status=400)

        start_time = parse_datetime(start_time_str)
        end_time = parse_datetime(end_time_str)

        if not start_time or not end_time:
            return JsonResponse({"error": "Invalid datetime format"}, status=400)

        # Получаем список уже забронированных столов
        booked_tables = Event.objects.filter(
            start_time__lt=end_time,
            end_time__gt=start_time,
            table__isnull=False  # Убираем пустые столы
        ).values_list("table_id", flat=True)

        # Фильтруем доступные столы
        available_tables = Tables.objects.exclude(id__in=booked_tables)
        tables_data = [{"id": table.id, "name": table.number} for table in available_tables]

        return JsonResponse({"tables": tables_data})




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
