from django.urls import path

from . import views
from .views.event_list import AdminStatsView

app_name = "calendarapp"

urlpatterns = [
    path("", views.CalendarViewNew.as_view(), name="calendar"),
    # path("calenders/", views.CalendarView.as_view(), name="calendars"),
    path("calenders/", views.CalendarView.as_view(), name="calendars"),
    path('delete_event/<int:event_id>/', views.delete_event, name='delete_event'),
    path('next_week/<int:event_id>/', views.next_week, name='next_week'),
    path('next_day/<int:event_id>/', views.next_day, name='next_day'),
    path("event/new/", views.create_event, name="event_new"),
    path("event/edit/<int:pk>/", views.EventEdit.as_view(), name="event_edit"),
    path("event/<int:event_id>/details/", views.event_details, name="event-detail"),
    path(
        "add_eventmember/<int:event_id>", views.add_eventmember, name="add_eventmember"
    ),

    path('change_event/<int:event_id>/', views.change_event, name='change_event'),
    path(
        "event/<int:pk>/remove",
        views.EventMemberDeleteView.as_view(),
        name="remove_event",
    ),
    path("all-event-list/", views.AllEventsListView.as_view(), name="all_events"),
    path(
        "running-event-list/",
        views.RunningEventsListView.as_view(),
        name="running_events",
    ),
    path(
        "upcoming-event-list/",
        views.UpcomingEventsListView.as_view(),
        name="upcoming_events",
    ),
    path(
        "completed-event-list/",
        views.CompletedEventsListView.as_view(),
        name="completed_events",
    ),
    path("stats/", AdminStatsView.as_view(), name="admin_stats"),
    path("user_stats/", views.UserStatsView.as_view(), name="user_stats"),

    path('get_table_statistics/', views.get_table_statistics, name='get_table_statistics'),
    path('api/user_events_count/', views.UserEventsCountView.as_view(), name='user_events_count'),
    path('create_yookassa_payment/', views.create_yookassa_payment, name='create_yookassa_payment'),
    path('my_bookings/', views.MyBookingsView.as_view(), name='my_bookings'),
    path('pay_booking/<int:booking_id>/', views.pay_booking, name='pay_booking'),
    path('payment_status/<int:temp_booking_id>/', views.payment_callback, name='payment_status'),

]
