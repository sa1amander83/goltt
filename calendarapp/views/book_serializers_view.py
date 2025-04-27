from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404
from yookassa import Payment
import uuid
import logging
from calendarapp.models import Event

from accounts.models import User
from calendarapp.models.event import UserEventStats
from calendarapp.models.serializers import PaymentCreateSerializer, PaymentStatusSerializer, EventSerializer, \
    UserEventStatsSerializer

logger = logging.getLogger(__name__)


class PaymentCreateAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = PaymentCreateSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        try:
            # Calculate total cost based on table price and duration
            table = serializer.validated_data['table_id']
            start_time = serializer.validated_data['start_time']
            end_time = serializer.validated_data['end_time']
            duration_hours = (end_time - start_time).total_seconds() / 3600

            # Simple pricing calculation (you can adjust this logic)
            if duration_hours <= 0.5:
                total_cost = table.price_per_half_hour
            else:
                total_cost = table.price_per_hour * duration_hours

            # Create or update event
            event_id = serializer.validated_data.get('event_id')
            if event_id:
                event = get_object_or_404(Event, id=event_id, user=request.user)
                event.title = serializer.validated_data['title']
                event.description = serializer.validated_data.get('description', '')
                event.start_time = start_time
                event.end_time = end_time
                event.table = table
                event.total_cost = total_cost
                event.is_paid = False
            else:
                event = Event.objects.create(
                    user=request.user,
                    title=serializer.validated_data['title'],
                    description=serializer.validated_data.get('description', ''),
                    start_time=start_time,
                    end_time=end_time,
                    table=table,
                    total_cost=total_cost,
                    is_paid=False
                )

            # Create YooKassa payment
            payment = Payment.create({
                "amount": {
                    "value": f"{total_cost:.2f}",
                    "currency": "RUB"
                },
                "confirmation": {
                    "type": "redirect",
                    "return_url": request.build_absolute_uri(
                        f'/api/bookings/{event.id}/payment-callback/'
                    )
                },
                "description": f"Бронирование: {event.title}",
                "metadata": {
                    "event_id": str(event.id)
                }
            }, str(uuid.uuid4()))

            event.payment_id = payment.id
            event.save()

            response_serializer = PaymentStatusSerializer({
                'status': 'pending',
                'payment_id': payment.id,
                'confirmation_url': payment.confirmation.confirmation_url
            })
            return Response(response_serializer.data)

        except Exception as e:
            logger.error(f"Payment error: {str(e)}")
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )


class PaymentCallbackAPIView(APIView):
    def get(self, request, booking_id):
        booking = get_object_or_404(Event, id=booking_id)

        if not booking.payment_id:
            return Response(
                {'error': 'Payment ID not found'},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            payment = Payment.find_one(booking.payment_id)
            booking.payment_status = payment.status
            booking.is_paid = (payment.status == 'succeeded')
            booking.save()

            return Response({
                'status': payment.status,
                'is_paid': booking.is_paid,
                'booking_id': booking.id
            })
        except Exception as e:
            logger.error(f"Payment callback error: {str(e)}")
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )


class BookingDetailAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, booking_id):
        booking = get_object_or_404(Event, id=booking_id)

        # Check permissions
        if not request.user.is_superuser and booking.user != request.user:
            return Response(
                {'error': 'Permission denied'},
                status=status.HTTP_403_FORBIDDEN
            )

        serializer = EventSerializer(booking)
        return Response(serializer.data)


class BookingCancelAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, booking_id):
        booking = get_object_or_404(Event, id=booking_id, user=request.user)

        if booking.is_canceled:
            return Response(
                {'error': 'Это бронирование уже отменено'},
                status=status.HTTP_400_BAD_REQUEST
            )

        if booking.is_paid:
            return Response(
                {'error': 'Нельзя отменить оплаченное бронирование'},
                status=status.HTTP_400_BAD_REQUEST
            )

        booking.is_canceled = True
        booking.save()

        return Response({'status': 'canceled'})


class MyBookingsAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        bookings = Event.objects.filter(
            user=request.user,
            is_canceled=False
        ).select_related('table').order_by('-start_time')

        serializer = EventSerializer(bookings, many=True)

        return Response({
            'unpaid': [b for b in serializer.data if not b['is_paid']],
            'paid': [b for b in serializer.data if b['is_paid']],
            'paid_count': len([b for b in serializer.data if b['is_paid']]),
            'max_bookings': 3
        })


class UserStatsAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        stats = UserEventStats.objects.filter(
            user=request.user
        ).select_related('table')

        serializer = UserEventStatsSerializer(stats, many=True)
        return Response(serializer.data)