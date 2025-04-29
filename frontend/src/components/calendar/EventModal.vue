<template>
  <div class="modal fade" id="eventModal" tabindex="-1" role="dialog" aria-hidden="true">
    <div class="modal-dialog modal-dialog-centered" role="document">
      <div class="modal-content">
        <div class="modal-header bg-primary">
          <h5 class="modal-title text-white">Забронировать стол</h5>
          <button type="button" class="close" @click="closeModal" aria-label="Close">
            <span aria-hidden="true">&times;</span>
          </button>
        </div>

        <form @submit.prevent="submitForm">
          <div class="modal-body">
            <div class="form-group">
              <input
                v-model="form.title"
                class="form-control"
                placeholder="Название бронирования"
                required
              >
            </div>

            <div class="form-group">
              <textarea
                v-model="form.description"
                class="form-control"
                placeholder="Описание"
              ></textarea>
            </div>

            <div class="form-group">
              <label>Начало брони:</label>
              <flat-pickr
                v-model="form.start_time"
                :config="timePickerConfig"
                class="form-control"
                @on-change="calculateTimeAndCost"
              ></flat-pickr>
            </div>

            <div class="form-group">
              <label>Конец брони:</label>
              <flat-pickr
                v-model="form.end_time"
                :config="timePickerConfig"
                class="form-control"
                @on-change="calculateTimeAndCost"
              ></flat-pickr>
            </div>

            <div class="form-group">
              <label>Выберите стол:</label>
              <select
                v-model="form.table"
                class="form-control"
                @change="calculateTimeAndCost"
              >
                <option
                  v-for="table in tables"
                  :key="table.id"
                  :value="table.id"
                  :data-price-hour="table.price_per_hour"
                  :data-price-half-hour="table.price_per_half_hour"
                >
                  Стол {{ table.number }} ({{ table.description }})
                </option>
              </select>
            </div>

            <div class="d-flex justify-content-between important">
              <div class="form-group">
                <label>Итоговая сумма: <span>{{ form.total_cost }} руб.</span></label>
                <input type="hidden" name="total_cost" v-model="form.total_cost">
              </div>

              <div class="form-group">
                <label>Всего часов: <span>{{ form.total_time }}</span></label>
                <input type="hidden" name="total_time" v-model="form.total_time">
              </div>
            </div>
          </div>

          <div class="modal-footer">
            <button type="button" class="btn btn-danger" @click="closeModal">Закрыть</button>
            <button
              v-if="isAdmin"
              type="submit"
              class="btn btn-primary"
              :disabled="loading"
            >
              <span v-if="loading" class="spinner-border spinner-border-sm"></span>
              {{ editMode ? 'Обновить' : 'Забронировать' }}
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
        </form>
      </div>
    </div>
  </div>
</template>

<script>
import flatPickr from 'vue-flatpickr-component'
import 'flatpickr/dist/flatpickr.min.css'
import { Russian } from 'flatpickr/dist/l10n/ru.js'

export default {
  components: {
    flatPickr
  },

  props: {
    isAdmin: Boolean,
    userId: Number,
    csrfToken: String
  },

  data() {
    return {
      form: {
        title: '',
        description: '',
        start_time: '',
        end_time: '',
        table: '',
        total_cost: 0,
        total_time: 0
      },
      tables: [],
      editMode: false,
      currentEventId: null,
      loading: false,
      timePickerConfig: {
        enableTime: true,
        dateFormat: "Y-m-d H:i",
        time_24hr: true,
        minuteIncrement: 30,
        locale: Russian
      }
    }
  },

  methods: {
    open(selectionInfo = null, eventData = null) {
      this.resetForm()

      if (eventData) {
        this.editMode = true
        this.currentEventId = eventData.id
        this.form = {
          title: eventData.title,
          description: eventData.description,
          start_time: this.formatDateForDjango(eventData.start),
          end_time: this.formatDateForDjango(eventData.end),
          table: eventData.table_number,
          total_cost: 0,
          total_time: 0
        }
      } else if (selectionInfo) {
        this.form.start_time = this.formatDateForDjango(selectionInfo.start)
        this.form.end_time = this.formatDateForDjango(selectionInfo.end)
      }

      this.calculateTimeAndCost()
      $('#eventModal').modal('show')
    },

    closeModal() {
      $('#eventModal').modal('hide')
    },

    resetForm() {
      this.form = {
        title: '',
        description: '',
        start_time: '',
        end_time: '',
        table: '',
        total_cost: 0,
        total_time: 0
      }
      this.editMode = false
      this.currentEventId = null
    },

    calculateTimeAndCost() {
      if (!this.form.start_time || !this.form.end_time) return

      const start = new Date(this.form.start_time)
      const end = new Date(this.form.end_time)
      const diffMs = end - start

      const diffHours = diffMs / (1000 * 60 * 60)
      const roundedHours = Math.round(diffHours * 2) / 2

      if (diffHours > 3 && !this.isAdmin) {
        alert('Максимальная продолжительность бронирования - 3 часа')
        this.form.end_time = this.formatDateForDjango(new Date(start.getTime() + 3 * 60 * 60 * 1000))
        return
      }

      const selectedTable = this.tables.find(t => t.id == this.form.table)
      if (!selectedTable) return

      const totalCost = Math.floor(roundedHours) * selectedTable.price_per_hour +
        (roundedHours % 1 !== 0 ? selectedTable.price_per_half_hour : 0)

      this.form.total_time = roundedHours
      this.form.total_cost = totalCost
    },

    submitForm() {
      this.loading = true
      const url = this.editMode
        ? `/change_event/${this.currentEventId}/`
        : '/create_event/'

      const formData = new FormData()
      for (const key in this.form) {
        formData.append(key, this.form[key])
      }
      formData.append('csrfmiddlewaretoken', this.csrfToken)

      fetch(url, {
        method: 'POST',
        body: formData
      })
      .then(response => response.json())
      .then(data => {
        if (data.success) {
          this.$emit('saved')
          this.closeModal()
        } else {
          alert(data.error || 'Ошибка сохранения')
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
      const formData = new FormData()

      for (const key in this.form) {
        formData.append(key, this.form[key])
      }
      formData.append('csrfmiddlewaretoken', this.csrfToken)

      fetch('/create_yookassa_payment/', {
        method: 'POST',
        body: formData
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

    formatDateForDjango(date) {
      const d = new Date(date)
      return `${d.getFullYear()}-${(d.getMonth() + 1).toString().padStart(2, '0')}-${d.getDate().toString().padStart(2, '0')} ` +
        `${d.getHours().toString().padStart(2, '0')}:${d.getMinutes().toString().padStart(2, '0')}:00`
    }
  },

  mounted() {
    // Загрузка списка столов
    fetch('/api/tables/')
      .then(response => response.json())
      .then(data => {
        this.tables = data
        if (this.tables.length) {
          this.form.table = this.tables[0].id
        }
      })
  }
}
</script>
