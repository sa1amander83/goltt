<template>
  <div class="calendar-page">
    <div class="calendar-header">
      <h2>
        <i class="fas fa-calendar-alt me-2"></i>
        Календарь бронирований
      </h2>
      <button
        v-if="isAuthenticated"
        class="btn btn-primary"
        @click="openQuickBooking"
      >
        <i class="fas fa-plus me-1"></i> Быстрое бронирование
      </button>
    </div>

    <div class="calendar-container">
      <FullCalendar ref="calendar" :options="calendarOptions" />
    </div>

    <!-- Модальное окно бронирования -->
    <BookingModal
      ref="bookingModal"
      :tables="availableTables"
      @booking-created="handleBookingCreated"
    />

    <!-- Модальное окно деталей события -->
    <EventDetailModal
      ref="eventDetailModal"
      :is-admin="isAdmin"
      @event-deleted="refreshCalendar"
      @event-updated="refreshCalendar"
    />

    <div v-if="error" class="alert alert-danger mt-3">
      {{ error }}
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useStore } from 'vuex'
import axios from 'axios'
import FullCalendar from '@fullcalendar/vue3'
import dayGridPlugin from '@fullcalendar/daygrid'
import timeGridPlugin from '@fullcalendar/timegrid'
import interactionPlugin from '@fullcalendar/interaction'
import ruLocale from '@fullcalendar/core/locales/ru'
import BookingModal from '@/components/bookings/BookingModal.vue'
import EventDetailModal from '@/components/calendar/EventDetailModal.vue'

// Ссылки на store и refs
const store = useStore()
const calendar = ref(null)
const bookingModal = ref(null)
const eventDetailModal = ref(null)
const availableTables = ref([])
const error = ref(null)

// Геттеры авторизации и прав
const isAdmin = computed(() => store.getters.isAdmin)
const isAuthenticated = computed(() => store.getters.isAuthenticated)

// Настройки FullCalendar
const calendarOptions = {
  plugins: [dayGridPlugin, timeGridPlugin, interactionPlugin],
  initialView: 'timeGridWeek',
  locales: [ruLocale],
  locale: 'ru',
  headerToolbar: {
    left: 'prev,next today',
    center: 'title',
    right: 'dayGridMonth,timeGridWeek,timeGridDay'
  },
  buttonText: {
    today: 'Сегодня',
    month: 'Месяц',
    week: 'Неделя',
    day: 'День'
  },
  slotDuration: '00:30:00',
  slotMinTime: '09:00:00',
  slotMaxTime: '24:00:00',
  selectable: isAuthenticated.value,
  selectMirror: true,
  select: handleDateSelect,
  eventClick: handleEventClick,
  events: fetchEvents,
  height: 'auto',
  eventDisplay: 'block',
  eventTimeFormat: {
    hour: '2-digit',
    minute: '2-digit',
    hour12: false
  }
}

// Получение событий для календаря
async function fetchEvents(info, successCallback, failureCallback) {
  error.value = null
  try {
    const params = {
      start: info.start.toISOString(),
      end: info.end.toISOString()
    }
    const response = await axios.get('/api/events/', { params })
    // Обеспечиваем, что всегда возвращаем массив
    const rawEvents = Array.isArray(response.data)
      ? response.data
      : response.data.events

    if (!Array.isArray(rawEvents)) {
      throw new Error('Некорректный формат событий от сервера')
    }
    successCallback(rawEvents)
  } catch (err) {
    error.value = 'Ошибка загрузки событий: ' + (err.response?.data?.detail || err.message)
    console.error('Error loading events:', err)
    successCallback([]) // Показываем пустой календарь при ошибке
  }
}

// Обработка выделения диапазона для создания бронирования
async function handleDateSelect(selectInfo) {
  if (!isAuthenticated.value) {
    alert('Для создания бронирования необходимо войти в систему')
    return
  }

  try {
    const params = {
      start_time: selectInfo.start.toISOString(),
      end_time: selectInfo.end.toISOString()
    }
    const response = await axios.get('/api/tables/available/', { params })
    availableTables.value = response.data.tables

    bookingModal.value.open({
      start: selectInfo.start,
      end: selectInfo.end
    })
  } catch (err) {
    error.value = 'Ошибка при проверке доступности столов'
    console.error('Error checking available tables:', err)
    alert('Ошибка при проверке доступности столов')
  }
}

// Клик по событию - показать детали
function handleEventClick(clickInfo) {
  eventDetailModal.value.open(clickInfo.event)
}

// Быстрое бронирование
function openQuickBooking() {
  bookingModal.value.open()
}

// Обновление календаря после событий
function refreshCalendar() {
  calendar.value?.getApi().refetchEvents()
}

function handleBookingCreated() {
  refreshCalendar()
}

// Автоматическое обновление при монтировании
onMounted(() => {
  refreshCalendar()
})
</script>

<style scoped>
.calendar-page {
  background: #f8f9fa;
  padding: 20px;
  border-radius: 8px;
  box-shadow: 0 2px 10px rgba(0, 0, 0, 0.05);
}

.calendar-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.calendar-container {
  background: white;
  border-radius: 8px;
  padding: 15px;
  box-shadow: 0 2px 5px rgba(0, 0, 0, 0.05);
}

:deep(.fc) {
  font-family: inherit;
}

:deep(.fc-toolbar-title) {
  font-size: 1.2rem;
  font-weight: 500;
}

:deep(.fc-daygrid-day-number) {
  color: #495057;
}

:deep(.fc-day-today) {
  background-color: rgba(13, 110, 253, 0.1) !important;
}

:deep(.fc-event) {
  cursor: pointer;
  border: none;
  background-color: #3c8dbc;
  color: white;
  padding: 3px 5px;
  border-radius: 3px;
}

:deep(.fc-event:hover) {
  opacity: 0.9;
}

.alert {
  margin-top: 20px;
}
</style>
