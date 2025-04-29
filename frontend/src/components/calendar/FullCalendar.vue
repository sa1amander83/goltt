<template>
  <div id="calendar"></div>
</template>

<script>
import FullCalendar from '@fullcalendar/vue3'
import dayGridPlugin from '@fullcalendar/daygrid'
import timeGridPlugin from '@fullcalendar/timegrid'
import interactionPlugin from '@fullcalendar/interaction'
import ruLocale from '@fullcalendar/core/locales/ru'

export default {
  name: 'Calendar',
  components: {
    FullCalendar
  },
  props: {
    isAdmin: Boolean,
    userId: Number
  },
  data() {
    return {
      calendarOptions: {
        plugins: [dayGridPlugin, timeGridPlugin, interactionPlugin],
        initialView: 'timeGridWeek',
        locales: [ruLocale],
        locale: 'ru',
        selectable: this.userId !== null,
        select: this.handleSelect,
        eventClick: this.handleEventClick,
        events: this.fetchEvents
      }
    }
  },
  methods: {
    fetchEvents(info, successCallback, failureCallback) {
      this.$api.get('/api/events/')
        .then(response => successCallback(response.data))
        .catch(error => failureCallback(error))
    },
    handleSelect(selectionInfo) {
      this.$emit('select', selectionInfo)
    },
    handleEventClick(clickInfo) {
      this.$emit('event-click', clickInfo.event)
    }
  }
}
</script>
