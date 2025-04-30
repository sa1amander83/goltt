<template>
  <div class="row">
    <div class="col-md-12">
      <div class="tile row">
        <CurrentEvents />

        <div class="col-md-9">
          <Calendar
            :is-admin="isAdmin"
            :user-id="userId"
            @select="openEventModal"
            @event-click="openEventDetailModal"
          />
        </div>
      </div>
    </div>

    <EventModal
      ref="eventModal"
      :is-admin="isAdmin"
      :user-id="userId"
      @created="refreshCalendar"
    />

    <EventDetailModal
      ref="eventDetailModal"
      :is-admin="isAdmin"
      @deleted="refreshCalendar"
      @updated="refreshCalendar"
    />
  </div>
</template>

<script>
import Calendar from '@/views/Calendar.vue'
import CurrentEvents from '@/components/events/CurrentEvents.vue'
import EventModal from '@/components/calendar/EventModal.vue'
import EventDetailModal from '@/components/calendar/EventDetailModal.vue'

export default {
  name: 'CalendarView',
  components: {
    Calendar,
    CurrentEvents,
    EventModal,
    EventDetailModal
  },
  data() {
    return {
      isAdmin: false,
      userId: null
    }
  },
  created() {
    this.checkAuth()
  },
  methods: {
    checkAuth() {
      // Проверка авторизации и прав
    },
    openEventModal(selectionInfo) {
      this.$refs.eventModal.open(selectionInfo)
    },
    openEventDetailModal(event) {
      this.$refs.eventDetailModal.open(event)
    },
    refreshCalendar() {
      this.$refs.calendar.refetchEvents()
    }
  }
}
</script>
