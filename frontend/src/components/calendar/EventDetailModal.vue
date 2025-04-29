<template>
  <div class="modal fade" id="detailModal" tabindex="-1" role="dialog" aria-hidden="true">
    <div class="modal-dialog modal-dialog-centered" role="document">
      <div class="modal-content">
        <div class="modal-header bg-primary">
          <h5 class="modal-title text-white">{{ event.title }}</h5>
          <button type="button" class="close" @click="closeModal" aria-label="Close">
            <span aria-hidden="true">&times;</span>
          </button>
        </div>

        <div class="modal-body">
          <div class="form-group">
            <p>{{ event.description }}</p>
          </div>

          <div class="form-group">
            <label>Начало брони:</label>
            <p>{{ formatDateTime(event.start) }}</p>
          </div>

          <div class="form-group">
            <label>Конец брони:</label>
            <p>{{ formatDateTime(event.end) }}</p>
          </div>

          <div class="form-group">
            <label>Забронирован стол: №{{ event.table_number }}</label>
          </div>
        </div>

        <div class="modal-footer" v-if="isAdmin">
          <button
            type="button"
            class="btn btn-primary"
            @click="editEvent"
          >
            Изменить
          </button>

          <button
            type="button"
            class="btn btn-danger"
            @click="deleteEvent"
            :disabled="loading"
          >
            <span v-if="loading" class="spinner-border spinner-border-sm"></span>
            Удалить
          </button>

          <button
            type="button"
            class="btn btn-success"
            @click="copyToNextWeek"
            :disabled="loading"
          >
            Следующая неделя
          </button>

          <button
            type="button"
            class="btn btn-primary"
            @click="copyToNextDay"
            :disabled="loading"
          >
            Завтра
          </button>

          <button
            type="button"
            class="btn btn-success"
            @click="processPayment"
            :disabled="loading"
          >
            <span v-if="loading" class="spinner-border spinner-border-sm"></span>
            Оплатить
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
export default {
  props: {
    isAdmin: Boolean,
    csrfToken: String
  },

  data() {
    return {
      event: {
        id: null,
        title: '',
        description: '',
        start: '',
        end: '',
        table_number: ''
      },
      loading: false
    }
  },

  methods: {
    open(eventData) {
      this.event = {
        id: eventData.id,
        title: eventData.title,
        description: eventData.extendedProps.description,
        start: eventData.start,
        end: eventData.end,
        table_number: eventData.extendedProps.table_number
      }
      $('#detailModal').modal('show')
    },

    closeModal() {
      $('#detailModal').modal('hide')
    },

    editEvent() {
      this.closeModal()
      this.$emit('edit', this.event)
    },

    deleteEvent() {
      if (!confirm('Хотите удалить событие?')) return

      this.loading = true

      fetch(`/delete_event/${this.event.id}/`, {
        method: 'POST',
        headers: {
          'X-CSRFToken': this.csrfToken,
          'Content-Type': 'application/x-www-form-urlencoded',
        }
      })
      .then(response => response.json())
      .then(data => {
        if (data.success) {
          this.$emit('deleted')
          this.closeModal()
        } else {
          alert(data.error || 'Ошибка удаления')
        }
      })
      .catch(error => {
        console.error('Error:', error)
        alert('Ошибка соединения')
      })
      .finally(() => {
        this.loading = false
      })
    },

    copyToNextWeek() {
      this.copyEvent('next_week')
    },

    copyToNextDay() {
      this.copyEvent('next_day')
    },

    copyEvent(action) {
      if (!confirm(`Хотите добавить событие на ${action === 'next_week' ? 'следующую неделю' : 'завтра'}?`)) return

      this.loading = true

      fetch(`/${action}/${this.event.id}/`, {
        method: 'POST',
        headers: {
          'X-CSRFToken': this.csrfToken,
          'Content-Type': 'application/x-www-form-urlencoded',
        }
      })
      .then(response => response.json())
      .then(data => {
        if (data.success) {
          this.$emit('copied')
          alert('Событие успешно скопировано')
        } else {
          alert(data.error || 'Ошибка копирования')
        }
      })
      .catch(error => {
        console.error('Error:', error)
        alert('Ошибка соединения')
      })
      .finally(() => {
        this.loading = false
      })
    },

    processPayment() {
      this.loading = true

      fetch(`/pay_booking/${this.event.id}/`, {
        method: 'POST',
        headers: {
          'X-CSRFToken': this.csrfToken,
          'Content-Type': 'application/x-www-form-urlencoded',
        }
      })
      .then(response => response.json())
      .then(data => {
        if (data.confirmation_url) {
          window.location.href = data.confirmation_url
        } else {
          throw new Error(data.error || 'Ошибка платежа')
        }
      })
      .catch(error => {
        alert(error.message)
      })
      .finally(() => {
        this.loading = false
      })
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
    }
  }
}
</script>
