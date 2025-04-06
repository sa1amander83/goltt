import json

from django.views.generic import View
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import render

from calendarapp.models import Event


class DashboardView( View):

    template_name = "calendarapp/dashboard.html"

    def get(self, request, *args, **kwargs):
        events = Event.objects.get_all_events(user=request.user)
        running_events = Event.objects.get_running_events(user=request.user)
        latest_events = Event.objects.filter(user=request.user).order_by("-id")[:10]
        completed_events = Event.objects.get_completed_events(user=request.user)
        upcoming_events = Event.objects.get_upcoming_events(user=request.user)
        context = {
            "total_event": events.count(),
            "running_events": running_events,
            "latest_events": latest_events,
            "completed_events": completed_events.count(),
            "upcoming_events": upcoming_events
        }
        return render(request, self.template_name, context)


import uuid

from yookassa import Configuration, Payment
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt

# Настройте ЮКассу (лучше вынести в settings.py)
Configuration.account_id = 'your_shop_id'
Configuration.secret_key = 'your_secret_key'


@csrf_exempt
def create_yookassa_payment(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            amount = float(data['amount'])
            booking_data = data['booking_data']

            # Создаем платеж в ЮКассе
            idempotence_key = str(uuid.uuid4())
            payment = Payment.create({
                "amount": {
                    "value": str(amount),
                    "currency": "RUB"
                },
                "confirmation": {
                    "type": "redirect",
                    "return_url": "http://your-site.com/booking/success/"  # URL после успешной оплаты
                },
                "capture": True,
                "description": f"Бронирование стола: {booking_data['title']}",
                "metadata": {
                    "booking_data": booking_data
                }
            }, idempotence_key)

            return JsonResponse({
                'id': payment.id,
                'status': payment.status,
                'confirmation_url': payment.confirmation.confirmation_url
            })

        except Exception as e:
            return JsonResponse({'error': str(e)}, status=400)

    return JsonResponse({'error': 'Invalid request'}, status=400)