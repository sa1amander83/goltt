import { createRouter, createWebHistory } from 'vue-router';
import Calendar from '@/components/calendar/Calendar.vue';
import EventsList from '@/components/events/EventsList.vue';
import RunningEvents from '@/components/events/RunningEvents.vue';
import UpcomingEvents from '@/components/events/UpcomingEvents.vue';
import CompletedEvents from '@/components/events/CompletedEvents.vue';
import CurrentBookings from '@/components/bookings/CurrentBookings.vue';
import UserStats from '@/views/UserStats.vue';
import AdminStats from '@/views/AdminStats.vue';
import Sidebar from '@/views/Sidebar.vue'; // if it's a layout

const routes = [
  {
    path: '/',
    redirect: '/calendar'
  },
  {
    path: '/calendar',
    name: 'Calendar',
    component: Calendar
  },
  {
    path: '/events',
    name: 'EventsList',
    component: EventsList
  },
  {
    path: '/events/running',
    name: 'RunningEvents',
    component: RunningEvents
  },
  {
    path: '/events/upcoming',
    name: 'UpcomingEvents',
    component: UpcomingEvents
  },
  {
    path: '/events/completed',
    name: 'CompletedEvents',
    component: CompletedEvents
  },
  {
    path: '/my-bookings',
    name: 'CurrentBookings',
    component: CurrentBookings
  },
  {
    path: '/user-stats',
    name: 'UserStats',
    component: UserStats
  },
  {
    path: '/admin-stats',
    name: 'AdminStats',
    component: AdminStats
  },
  {
    path: '/sidebar',
    name: 'Sidebar',
    component: Sidebar
  }
];

const router = createRouter({
  history: createWebHistory(),
  routes
});

export default router;
