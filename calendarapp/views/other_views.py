from django.contrib.auth import get_user_model
from django.db.models import Q, Case, When, Value, BooleanField# cal/views.py

import json
import os
from django.views.decorators.http import require_POST

from django.conf import settings
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
from django.views.generic import ListView ,UpdateView, CreateView, TemplateView

from accounts.models.user import User
from calendarapp.models import EventMember, Event

from calendarapp.models.event import Subscription, Tables
from calendarapp.utils import Calendar
from calendarapp.forms import EventForm, AddMemberForm, TableSettingsForm

from django.views.decorators.csrf import csrf_exempt
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
    if request.method == 'POST':
        form = EventForm(request.POST)
        if form.is_valid():
            event = form.save(commit=False)
            event.user = request.user

            # For admin - save without payment if "Save" button clicked
            if request.user.is_superuser and 'save' in request.POST:
                event.is_paid = True
                event.save()
                messages.success(request, 'Бронь сохранена без оплаты')
                return redirect('calendarapp:calendar')

            # Check booking limit for non-admin users
            if not request.user.is_superuser:
                paid_bookings_count = Event.objects.filter(
                    user=request.user,
                    is_paid=True,
                    is_canceled=False
                ).count()

                if paid_bookings_count >= 3:
                    messages.error(request, "Вы можете иметь не более 3 оплаченных бронирований одновременно.")
                    return redirect("calendarapp:calendar")

            # For all other cases (including admin when clicking "Pay")
            event.is_paid = False
            event.save()

            if request.user.is_superuser:
                # For admin when clicking "Pay" - create payment
                return create_yookassa_payment(request, event)
            else:
                # For regular users - always create payment
                return create_yookassa_payment(request, event)
        else:
            messages.error(request, "Пожалуйста, исправьте ошибки в форме")
    else:
        form = EventForm()

    return render(request, "event.html", {"form": form})


@csrf_exempt
def create_yookassa_payment(request, event=None):
    if request.method == 'POST':
        try:
            # Если событие не передано, создаем новое
            if event is None:
                form = EventForm(request.POST)
                if not form.is_valid():
                    return JsonResponse({'error': 'Неверные данные формы'}, status=400)
                
                # Проверяем, не существует ли уже такое событие
                existing_event = Event.objects.filter(
                    user=request.user,
                    title=form.cleaned_data['title'],
                    start_time=form.cleaned_data['start_time'],
                    end_time=form.cleaned_data['end_time'],
                    table=form.cleaned_data['table']
                ).first()

                if existing_event:
                    if existing_event.payment_id:
                        # Если событие уже существует и имеет платеж
                        payment = Payment.find_one(existing_event.payment_id)
                        if payment.status == 'pending':
                            return JsonResponse({
                                'payment_id': existing_event.payment_id,
                                'confirmation_url': payment.confirmation.confirmation_url
                            })
                    
                    # Обновляем существующее событие вместо создания нового
                    event = existing_event
                else:
                    # Создаем новое событие только если дубликата нет
                    event = form.save(commit=False)
                    event.user = request.user
                    event.is_paid = False
                    event.save()
            else:
                # Для существующего события проверяем дубликаты
                duplicate = Event.objects.filter(
                    user=request.user,
                    title=event.title,
                    start_time=event.start_time,
                    end_time=event.end_time,
                    table=event.table
                ).exclude(id=event.id).first()

                if duplicate:
                    return JsonResponse({
                        'error': 'Такое бронирование уже существует'
                    }, status=400)

            # Проверка на пересечение времени бронирования
            conflicting_events = Event.objects.filter(
                table=event.table,
                start_time__lt=event.end_time,
                end_time__gt=event.start_time
            ).exclude(id=event.id if event.id else None)

            if conflicting_events.exists():
                return JsonResponse({
                    'error': 'Стол уже забронирован на это время'
                }, status=400)

            # Если у события уже есть платеж, проверяем его статус
            if event.payment_id:
                payment = Payment.find_one(event.payment_id)
                if payment.status == 'pending':
                    return JsonResponse({
                        'payment_id': event.payment_id,
                        'confirmation_url': payment.confirmation.confirmation_url
                    })

            # Создаем новый платеж
            return_url = request.build_absolute_uri(
                reverse('calendarapp:payment_callback', args=[event.id])
            )

            payment = Payment.create({
                "amount": {
                    "value": f"{event.total_cost:.2f}",
                    "currency": "RUB"
                },
                "confirmation": {
                    "type": "redirect",
                    "return_url": return_url
                },
                "capture": True,
                "description": f"Бронирование стола: {event.title}",
                "metadata": {
                    "event_id": str(event.id),
                    "user_id": str(request.user.id)
                }
            }, idempotency_key=str(uuid.uuid4()))

            # Сохраняем ID платежа
            event.payment_id = payment.id
            event.save()

            return JsonResponse({
                'payment_id': payment.id,
                'confirmation_url': payment.confirmation.confirmation_url
            })

        except Exception as e:
            logger.error(f"Ошибка создания платежа: {str(e)}", exc_info=True)
            return JsonResponse({
                'error': 'Ошибка при создании платежа'
            }, status=500)

    return JsonResponse({
        'error': 'Неподдерживаемый метод запроса'
    }, status=405)


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


@login_required
@require_POST
def cancel_booking(request):
    booking_id = request.POST.get('booking_id')
    try:
        booking = Event.objects.get(id=booking_id, user=request.user)
        
        # Мягкое удаление - помечаем как отмененное
        booking.is_canceled = True
        booking.save()
        
        return JsonResponse({'success': True, 'message': 'Бронирование отменено'})
        
    except Event.DoesNotExist:
        return JsonResponse({
            'success': False,
            'message': 'Бронирование не найдено'
        }, status=404)


@login_required
@require_POST
def delete_event(request, event_id):
    try:
        event = Event.objects.get(id=event_id)
        
        # Проверка прав - только админ или владелец события
        if not request.user.is_superuser and event.user != request.user:
            return JsonResponse({
                'success': False,
                'message': 'Недостаточно прав для удаления'
            }, status=403)
            
        # Полное удаление события
        event.delete()
        
        return JsonResponse({
            'success': True,
            'message': 'Событие полностью удалено'
        })
        
    except Event.DoesNotExist:
        return JsonResponse({
            'success': False,
            'message': 'Событие не найдено'
        }, status=404)

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

        paid_count = Event.objects.filter(
            user=request.user,
            is_paid=True,
            is_canceled=False
        ).count()

        return JsonResponse({
            'count': paid_count,
            'is_admin': request.user.is_superuser,
            'max_events': 3 if not request.user.is_superuser else None
        })


from django.views import generic
from django.db.models import Count, Sum, Q, F, FilteredRelation
User = get_user_model()

class UserStatsView(generic.TemplateView):
    template_name = "calendarapp/user_stats.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Получаем всех пользователей с аннотированной статистикой
        users = User.objects.annotate(
            total_events=Count('events', filter=Q(events__is_canceled=False)),
            paid_events=Count('events', filter=Q(events__is_canceled=False, events__is_paid=True)),
            total_payments=Sum('events__total_cost', filter=Q(events__is_canceled=False, events__is_paid=True)),
            unpaid_events=Count('events', filter=Q(events__is_canceled=False, events__is_paid=False))
        ).filter(
            events__isnull=False  # Только пользователи с бронированиями
        ).distinct()

        context['users_stats'] = users
        return context
        


import uuid
import yookassa
from yookassa import Configuration, Payment
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt

# Настройте ЮКассу (лучше вынести в settings.py)
Configuration.account_id = settings.ACCOUNT_ID
Configuration.secret_key = settings.SHOP_SECRET_KEY


@csrf_exempt
def check_payment_status(request, payment_id):
    if request.method == 'GET':
        payment = Payment.find_one(payment_id)
        return JsonResponse({'status': payment.status})
    return JsonResponse({'error': 'Invalid request'}, status=400)


# views.py
@csrf_exempt
def payment_callback(request, booking_id):
    booking = get_object_or_404(Event, id=booking_id)

    try:
        if not booking.payment_id:
            raise ValueError("Payment ID not found")

        payment = Payment.find_one(booking.payment_id)

        if payment.status == 'succeeded':
            booking.is_paid = True
            booking.payment_status = 'succeeded'
            booking.save()
            messages.success(request, 'Бронирование успешно оплачено!')
        else:
            booking.payment_status = payment.status
            booking.save()
            messages.warning(request, f'Платеж имеет статус: {payment.status}')

    except Exception as e:
        logger.error(f"Payment callback error: {str(e)}")
        messages.error(request, 'Ошибка обработки платежа')

    return redirect('calendarapp:my_bookings')


from django.utils import timezone
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import ListView
from calendarapp.models import Event


class MyBookingsView(LoginRequiredMixin, ListView):
    template_name = 'calendarapp/my_bookings.html'
    context_object_name = 'bookings'
    paginate_by = 10

    def get_queryset(self):
        now = timezone.now()
        queryset = Event.objects.filter(
            user=self.request.user
        ).annotate(
            is_past=Case(
                When(end_time__lt=now, then=Value(True)),
                default=Value(False),
                output_field=BooleanField()
            ),
            is_current=Case(
                When(
                    Q(start_time__lte=now) & Q(end_time__gte=now),
                    then=Value(True)
                ),
                default=Value(False),
                output_field=BooleanField()
            ),
            is_future=Case(
                When(start_time__gt=now, then=Value(True)),
                default=Value(False),
                output_field=BooleanField()
            ),
            is_overdue=Case(
                When(
                    Q(end_time__lt=now) & Q(is_paid=False) & Q(is_canceled=False),
                    then=Value(True)
                ),
                default=Value(False),
                output_field=BooleanField()
            ),
            user_name=F('user__email')  # Добавляем аннотацию для имени пользователя
        ).select_related('table', 'user').order_by('-start_time')
        
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        now = timezone.now()
        
        # Получаем полный queryset (без пагинации)
        full_queryset = self.get_queryset()
        
        # Разделение бронирований по статусам
        context['past_bookings'] = full_queryset.filter(end_time__lt=now)
        context['current_bookings'] = full_queryset.filter(
            start_time__lte=now, 
            end_time__gte=now
        )
        context['future_bookings'] = full_queryset.filter(start_time__gt=now)
        context['overdue_bookings'] = full_queryset.filter(
            end_time__lt=now, 
            is_paid=False,
            is_canceled=False
        )
        
        # Статистика
        context['paid_count'] = full_queryset.filter(is_paid=True).count()
        context['unpaid_count'] = full_queryset.filter(is_paid=False).count()
        context['canceled_count'] = full_queryset.filter(is_canceled=True).count()
        context['overdue_count'] = context['overdue_bookings'].count()
        context['max_bookings'] = 3
        
        return context

@csrf_exempt
def pay_booking(request, booking_id):
    # Проверка аутентификации
    if not request.user.is_authenticated:
        return redirect('login')
    
    booking = get_object_or_404(Event, id=booking_id, user=request.user)

    if booking.is_paid:
        messages.warning(request, 'Это бронирование уже оплачено')
        return redirect('calendarapp:my_bookings')

    return_url = request.build_absolute_uri(
        reverse('calendarapp:payment_callback', args=[booking.id])
    )

    try:
        # Создаем платеж
        payment = Payment.create({
            "amount": {
                "value": f"{booking.total_cost:.2f}",
                "currency": "RUB"
            },
            "confirmation": {
                "type": "redirect",
                "return_url": return_url
            },
            "capture": True,
            "description": f"Оплата брони: {booking.title}",
            "metadata": {
                "booking_id": str(booking.id),
                "user_id": str(request.user.id)
            }
        }, idempotency_key=str(uuid.uuid4()))

        booking.payment_id = payment.id
        booking.save()

        # Редирект на страницу оплаты ЮКассы
        return redirect(payment.confirmation.confirmation_url)

    except Exception as e:
        logger.error(f"Payment error: {str(e)}", exc_info=True)
        messages.error(request, 'Ошибка при создании платежа. Попробуйте позже.')
        return redirect('calendarapp:event_detail', booking_id=booking.id)
   


# calendarapp/views.py
from django.views.decorators.csrf import csrf_exempt
from django.http import HttpResponse


import hmac
import hashlib
import json

@csrf_exempt
def yookassa_webhook(request):
    """Обработчик webhook уведомлений от ЮKassa"""
    if request.method != 'POST':
        return HttpResponse(status=405)
    
    try:
        # Получаем подпись из заголовков
        signature = request.headers.get('Content-Signature', '')
        if not signature:
            logger.warning("Missing Content-Signature header")
            return HttpResponse(status=400)

        # Проверяем подпись с использованием секретного ключа API
        secret_key = settings.YOOKASSA_SECRET_KEY.encode('utf-8')
        digest = hmac.new(secret_key, request.body, hashlib.sha256).hexdigest()
        expected_signature = f"sha256={digest}"
        
        if not hmac.compare_digest(expected_signature, signature):
            logger.warning(f"Invalid webhook signature. Expected: {expected_signature}, got: {signature}")
            return HttpResponse(status=403)

        event_json = json.loads(request.body)
        payment_id = event_json.get('object', {}).get('id')
        
        if not payment_id:
            logger.warning("Missing payment ID in webhook")
            return HttpResponse(status=400)

        # Обрабатываем только нужные типы событий
        event_type = event_json.get('event')
        if event_type not in ['payment.succeeded', 'payment.waiting_for_capture', 'payment.canceled']:
            return HttpResponse(status=200)

        # Находим бронирование
        booking = Event.objects.filter(payment_id=payment_id).first()
        if not booking:
            logger.warning(f"Booking not found for payment {payment_id}")
            return HttpResponse(status=404)

        # Получаем актуальный статус платежа из API
        payment = Payment.find_one(payment_id)
        booking.payment_status = payment.status
        booking.is_paid = (payment.status == 'succeeded')
        booking.save()

        if payment.status == 'succeeded':
            logger.info(f"Payment succeeded for booking {booking.id}")
            # Дополнительные действия при успешной оплате
            #send_payment_success_email(booking)
        else:
            logger.info(f"Payment status changed to {payment.status} for booking {booking.id}")

        return HttpResponse(status=200)

    except json.JSONDecodeError:
        logger.error("Invalid JSON in webhook")
        return HttpResponse(status=400)
    except Exception as e:
        logger.error(f"Webhook processing error: {str(e)}", exc_info=True)
        return JsonResponse({'error': 'Internal server error'}, status=500)
   

# calendarapp/views.py
from django.http import JsonResponse
from django.views.decorators.http import require_POST
# calendarapp/views.py
from django.views.decorators.http import require_POST
from django.contrib.auth.decorators import login_required


@login_required
@require_POST
def cancel_booking(request):
    booking_id = request.POST.get('booking_id')
    try:
        booking = Event.objects.get(id=booking_id, user=request.user)

        if booking.is_canceled:
            return JsonResponse({
                'success': False,
                'message': 'Это бронирование уже отменено'
            }, status=400)

        if booking.is_paid:
            return JsonResponse({
                'success': False,
                'message': 'Нельзя отменить оплаченное бронирование'
            }, status=400)

        booking.is_canceled = True
        booking.save()

        return JsonResponse({'success': True})

    except Event.DoesNotExist:
        return JsonResponse({
            'success': False,
            'message': 'Бронирование не найдено'
        }, status=404)


from django.http import JsonResponse
from django.views.decorators.http import require_GET
from django.core.serializers.json import DjangoJSONEncoder
@require_GET
def booking_details_api(request, booking_id):
    try:
        booking = Event.objects.select_related('table', 'user').get(id=booking_id)

        # Проверка прав доступа
        if not request.user.is_superuser and booking.user != request.user:
            return JsonResponse({'error': 'Доступ запрещен'}, status=403)

        data = {
            'id': booking.id,
            'title': booking.title,
            'description': booking.description,
            'start_time': booking.start_time.strftime("%d.%m.%Y %H:%M"),
            'end_time': booking.end_time.strftime("%H:%M"),
            'table': {
                'number': booking.table.number,
                'table_description': booking.table.table_description,
            },
            'total_cost': booking.total_cost,
            'is_paid': booking.is_paid,
            'is_canceled': booking.is_canceled,
            'user': {
                'email': booking.user.email,
            }
        }

        return JsonResponse(data, encoder=DjangoJSONEncoder)

    except Event.DoesNotExist:
        return JsonResponse({'error': 'Бронирование не найдено'}, status=404)

from django.contrib.auth.mixins import UserPassesTestMixin
from django.views.generic import View
from django.shortcuts import render, redirect
from django.contrib import messages
from django.urls import reverse_lazy

class TableSettingsListView(LoginRequiredMixin, UserPassesTestMixin, ListView):
    """Список всех столов для настройки"""
    model = Tables
    template_name = 'calendarapp/settings_table.html'
    context_object_name = 'tables'
    login_url = reverse_lazy('admin:login')
    
    def test_func(self):
        return self.request.user.is_superuser
from django.shortcuts import get_object_or_404, redirect, render
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.views.generic import UpdateView
from django.urls import reverse_lazy
from django.contrib import messages

import logging

logger = logging.getLogger(__name__)


class TableSettingsUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    """Редактирование настроек конкретного стола"""
    model = Tables
    form_class = TableSettingsForm
    template_name = 'calendarapp/table_settings_form.html'
    success_url = reverse_lazy('calendarapp:table_settings_list')
    login_url = reverse_lazy('admin:login')

    def test_func(self):
        return self.request.user.is_superuser

    def get_object(self):
        """Получаем объект для редактирования, используя pk из URL"""
        table_id = self.kwargs.get('pk')  # Получаем pk из URL
        return get_object_or_404(Tables, pk=table_id)  # Получаем объект по pk

    def form_valid(self, form):
        messages.success(self.request, f'Настройки стола №{form.instance.number} успешно обновлены!')
        return super().form_valid(form)

    def form_invalid(self, form):
        messages.error(self.request, 'Ошибка при сохранении настроек')
        return super().form_invalid(form)

class TableCreateView(LoginRequiredMixin, UserPassesTestMixin, CreateView):
    """Создание нового стола"""
    model = Tables
    form_class = TableSettingsForm
    template_name = 'calendarapp/table_settings_form.html'
    success_url = reverse_lazy('calendarapp:table_settings_list')
    login_url = reverse_lazy('admin:login')
    
    def test_func(self):
        return self.request.user.is_superuser
    
    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, f'Стол №{form.instance.number} успешно создан!')
        return response
    

class SettingsListView(LoginRequiredMixin, UserPassesTestMixin, TemplateView):
    template_name = 'calendarapp/settings_list.html'
    login_url = reverse_lazy('admin:login')
    
    def test_func(self):
        return self.request.user.is_superuser
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Все столы с ценами
        context['tables'] = Tables.objects.all().order_by('number')
        
        # Все абонементы
        context['subscriptions'] = Subscription.objects.all().order_by('name')
        
        # Другие настройки (пример)
        context['site_settings'] = {
            'site_name': 'Мой Бизнес',
            'business_hours': '09:00 - 22:00',
            # Добавьте другие настройки по необходимости
        }
        
        return context

# views.py
class SubscriptionCreateView(LoginRequiredMixin, UserPassesTestMixin, CreateView):
    model = Subscription
    fields = ['name', 'description', 'price', 'duration', 'is_active', 'number_of_events']
    template_name = 'calendarapp/subscription_form.html'
    success_url = reverse_lazy('calendarapp:all_settings')
    login_url = reverse_lazy('admin:login')
    
    def test_func(self):
        return self.request.user.is_superuser
    
    def form_valid(self, form):
        messages.success(self.request, 'Абонемент успешно создан!')
        return super().form_valid(form)

class SubscriptionUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = Subscription
    fields = ['name', 'description', 'price', 'duration', 'is_active', 'number_of_events']
    template_name = 'calendarapp/subscription_form.html'
    success_url = reverse_lazy('calendarapp:all_settings')
    login_url = reverse_lazy('admin:login')
    
    def test_func(self):
        return self.request.user.is_superuser
    
    def form_valid(self, form):
        messages.success(self.request, 'Абонемент успешно обновлен!')
        return super().form_valid(form)
    

# views.py
from django.views.generic import DeleteView

class TableDeleteView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    model = Tables
    success_url = reverse_lazy('calendarapp:all_settings')
    template_name = 'calendarapp/confirm_delete.html'
    
    def test_func(self):
        return self.request.user.is_superuser
class SubscriptionDeleteView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    model = Subscription
    success_url = reverse_lazy('calendarapp:all_settings')
    template_name = 'calendarapp/confirm_delete.html'
    
    def test_func(self):
        return self.request.user.is_superuser