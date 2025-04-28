<template>
  <div class="container mt-4">
    <h2>{{ statusTitle }}</h2>

    <div class="alert alert-info">
      Всего бронирований: {{ events.length }}
      <span v-if="!events.length">- Нет данных!</span>
    </div>

    <div v-if="messages.length" class="mb-3">
      <div v-for="(message, index) in messages" :key="index"
           :class="`alert alert-${message.type}`">
        {{ message.text }}
      </div>
    </div>

    <div v-if="events.length" class="table-responsive">
      <table class="table table-striped table-hover">
        <thead>
          <tr>
            <th>Название</th>
            <th>Стол</th>
            <th>Начало</th>
            <th>Конец</th>
            <th>Статус оплаты</th>
            <th>Стоимость</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="event in events" :key="event.id"
              @click="showEventDetails(event)"
              class="event-row">
            <td>{{ event.title }}</td>
            <td>Стол №{{ event.table.number }}</td>
            <td>{{ formatDateTime(event.start_time) }}</td>
            <td>{{ formatDateTime(event.end_time) }}</td>
            <td>
              <span :class="`badge bg-${getStatusBadgeClass(event)}`">
                {{ getStatusText(event) }}
              </span>
            </td>
            <td>{{ event.total_cost }} руб.</td>
          </tr>
        </tbody>
      </table>
    </div>
    <div v-else class="alert alert-info">У вас пока нет бронирований</div>

    <!-- Event Details Modal -->
    <div class="modal fade" id="eventDetailsModal" tabindex="-1" aria-hidden="true">
      <div class="modal-dialog modal-dialog-centered">
        <div class="modal-content">
          <div class="modal-header bg-primary text-white">
            <h5 class="modal-title">{{ selectedEvent.title }}</h5>
            <button type="button" class="btn-close" @click="closeModal"></button>
          </div>
          <div class="modal-body">
            <div class="mb-3">
              <label class="form-label"><strong>Описание:</strong></label>
              <p>{{ selectedEvent.description || 'Нет описания' }}</p>
            </div>
            <div class="row">
              <div class="col-md-6 mb-3">
                <label class="form-label"><strong>Начало:</strong></label>
                <p>{{ formatDateTime(selectedEvent.start_time) }}</p>
              </div>
              <div class="col-md-6 mb-3">
                <label class="form-label"><strong>Конец:</strong></label>
                <p>{{ formatDateTime(selectedEvent.end_time) }}</p>
              </div>
            </div>
            <div class="row">
              <div class="col-md-6 mb-3">
                <label class="form-label"><strong>Стол:</strong></label>
                <p>Стол №{{ selectedEvent.table.number }} ({{ selectedEvent.table.table_description }})</p>
              </div>
              <div class="col-md-6 mb-3">
                <label class="form-label"><strong>Статус:</strong></label>
                <p :class="`text-${getStatusBadgeClass(selectedEvent)}`">
                  {{ getStatusText(selectedEvent) }}
                </p>
              </div>
            </div>
            <div class="mb-3">
              <label class="form-label"><strong>Сумма:</strong></label>
              <p>{{ selectedEvent.total_cost }} руб.</p>
            </div>
          </div>
          <div class="modal-footer">
            <button type="button" class="btn btn-secondary" @click="closeModal">Закрыть</button>
            <button v-if="!selectedEvent.is_paid && !selectedEvent.is_canceled"
                    type="button" class="btn btn-success" @click="processPayment">
              Оплатить
            </button>
            <button v-if="!selectedEvent.is_paid && !selectedEvent.is_canceled"
                    type="button" class="btn btn-danger" @click="cancelBooking">
              Отменить
            </button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { Modal } from 'bootstrap'
import axios from 'axios'

export default {
  data() {
    return {
      events: [],
      selectedEvent: {},
      messages: [],
      eventModal: null,
      statusMap: {
        running: 'Текущие бронирования',
        upcoming: 'Предстоящие бронирования',
        completed: 'Завершенные бронирования'
      }
    }
  },
  computed: {
    currentStatus() {
      return this.$route.query.status || 'upcoming'
    },
    statusTitle() {
      return this.statusMap[this.currentStatus] || 'Все бронирования'
    }
  },
  async mounted() {
    this.eventModal = new Modal(document.getElementById('eventDetailsModal'))
    await this.loadEvents()

    // Check for messages in URL (e.g., after redirect from payment)
    if (this.$route.query.message) {
      this.messages.push({
        text: this.$route.query.message,
        type: this.$route.query.message_type || 'success'
      })
    }
  },
  methods: {
    async loadEvents() {
      try {
        const response = await axios.get('/api/events/', {
          params: {
            status: this.currentStatus
          }
        })
        this.events = response.data.events
      } catch (error) {
        console.error('Error loading events:', error)
      }
    },
    formatDateTime(dateTime) {
      return new Date(dateTime).toLocaleString('ru-RU', {
        day: '2-digit',
        month: '2-digit',
        year: 'numeric',
        hour: '2-digit',
        minute: '2-digit'
      })
    },
    getStatusBadgeClass(event) {
      if (event.is_paid) return 'success'
      if (event.is_canceled) return 'danger'
      return 'warning'
    },
    getStatusText(event) {
      if (event.is_paid) return 'Оплачено'
      if (event.is_canceled) return 'Отменено'
      return 'Ожидает оплаты'
    },
    showEventDetails(event) {
      this.selectedEvent = { ...event }
      this.eventModal.show()
    },
    closeModal() {
      this.eventModal.hide()
    },
    async processPayment() {
      try {
        const response = await axios.post(`/api/payments/${this.selectedEvent.id}/`)
        if (response.data.confirmation_url) {
          window.location.href = response.data.confirmation_url
        }
      } catch (error) {
        console.error('Payment error:', error)
        this.messages.push({
          text: 'Ошибка при создании платежа',
          type: 'danger'
        })
      }
    },
    async cancelBooking() {
      if (!confirm('Вы уверены, что хотите отменить это бронирование?')) return

      try {
        await axios.post(`/api/events/${this.selectedEvent.id}/cancel/`)
        this.closeModal()
        await this.loadEvents()
      } catch (error) {
        console.error('Error canceling booking:', error)
        this.messages.push({
          text: 'Ошибка при отмене бронирования',
          type: 'danger'
        })
      }
    }
  }
}
</script>

<style>
.event-row {
  cursor: pointer;
}
.event-row:hover {
  background-color: #f8f9fa;
}
</style>