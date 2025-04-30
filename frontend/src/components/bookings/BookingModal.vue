<template>
  <div class="modal fade" id="bookingModal" tabindex="-1" aria-hidden="true">
    <div class="modal-dialog modal-dialog-centered">
      <div class="modal-content">
        <div class="modal-header bg-primary text-white">
          <h5 class="modal-title">
            {{ editMode ? 'Редактировать бронь' : 'Новое бронирование' }}
          </h5>
          <button
            type="button"
            class="btn-close btn-close-white"
            @click="closeModal"
          ></button>
        </div>

        <form @submit.prevent="submitForm">
          <div class="modal-body">
            <div class="form-group mb-3">
              <label class="form-label">Название</label>
              <input
                v-model="form.title"
                type="text"
                class="form-control"
                placeholder="Название бронирования"
                required
              >
            </div>

            <div class="form-group mb-3">
              <label class="form-label">Описание</label>
              <textarea
                v-model="form.description"
                class="form-control"
                placeholder="Описание (необязательно)"
                rows="2"
              ></textarea>
            </div>

            <div class="row">
              <div class="col-md-6">
                <div class="form-group mb-3">
                  <label class="form-label">Начало</label>
                  <VueDatePicker
                    v-model="form.start_time"
                    :min-date="new Date()"
                    :enable-time-picker="true"
                    :minutes-increment="30"
                    :format="'dd.MM.yyyy HH:mm'"
                    :locale="'ru'"
                    text-input
                    required
                    @update:model-value="calculateTimeAndCost"
                  />
                </div>
              </div>

              <div class="col-md-6">
                <div class="form-group mb-3">
                  <label class="form-label">Конец</label>
                  <VueDatePicker
                    v-model="form.end_time"
                    :min-date="form.start_time || new Date()"
                    :enable-time-picker="true"
                    :minutes-increment="30"
                    :format="'dd.MM.yyyy HH:mm'"
                    :locale="'ru'"
                    text-input
                    required
                    @update:model-value="calculateTimeAndCost"
                  />
                </div>
              </div>
            </div>

            <div class="form-group mb-3">
              <label class="form-label">Стол</label>
              <select
                v-model="form.table_id"
                class="form-select"
                required
                @change="calculateTimeAndCost"
              >
                <option value="" disabled>Выберите стол</option>
                <option
                  v-for="table in tables"
                  :key="table.id"
                  :value="table.id"
                >
                  Стол {{ table.number }} ({{ table.price_per_hour }} руб./час)
                </option>
              </select>
            </div>

            <div class="booking-summary">
              <div class="summary-item">
                <span>Продолжительность:</span>
                <strong>{{ totalTime }} ч.</strong>
              </div>
              <div class="summary-item">
                <span>Стоимость:</span>
                <strong>{{ totalCost.toFixed(2) }} руб.</strong>
              </div>
            </div>
          </div>

          <div class="modal-footer">
            <button
              type="button"
              class="btn btn-secondary"
              @click="closeModal"
              :disabled="loading"
            >
              Отмена
            </button>
            <button
              type="submit"
              class="btn btn-primary"
              :disabled="loading"
            >
              <span
                v-if="loading"
                class="spinner-border spinner-border-sm me-1"
              ></span>
              {{ editMode ? 'Обновить' : 'Забронировать' }}
            </button>
            <button
              v-if="!editMode"
              type="button"
              class="btn btn-success"
              @click="processPayment"
              :disabled="loading"
            >
              <span
                v-if="loading"
                class="spinner-border spinner-border-sm me-1"
              ></span>
              Оплатить
            </button>
          </div>
        </form>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, defineProps, defineEmits } from 'vue'
import axios from 'axios'
import VueDatePicker from '@vuepic/vue-datepicker'
import { Modal } from 'bootstrap'
import '@vuepic/vue-datepicker/dist/main.css'

const props = defineProps({
  tables: {
    type: Array,
    default: () => []
  },
  isAdmin: {
    type: Boolean,
    default: false
  }
})

const emit = defineEmits(['booking-created', 'booking-updated'])

const form = ref({
  title: '',
  description: '',
  start_time: null,
  end_time: null,
  table_id: '',
  total_cost: 0,
  total_time: 0
})

const loading = ref(false)
const editMode = ref(false)
const currentBookingId = ref(null)
const modalInstance = ref(null)

const totalTime = computed(() => {
  return form.value.total_time.toFixed(1)
})

const totalCost = computed(() => {
  return form.value.total_cost
})

const open = (initialData = null) => {
  resetForm()

  if (initialData?.id) {
    editMode.value = true
    currentBookingId.value = initialData.id
    form.value = {
      title: initialData.title,
      description: initialData.description,
      start_time: new Date(initialData.start),
      end_time: new Date(initialData.end),
      table_id: initialData.extendedProps.table_id,
      total_cost: initialData.extendedProps.total_cost,
      total_time: initialData.extendedProps.total_time
    }
  } else if (initialData?.start && initialData?.end) {
    form.value.start_time = new Date(initialData.start)
    form.value.end_time = new Date(initialData.end)
  }

  if (!modalInstance.value) {
    modalInstance.value = new Modal(document.getElementById('bookingModal'))
  }

  modalInstance.value.show()
  calculateTimeAndCost()
}

const closeModal = () => {
  modalInstance.value.hide()
}

const resetForm = () => {
  form.value = {
    title: '',
    description: '',
    start_time: null,
    end_time: null,
    table_id: '',
    total_cost: 0,
    total_time: 0
  }
  editMode.value = false
  currentBookingId.value = null
}

const calculateTimeAndCost = () => {
  if (!form.value.start_time || !form.value.end_time || !form.value.table_id) return

  const start = new Date(form.value.start_time)
  const end = new Date(form.value.end_time)

  if (start >= end) {
    form.value.end_time = new Date(start.getTime() + 30 * 60 * 1000)
    return
  }

  const diffMs = end - start
  const diffHours = diffMs / (1000 * 60 * 60)
  form.value.total_time = Math.round(diffHours * 2) / 2

  const selectedTable = props.tables.find(t => t.id == form.value.table_id)
  if (!selectedTable) return

  // Проверка максимальной продолжительности для обычных пользователей
  if (diffHours > 3 && !props.isAdmin) {
    alert('Максимальная продолжительность бронирования - 3 часа')
    form.value.end_time = new Date(start.getTime() + 3 * 60 * 60 * 1000)
    return
  }

  form.value.total_cost = Math.floor(form.value.total_time) * selectedTable.price_per_hour +
    (form.value.total_time % 1 !== 0 ? selectedTable.price_per_half_hour || selectedTable.price_per_hour * 0.5 : 0)
}

const submitForm = async () => {
  loading.value = true

  try {
    const url = editMode.value
      ? `/api/bookings/${currentBookingId.value}/`
      : '/api/bookings/'

    const method = editMode.value ? 'PUT' : 'POST'

    const response = await axios({
      method,
      url,
      data: {
        title: form.value.title,
        description: form.value.description,
        start_time: form.value.start_time.toISOString(),
        end_time: form.value.end_time.toISOString(),
        table_id: form.value.table_id,
        total_cost: form.value.total_cost,
        total_time: form.value.total_time
      }
    })

    if (editMode.value) {
      emit('booking-updated', response.data)
    } else {
      emit('booking-created', response.data)
    }

    closeModal()
  } catch (error) {
    console.error('Ошибка при сохранении бронирования:', error)
    alert(error.response?.data?.message || 'Произошла ошибка при сохранении')
  } finally {
    loading.value = false
  }
}

const processPayment = async () => {
  loading.value = true

  try {
    const response = await axios.post('/api/payments/create/', {
      booking_data: {
        title: form.value.title,
        start_time: form.value.start_time.toISOString(),
        end_time: form.value.end_time.toISOString(),
        table_id: form.value.table_id,
        amount: form.value.total_cost
      }
    })

    if (response.data.confirmation_url) {
      window.location.href = response.data.confirmation_url
    }
  } catch (error) {
    console.error('Ошибка при создании платежа:', error)
    alert(error.response?.data?.message || 'Произошла ошибка при оплате')
  } finally {
    loading.value = false
  }
}

defineExpose({
  open,
  closeModal
})
</script>

<style scoped>
.booking-summary {
  background-color: #f8f9fa;
  border-radius: 5px;
  padding: 15px;
  margin-top: 20px;
}

.summary-item {
  display: flex;
  justify-content: space-between;
  margin-bottom: 8px;
}

.summary-item:last-child {
  margin-bottom: 0;
}

.form-group {
  margin-bottom: 1rem;
}

.dp__input {
  height: 38px;
  border: 1px solid #ced4da;
  border-radius: 0.25rem;
}

.dp__input:hover {
  border-color: #86b7fe;
}
</style>
