from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404
from yookassa import Payment
import uuid
import logging
from calendarapp.models import Event
from calendarapp.serializers import (
    EventSerializer, PaymentCreateSerializer,
    PaymentStatusSerializer, BookingDetailSerializer
)

logger = logging.getLogger(__name__)


class PaymentCreateAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = PaymentCreateSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        try:
            # Create or get event
            event_id = serializer.validated_data.get('event_id')
            if event_id:
                event = get_object_or_404(Event, id=event_id, user=request.user)
            else:
                event = Event.objects.create(
                    user=request.user,
                    title=serializer.validated_data['title'],
                    description=serializer.validated_data.get('description', ''),
                    start_time=serializer.validated_data['start_time'],
                    end_time=serializer.validated_data['end_time'],
                    table_id=serializer.validated_data['table_id'],
                    total_cost=serializer.validated_data['total_cost'],
                    is_paid=False
                )

            # Create payment
            payment = Payment.create({
                "amount": {
                    "value": str(event.total_cost),
                    "currency": "RUB"
                },
                "confirmation": {
                    "type": "redirect",
                    "return_url": request.build_absolute_uri(f'/api/bookings/{event.id}/payment-callback/')
                },
                "description": f"Booking: {event.title}",
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
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)


class PaymentCallbackAPIView(APIView):
    def get(self, request, booking_id):
        booking = get_object_or_404(Event, id=booking_id)

        if not booking.payment_id:
            return Response({'error': 'Payment ID not found'}, status=status.HTTP_400_BAD_REQUEST)

        payment = Payment.find_one(booking.payment_id)
        booking.payment_status = payment.status
        booking.is_paid = (payment.status == 'succeeded')
        booking.save()

        return Response({
            'status': payment.status,
            'is_paid': booking.is_paid,
            'booking_id': booking.id
        })


class BookingDetailAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, booking_id):
        booking = get_object_or_404(Event, id=booking_id)

        # Check permissions
        if not request.user.is_superuser and booking.user != request.user:
            return Response({'error': 'Permission denied'}, status=status.HTTP_403_FORBIDDEN)

        serializer = BookingDetailSerializer(booking)
        return Response(serializer.data)


class BookingCancelAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, booking_id):
        booking = get_object_or_404(Event, id=booking_id, user=request.user)

        if booking.is_canceled:
            return Response(
                {'error': 'This booking is already canceled'},
                status=status.HTTP_400_BAD_REQUEST
            )

        if booking.is_paid:
            return Response(
                {'error': 'Cannot cancel paid booking'},
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

        serializer = BookingDetailSerializer(bookings, many=True)
        return Response({
            'unpaid': [b for b in serializer.data if not b['is_paid']],
            'paid': [b for b in serializer.data if b['is_paid']],
            'paid_count': len([b for b in serializer.data if b['is_paid']]),
            'max_bookings': 3
        })