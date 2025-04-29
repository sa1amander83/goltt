<template>
  <div class="container py-4">
    <h2 class="mb-4">Бронирования</h2>

    <!-- Таблица броней -->
    <table class="table table-bordered">
      <thead class="table-light">
        <tr>
          <th>Название</th>
          <th>Стол</th>
          <th>Начало</th>
          <th>Конец</th>
          <th>Стоимость</th>
          <th>Действия</th>
        </tr>
      </thead>
      <tbody>
        <tr v-for="booking in bookings" :key="booking.id">
          <td>{{ booking.title }}</td>
          <td>{{ booking.table.number }}</td>
          <td>{{ formatDate(booking.start_time) }}</td>
          <td>{{ formatDate(booking.end_time) }}</td>
          <td>{{ booking.total_cost }} ₽</td>
          <td>
            <button class="btn btn-sm btn-info me-2" @click="viewBooking(booking)">Подробнее</button>
          </td>
        </tr>
      </tbody>
    </table>

    <!-- Модальное окно просмотра -->
    <EventDetailModal
      v-if="selectedBooking"
      :booking="selectedBooking"
      :isAdmin="true"
      @close="selectedBooking = null"
      @delete="deleteBooking"
      @edit="openEditForm"
/>

    <!-- Модальное окно редактирования/создания -->
    <BookingFormModal
      v-if="showFormModal"
      :selectedSlot="editingSlot"
      :availableTables="availableTables"
      :isAdmin="true"
      @close="closeFormModal"
      @submit="saveBooking"
/>

    <!-- Кнопка для новой брони -->
    <button class="btn btn-primary mt-3" @click="createNewBooking">+ Новая бронь</button>
  </div>
</template>

<script>
import { ref } from 'vue'
import EventDetailModal from '@/components/EventDetailModal.vue'
import BookingFormModal from '@/components/BookingFormModal.vue' // предполагаем, что ты уже вынес форму

export default {
  components: {
    EventDetailModal,
    BookingFormModal
  },
  setup() {
    const bookings = ref([
      {
        id: 1,
        title: 'Встреча с клиентом',
        description: 'Важно!',
        start_time: new Date(),
        end_time: new Date(Date.now() + 60 * 60 * 1000),
        total_cost: 1000,
        total_time: 1,
        table: {
          id: 1,
          number: 5,
          price_per_hour: 1000,
          price_per_half_hour: 600
        }
      }
    ])

    const availableTables = ref([
      { id: 1, number: 5, price_per_hour: 1000, price_per_half_hour: 600 },
      { id: 2, number: 6, price_per_hour: 800, price_per_half_hour: 500 }
    ])

    const selectedBooking = ref(null)
    const showFormModal = ref(false)
    const editingSlot = ref(null)

    function formatDate(date) {
      return new Date(date).toLocaleString('ru-RU')
    }

    function viewBooking(booking) {
      selectedBooking.value = booking
    }

    function deleteBooking(id) {
      bookings.value = bookings.value.filter(b => b.id !== id)
      selectedBooking.value = null
    }

    function openEditForm(booking) {
      editingSlot.value = {
        start: booking.start_time,
        end: booking.end_time,
        event: booking
      }
      selectedBooking.value = null
      showFormModal.value = true
    }

    function createNewBooking() {
      editingSlot.value = null
      showFormModal.value = true
    }

    function saveBooking(newBooking) {
      const existing = bookings.value.find(b => b.id === newBooking.id)
      if (existing) {
        Object.assign(existing, newBooking)
      } else {
        newBooking.id = Date.now()
        bookings.value.push(newBooking)
      }
      showFormModal.value = false
    }

    function closeFormModal() {
      showFormModal.value = false
    }

    return {
      bookings,
      availableTables,
      selectedBooking,
      showFormModal,
      editingSlot,
      formatDate,
      viewBooking,
      deleteBooking,
      openEditForm,
      createNewBooking,
      saveBooking,
      closeFormModal
    }
  }
}
</script>
