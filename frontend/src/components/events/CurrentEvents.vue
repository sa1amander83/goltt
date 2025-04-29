<template>
  <div class="col-md-3">
    <div id="external-events">
      <h4 class="mb-4">Сейчас идет</h4>
      <div v-if="currentBookings.length">
        <div class="fc-event" v-for="event in currentBookings" :key="event.id">
          <h3>{{ event.title }}</h3>
          <p>{{ event.description }}</p>
          <p>Стол {{ event.table_number }}</p>
          <p>Начало: {{ formatDateTime(event.start_time) }}</p>
          <p>Конец: {{ formatDateTime(event.end_time) }}</p>
        </div>
      </div>
      <p v-else>Не найдено бронирований</p>
    </div>
  </div>
</template>

<script>
export default {
  name: 'CurrentEvents',
  data() {
    return {
      currentBookings: []
    }
  },
  methods: {
    fetchCurrentEvents() {
      this.$api.get('/api/current_events/')
        .then(response => {
          this.currentBookings = response.data
        })
    },
    formatDateTime(datetime) {
      return new Date(datetime).toLocaleString('ru-RU')
    }
  },
  mounted() {
    this.fetchCurrentEvents()
  }
}
</script>
