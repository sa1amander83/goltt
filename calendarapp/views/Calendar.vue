<template>
  <div class="row">
    <div class="col-md-12">
      <div class="tile row">
        <div class="col-md-3">
          <div id="external-events">
            <h4 class="mb-4">Сейчас идет</h4>
            <div v-if="currentBookings.length">
              <div v-for="event in currentBookings" :key="event.id" class="fc-event">
                <h3>{{ event.title }}</h3>
                <p>{{ event.description }}</p>
                <p>Стол №{{ event.table.number }}</p>
                <p>Начало: {{ formatDateTime(event.start_time) }}</p>
                <p>Конец: {{ formatDateTime(event.end_time) }}</p>
              </div>
            </div>
            <p v-else>Не найдено бронирований</p>
          </div>
        </div>
        <div class="col-md-9">
          <FullCalendar :options="calendarOptions" />
        </div>
      </div>
    </div>

    <!-- Booking Modal -->
    <div class="modal fade" id="eventModal" tabindex="-1" aria-hidden="true">
      <div class="modal-dialog modal-dialog-centered">
        <div class="modal-content">
          <div class="modal-header bg-primary text-white">
            <h5 class="modal-title">Забронировать стол</h5>
            <button type="button" class="btn-close" @click="closeBookingModal"></button>
          </div>
          <form @submit.prevent="handleBookingSubmit">
            <div class="modal-body">
              <div class="form-group">
                <input
                  v-model="bookingForm.title"
                  type="text"
                  class="form-control"
                  placeholder="Название бронирования"
                  required
                >
              </div>
              <div class="form-group">
                <textarea
                  v-model="bookingForm.description"
                  class="form-control"
                  placeholder="Описание"
                ></textarea>
              </div>
              <div class="form-group">
                <label>Начало брони:</label>
                <VueDatePicker
                  v-model="bookingForm.start_time"
                  :min-date="new Date()"
                  :enable-time-picker="true"
                  :minutes-increment="30"
                  :format="'yyyy-MM-dd HH:mm'"
                  :locale="'ru'"
                  @update:model-value="calculateTimeAndCost"
                />
              </div>
              <div class="form-group">
                <label>Конец брони:</label>
                <VueDatePicker
                  v-model="bookingForm.end_time"
                  :min-date="bookingForm.start_time || new Date()"
                  :enable-time-picker="true"
                  :minutes-increment="30"
                  :format="'yyyy-MM-dd HH:mm'"
                  :locale="'ru'"
                  @update:model-value="calculateTimeAndCost"
                />
              </div>
              <div class="form-group">
                <label>Выберите стол:</label>
                <select
                  v-model="bookingForm.table_id"
                  class="form-control"
                  @change="calculateTimeAndCost"
                >
                  <option
                    v-for="table in availableTables"
                    :key="table.id"
                    :value="table.id"
                    :data-price-hour="table.price_per_hour"
                    :data-price-half-hour="table.price_per_half_hour"
                  >
                    Стол {{ table.number }} ({{ table.table_description }})
                  </option>
                </select>
              </div>
              <div class="d-flex justify-content-between important">
                <div class="form-group">
                  <label>Итоговая сумма: <span>{{ totalCost.toFixed(2) }} руб.</span></label>
                </div>
                <div class="form-group">
                  <label>Всего часов: <span>{{ totalTime }}</span></label>
                </div>
              </div>
            </div>
            <div class="modal-footer">
              <button type="button" class="btn btn-danger" @click="closeBookingModal">Закрыть</button>
              <button v-if="isAdmin" type="submit" class="btn btn-primary">Забронировать</button>
              <button type="button" class="btn btn-success" @click="processPayment">Оплатить</button>
            </div>
          </form>
        </div>
      </div>
    </div>

    <!-- Event Details Modal -->
    <div class="modal fade" id="detailModal" tabindex="-1" aria-hidden="true">
      <div class="modal-dialog modal-dialog-centered">
        <div class="modal-content">
          <div class="modal-header bg-primary text-white">
            <h5 class="modal-title">{{ selectedEvent.title }}</h5>
            <button type="button" class="btn-close" @click="closeDetailModal"></button>
          </div>
          <div class="modal-body">
            <div class="form-group">
              <p>{{ selectedEvent.description || 'Нет описания' }}</p>
            </div>
            <div class="form-group">
              <label>Начало брони:</label>
              <p>{{ formatDateTime(selectedEvent.start_time) }}</p>
            </div>
            <div class="form-group">
              <label>Конец брони:</label>
              <p>{{ formatDateTime(selectedEvent.end_time) }}</p>
            </div>
            <div class="form-group">
              <label>Забронирован стол: №{{ selectedEvent.table?.number }}</label>
            </div>
          </div>
          <div v-if="isAdmin" class="modal-footer">
            <button type="button" class="btn btn-primary" @click="openEditModal">Изменить</button>
            <button type="button" class="btn btn-danger" @click="deleteEvent">Удалить</button>
            <button type="button" class="btn btn-success" @click="copyToNextWeek">Следующая неделя</button>
            <button type="button" class="btn btn-primary" @click="copyToNextDay">Завтра</button>
            <button type="button" class="btn btn-success" @click="payExistingBooking">Оплатить</button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import FullCalendar from '@fullcalendar/vue3'
import dayGridPlugin from '@fullcalendar/daygrid'
import timeGridPlugin from '@fullcalendar/timegrid'
import interactionPlugin from '@fullcalendar/interaction'
import { Modal } from 'bootstrap'
import axios from 'axios'
import VueDatePicker from '@vuepic/vue-datepicker'
import '@vuepic/vue-datepicker/dist/main.css'

export default {
  components: {
    FullCalendar,
    VueDatePicker
  },
  data() {
    return {
      calendarOptions: {
        plugins: [dayGridPlugin, timeGridPlugin, interactionPlugin],
        initialView: 'timeGridWeek',
        headerToolbar: {
          left: 'prev,next today',
          center: 'title',
          right: 'dayGridMonth,timeGridWeek,timeGridDay,list'
        },
        buttonText: {
          today: 'Сегодня',
          month: 'Месяц',
          week: 'Неделя',
          day: 'День',
          list: 'Список'
        },
        locale: 'ru',
        selectable: true,
        selectMirror: true,
        select: this.handleDateSelect,
        eventClick: this.handleEventClick,
        events: [],
        slotDuration: '00:30:00',
        slotMinTime: '09:00:00',
        slotMaxTime: '24:00:00'
      },
      bookingForm: {
        title: '',
        description: '',
        start_time: null,
        end_time: null,
        table_id: null,
        total_cost: 0,
        total_time: 0
      },
      selectedEvent: {},
      currentBookings: [],
      availableTables: [],
      totalCost: 0,
      totalTime: 0,
      bookingModal: null,
      detailModal: null,
      isAdmin: false
    }
  },
  async mounted() {
    this.bookingModal = new Modal(document.getElementById('eventModal'))
    this.detailModal = new Modal(document.getElementById('detailModal'))
    this.isAdmin = await this.checkAdminStatus()
    await this.loadCurrentEvents()
    await this.loadCalendarEvents()
  },
  methods: {
    async checkAdminStatus() {
      try {
        const response = await axios.get('/api/user/me/')
        return response.data.is_superuser
      } catch (error) {
        console.error('Error checking admin status:', error)
        return false
      }
    },
    async loadCurrentEvents() {
      try {
        const response = await axios.get('/api/events/running/')
        this.currentBookings = response.data.events
      } catch (error) {
        console.error('Error loading current events:', error)
      }
    },
    async loadCalendarEvents() {
      try {
        const today = new Date()
        const response = await axios.get(`/api/calendar/?year=${today.getFullYear()}&month=${today.getMonth() + 1}`)
        this.calendarOptions.events = response.data.events
      } catch (error) {
        console.error('Error loading calendar events:', error)
      }
    },
    async handleDateSelect(selectInfo) {
      if (!this.$store.getters.isAuthenticated) {
        alert('Для создания бронирования необходимо войти в систему')
        return
      }

      try {
        const response = await axios.get('/api/tables/available/', {
          params: {
            start_time: selectInfo.start.toISOString(),
            end_time: selectInfo.end.toISOString()
          }
        })
        this.availableTables = response.data.tables
        this.bookingForm.start_time = selectInfo.start
        this.bookingForm.end_time = selectInfo.end
        this.bookingModal.show()
      } catch (error) {
        console.error('Error checking available tables:', error)
      }
    },
    handleEventClick(clickInfo) {
      this.selectedEvent = {
        ...clickInfo.event.extendedProps,
        id: clickInfo.event.id,
        start_time: clickInfo.event.start,
        end_time: clickInfo.event.end,
        title: clickInfo.event.title
      }
      this.detailModal.show()
    },
    closeBookingModal() {
      this.bookingModal.hide()
      this.resetBookingForm()
    },
    closeDetailModal() {
      this.detailModal.hide()
    },
    resetBookingForm() {
      this.bookingForm = {
        title: '',
        description: '',
        start_time: null,
        end_time: null,
        table_id: null,
        total_cost: 0,
        total_time: 0
      }
      this.totalCost = 0
      this.totalTime = 0
    },
    calculateTimeAndCost() {
      if (!this.bookingForm.start_time || !this.bookingForm.end_time || !this.bookingForm.table_id) return

      const startTime = new Date(this.bookingForm.start_time)
      const endTime = new Date(this.bookingForm.end_time)
      const diffMs = endTime - startTime
      const diffHours = diffMs / (1000 * 60 * 60)
      this.totalTime = Math.round(diffHours * 2) / 2

      // Check max duration for non-admins
      if (diffHours > 3 && !this.isAdmin) {
        alert('Максимальная продолжительность бронирования - 3 часа')
        this.bookingForm.end_time = new Date(startTime.getTime() + 3 * 60 * 60 * 1000)
        return
      }

      const selectedTable = this.availableTables.find(t => t.id == this.bookingForm.table_id)
      if (!selectedTable) return

      this.totalCost = Math.floor(this.totalTime) * selectedTable.price_per_hour +
        (this.totalTime % 1 !== 0 ? selectedTable.price_per_half_hour : 0)

      this.bookingForm.total_cost = this.totalCost
      this.bookingForm.total_time = this.totalTime
    },
    formatDateTime(dateTime) {
      return new Date(dateTime).toLocaleString('ru-RU', {
        weekday: 'long',
        year: 'numeric',
        month: 'long',
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit'
      })
    },
    async handleBookingSubmit() {
      try {
        await axios.post('/api/events/', this.bookingForm)
        this.closeBookingModal()
        await this.loadCalendarEvents()
        await this.loadCurrentEvents()
      } catch (error) {
        console.error('Error creating booking:', error)
        alert('Ошибка при создании бронирования')
      }
    },
    async processPayment() {
      try {
        const response = await axios.post('/api/payments/', this.bookingForm)
        if (response.data.confirmation_url) {
          window.location.href = response.data.confirmation_url
        }
      } catch (error) {
        console.error('Payment error:', error)
        alert('Ошибка при создании платежа')
      }
    },
    async deleteEvent() {
      if (!confirm('Хотите удалить событие?')) return

      try {
        await axios.delete(`/api/events/${this.selectedEvent.id}/`)
        this.closeDetailModal()
        await this.loadCalendarEvents()
        await this.loadCurrentEvents()
      } catch (error) {
        console.error('Error deleting event:', error)
      }
    },
    async copyToNextWeek() {
      try {
        await axios.post(`/api/events/${this.selectedEvent.id}/copy/`, { days: 7 })
        await this.loadCalendarEvents()
        this.closeDetailModal()
      } catch (error) {
        console.error('Error copying to next week:', error)
      }
    },
    async copyToNextDay() {
      try {
        await axios.post(`/api/events/${this.selectedEvent.id}/copy/`, { days: 1 })
        await this.loadCalendarEvents()
        this.closeDetailModal()
      } catch (error) {
        console.error('Error copying to next day:', error)
      }
    },
    async payExistingBooking() {
      try {
        const response = await axios.post(`/api/payments/${this.selectedEvent.id}/`)
        if (response.data.confirmation_url) {
          window.location.href = response.data.confirmation_url
        }
      } catch (error) {
        console.error('Payment error:', error)
        alert('Ошибка при создании платежа')
      }
    },
    openEditModal() {
      this.bookingForm = {
        title: this.selectedEvent.title,
        description: this.selectedEvent.description,
        start_time: new Date(this.selectedEvent.start_time),
        end_time: new Date(this.selectedEvent.end_time),
        table_id: this.selectedEvent.table?.id,
        total_cost: this.selectedEvent.total_cost,
        total_time: this.selectedEvent.total_time
      }
      this.totalCost = this.selectedEvent.total_cost
      this.totalTime = this.selectedEvent.total_time
      this.detailModal.hide()
      this.bookingModal.show()
    }
  }
}
</script>

<style>
.fc-day-today {
  background-color: var(--fc-today-bg-color, rgba(255, 220, 40, 0.15)) !important;
}
</style>