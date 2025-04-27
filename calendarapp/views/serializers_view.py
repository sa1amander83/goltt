from decimal import Decimal

from django.db.models import Sum, Count
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.utils.dateparse import parse_datetime
from django.utils.timezone import now
from rest_framework import serializers
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from rest_framework.response import Response
from rest_framework.views import APIView
from calendarapp.models import Event, EventMember
from calendarapp.models.event import Tables
from calendarapp.utils import Calendar
from calendarapp.views.other_views import get_date
from calendarapp.models.serializers import TablesSerializer, AdminStatsSerializer, EventListSerializer, \
    UserStatsSerializer


class EventSerializer(serializers.ModelSerializer):
    class Meta:
        model = Event
        fields = ['id', 'title', 'start_time', 'end_time', 'description', 'table']

class CalendarView(APIView):
    def get(self, request, *args, **kwargs):
        d = get_date(self.request.GET.get("month", None))
        cal = Calendar(d.year, d.month)
        events = Event.objects.filter(start_time__month=d.month, start_time__year=d.year)

        serializer = EventSerializer(events, many=True)
        return Response({"calendar": cal.formatmonth(withyear=True), "events": serializer.data})

class EventCreateAPIView(APIView):
    def post(self, request, *args, **kwargs):
        serializer = EventSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(user=request.user)
            return Response(serializer.data, status=201)
        return Response(serializer.errors, status=400)


class EventDetailAPIView(APIView):
    def get(self, request, event_id, *args, **kwargs):
        event = get_object_or_404(Event, id=event_id)
        serializer = EventSerializer(event)
        return Response(serializer.data)


class EventUpdateAPIView(APIView):
    def post(self, request, event_id, *args, **kwargs):
        event = get_object_or_404(Event, id=event_id)
        serializer = EventSerializer(event, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=400)
class EventDeleteAPIView(APIView):
    def post(self, request, event_id, *args, **kwargs):
        event = get_object_or_404(Event, id=event_id)
        event.delete()
        return Response({"message": "Event deleted successfully"})


class AvailableTablesAPIView(APIView):
    def get(self, request, *args, **kwargs):
        start_time = parse_datetime(request.GET.get('start_time'))
        end_time = parse_datetime(request.GET.get('end_time'))

        booked_tables = Event.objects.filter(
            start_time__lt=end_time,
            end_time__gt=start_time
        ).exclude(table=None).values_list('table_id', flat=True)

        available_tables = Tables.objects.exclude(id__in=booked_tables)
        serializer = TablesSerializer(available_tables, many=True)
        return Response({"tables": serializer.data})


class EventMemberCreateAPIView(APIView):
    def post(self, request, event_id, *args, **kwargs):
        event = get_object_or_404(Event, id=event_id)
        user = request.data.get('user')
        # Логика добавления пользователя в EventMember
        event_member = EventMember.objects.create(event=event, user=user)
        return Response({"message": "Member added successfully"}, status=201)


class AdminStatsAPIView(APIView):
    permission_classes = [IsAuthenticated, IsAdminUser]

    def get(self, request):
        today = now().date()
        current_month = int(request.GET.get('month', today.month))
        current_year = int(request.GET.get('year', today.year))

        # Get available months and years
        months = list(range(1, 13))
        years = list(range(today.year - 1, today.year + 1))

        tables = Tables.objects.all()
        table_stats = []

        total_daily_income = Decimal(0)
        total_monthly_income = Decimal(0)
        total_past_month_income = Decimal(0)

        for table in tables:
            # Daily stats
            daily_bookings = Event.objects.filter(
                table=table,
                start_time__date=today
            )
            daily_income = daily_bookings.aggregate(
                total=Sum('total_cost')
            )['total'] or Decimal(0)
            daily_booking_count = daily_bookings.count()

            # Monthly stats
            monthly_bookings = Event.objects.filter(
                table=table,
                start_time__month=current_month,
                start_time__year=current_year
            )
            monthly_income = monthly_bookings.aggregate(
                total=Sum('total_cost')
            )['total'] or Decimal(0)
            monthly_booking_count = monthly_bookings.count()

            # Past month stats (completed events only)
            past_month = current_month - 1 if current_month > 1 else 12
            past_year = current_year if current_month > 1 else current_year - 1

            past_month_bookings = Event.objects.filter(
                table=table,
                start_time__month=past_month,
                start_time__year=past_year,
                end_time__lt=now()
            )
            past_month_income = past_month_bookings.aggregate(
                total=Sum('total_cost')
            )['total'] or Decimal(0)

            # Update totals
            total_daily_income += daily_income
            total_monthly_income += monthly_income
            total_past_month_income += past_month_income

            table_stats.append({
                "table_number": table.id,
                "daily_income": daily_income,
                "monthly_income": monthly_income,
                "past_month_income": past_month_income,
                "total_bookings_today": daily_booking_count,
                "total_bookings_month": monthly_booking_count,
            })

        # Prepare response data
        data = {
            "table_stats": table_stats,
            "total_daily_income": total_daily_income,
            "total_monthly_income": total_monthly_income,
            "total_past_month_income": total_past_month_income,
            "months": months,
            "years": years,
            "current_month": current_month,
            "current_year": current_year,
        }

        serializer = AdminStatsSerializer(data=data)
        serializer.is_valid(raise_exception=True)

        return Response(serializer.data)


class EventListAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Event.objects.filter(
            user=self.request.user,
            is_active=True,
            is_deleted=False
        ).select_related('table', 'user')

    def get(self, request):
        serializer = EventListSerializer(self.get_queryset(), many=True)
        return Response({
            'events': serializer.data,
            'status_choices': dict(Event.PAYMENT_STATUS_CHOICES)
        })


class RunningEventsAPIView(EventListAPIView):
    def get_queryset(self):
        return Event.objects.get_running_events(user=self.request.user)

    def get(self, request):
        serializer = EventListSerializer(self.get_queryset(), many=True)
        return Response({
            'events': serializer.data,
            'status_choices': dict(Event.PAYMENT_STATUS_CHOICES),
            'current_status': 'running'
        })


class UpcomingEventsAPIView(EventListAPIView):
    def get_queryset(self):
        return Event.objects.get_upcoming_events(user=self.request.user)

    def get(self, request):
        serializer = EventListSerializer(self.get_queryset(), many=True)
        return Response({
            'events': serializer.data,
            'status_choices': dict(Event.PAYMENT_STATUS_CHOICES),
            'current_status': 'upcoming'
        })


class CompletedEventsAPIView(EventListAPIView):
    def get_queryset(self):
        return Event.objects.get_completed_events(user=self.request.user)

    def get(self, request):
        serializer = EventListSerializer(self.get_queryset(), many=True)
        return Response({
            'events': serializer.data,
            'status_choices': dict(Event.PAYMENT_STATUS_CHOICES),
            'current_status': 'completed'
        })





class UserBookingStatsAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        now = timezone.now()

        # Основная статистика
        stats = Event.objects.filter(user=user).aggregate(
            total_bookings=Count('id'),
            total_spent=Sum('total_cost')
        )

        # Предстоящие бронирования
        upcoming_bookings = Event.objects.filter(
            user=user,
            start_time__gt=now,
            is_canceled=False
        ).select_related('table').order_by('start_time')

        # Прошедшие бронирования
        past_bookings = Event.objects.filter(
            user=user,
            start_time__lte=now,
            is_canceled=False
        ).select_related('table').order_by('-start_time')

        # Самый популярный стол
        favorite_table = Event.objects.filter(
            user=user
        ).values('table').annotate(
            count=Count('id')
        ).order_by('-count').first()

        if favorite_table:
            favorite_table = Tables.objects.get(id=favorite_table['table'])
        else:
            favorite_table = None

        # Подготовка данных
        data = {
            'total_bookings': stats['total_bookings'] or 0,
            'total_spent': stats['total_spent'] or 0,
            'upcoming_bookings': upcoming_bookings,
            'past_bookings': past_bookings,
            'favorite_table': favorite_table
        }

        serializer = UserStatsSerializer(data)
        return Response(serializer.data)