from django.shortcuts import redirect
from django.contrib.auth import logout


def signout(request):
    logout(request)
    request.session.flush()

    return redirect("calendarapp:calendar")
