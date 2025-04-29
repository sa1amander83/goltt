<template>
  <div id="external-events">
    <h4 class="mb-4">Сейчас идет</h4>
    <div v-if="events.length">
      <div v-for="event in events" :key="event.id" class="fc-event">
        <h3>{{ event.title }}</h3>
        <p>{{ event.description }}</p>
        <p>Стол №{{ event.table.number }}</p>
        <p>Начало: {{ formatDateTime(event.start_time) }}</p>
        <p>Конец: {{ formatDateTime(event.end_time) }}</p>
      </div>
    </div>
    <p v-else>Не найдено бронирований</p>
  </div>
</template>

<script>
export default {
  props: ['events'],
  methods: {
    formatDateTime(dateTime) {
      return new Date(dateTime).toLocaleString('ru-RU', { hour: '2-digit', minute: '2-digit', day: 'numeric', month: 'long' })
    }
  }
}
</script>
