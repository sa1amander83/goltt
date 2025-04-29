<template>
  <div class="modal fade show" tabindex="-1" style="display: block; background: rgba(0,0,0,0.5)">
    <div class="modal-dialog modal-dialog-centered">
      <div class="modal-content">
        <div class="modal-header bg-primary text-white">
          <h5 class="modal-title">
            {{ isEditMode ? 'Редактировать бронь' : 'Новая бронь' }}
          </h5>
          <button type="button" class="btn-close" @click="$emit('close')"></button>
        </div>

        <form @submit.prevent="submitBooking">
          <div class="modal-body">
            <!-- Title -->
            <div class="form-group mb-3">
              <label class="form-label">Название</label>
              <input v-model="bookingForm.title" type="text" class="form-control" required>
            </div>

            <!-- Description -->
            <div class="form-group mb-3">
              <label class="form-label">Описание</label>
              <textarea v-model="bookingForm.description" class="form-control" rows="3"></textarea>
            </div>

            <!-- Dates -->
            <div class="row">
              <div class="col-md-6 form-group mb-3">
                <label class="form-label">Начало брони</label>
                <VueDatePicker
                  v-model="bookingForm.start_time"
                  :min-date="new Date()"
                  :enable-time-picker="true"
                  :minutes-increment="30"
                  :format="'yyyy-MM-dd HH:mm'"
                  locale="ru"
                  @update:model-value="calculateTotal"
                />
              </div>

              <div class="col-md-6 form-group mb-3">
                <label class="form-label">Конец брони</label>
                <VueDatePicker
                  v-model="bookingForm.end_time"
                  :min-date="bookingForm.start_time || new Date()"
                  :enable-time-picker="true"
                  :minutes-increment="30"
                  :format="'yyyy-MM-dd HH:mm'"
                  locale="ru"
                  @update:model-value="calculateTotal"
                />
              </div>
            </div>

            <!-- Table Select -->
            <div class="form-group mb-3">
              <label class="form-label">Стол</label>
              <select v-model="bookingForm.table_id" class="form-select" @change="calculateTotal" required>
                <option v-for="table in availableTables" :key="table.id" :value="table.id">
                  Стол {{ table.number }} ({{ table.table_description }})
                </option>
              </select>
            </div>

            <!-- Summary -->
            <div class="d-flex justify-content-between mb-3">
              <div>
                <label class="form-label">Всего часов:</label>
                <span class="ms-2">{{ totalTime }}</span>
              </div>
              <div>
                <label class="form-label">Итоговая сумма:</label>
                <span class="ms-2">{{ totalCost.toFixed(2) }} ₽</span>
              </div>
            </div>
          </div>

          <div class="modal-footer">
            <button type="button" class="btn btn-secondary" @click="$emit('close')">Закрыть</button>

            <button v-if="isAdmin" type="submit" class="btn btn-primary">
              {{ isEditMode ? 'Обновить' : 'Забронировать' }}
            </button>

            <button
              type="button"
              class="btn btn-success"
              @click="submitPayment"
              :disabled="!isFormValid"
            >
              Оплатить
            </button>
          </div>
        </form>

      </div>
    </div>
  </div>
</template>

<script>
import { ref, computed, onMounted } from 'vue'
import VueDatePicker from '@vuepic/vue-datepicker'
import '@vuepic/vue-datepicker/dist/main.css'

export default {
  components: {
    VueDatePicker
  },
  props: {
    selectedSlot: {
      type: Object,
      required: true
    },
    availableTables: {
      type: Array,
      default: () => []
    },
    isAdmin: {
      type: Boolean,
      default: false
    }
  },
  emits: ['close', 'submit', 'payment'],
  setup(props, { emit }) {
    const bookingForm = ref({
      title: '',
      description: '',
      start_time: null,
      end_time: null,
      table_id: null,
      total_cost: 0,
      total_time: 0
    })

    const totalCost = ref(0)
    const totalTime = ref(0)

    const isEditMode = computed(() => !!props.selectedSlot?.event)

    onMounted(() => {
      const { selectedSlot, availableTables } = props

      if (selectedSlot) {
        bookingForm.value.start_time = selectedSlot.start
        bookingForm.value.end_time = selectedSlot.end

        if (selectedSlot.event) {
          const event = selectedSlot.event
          bookingForm.value = {
            title: event.title,
            description: event.description,
            start_time: new Date(event.start_time),
            end_time: new Date(event.end_time),
            table_id: event.table.id,
            total_cost: event.total_cost,
            total_time: event.total_time
          }
          totalCost.value = event.total_cost
          totalTime.value = event.total_time
        }

        if (availableTables.length === 1) {
          bookingForm.value.table_id = availableTables[0].id
        }
      }
    })

    const isFormValid = computed(() => {
      const form = bookingForm.value
      return form.title && form.start_time && form.end_time && form.table_id
    })

    function calculateTotal() {
      const { start_time, end_time, table_id } = bookingForm.value

      if (!start_time || !end_time || !table_id) return

      const start = new Date(start_time)
      const end = new Date(end_time)
      const diffMs = end - start
      const diffHours = diffMs / (1000 * 60 * 60)

      totalTime.value = Math.round(diffHours * 2) / 2

      const selectedTable = props.availableTables.find(t => t.id === table_id)
      if (!selectedTable) return

      totalCost.value = Math.floor(totalTime.value) * selectedTable.price_per_hour
        + (totalTime.value % 1 !== 0 ? selectedTable.price_per_half_hour : 0)

      bookingForm.value.total_cost = totalCost.value
      bookingForm.value.total_time = totalTime.value
    }

    function submitBooking() {
      emit('submit', {
        ...bookingForm.value,
        start_time: bookingForm.value.start_time.toISOString(),
        end_time: bookingForm.value.end_time.toISOString()
      })
    }

    function submitPayment() {
      emit('payment', {
        ...bookingForm.value,
        start_time: bookingForm.value.start_time.toISOString(),
        end_time: bookingForm.value.end_time.toISOString()
      })
    }

    return {
      bookingForm,
      totalCost,
      totalTime,
      isEditMode,
      isFormValid,
      calculateTotal,
      submitBooking,
      submitPayment
    }
  }
}
</script>
