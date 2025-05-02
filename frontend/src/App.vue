<template>
  <div class="app">
    <NavBar />
    <div class="main-content">
      <Sidebar :current-bookings="currentBookings" />
      <div class="content-wrapper">
        <router-view />
      </div>
    </div>
  </div>


</template>

<script setup>
import { ref, onMounted, onUnmounted } from 'vue'
import axios from 'axios'
import NavBar from '@/components/NavBar.vue'
import Sidebar from '@/components/Sidebar.vue'

const currentBookings = ref([])
const isLoading = ref(true)
const error = ref(null)
const abortController = new AbortController()

onMounted(async () => {
  try {
    const response = await axios.get('/api/events/running/', {
      signal: abortController.signal
    })
    currentBookings.value = response.data.events
  } catch (err) {
    if (!axios.isCancel(err)) {
      error.value = err.message
      console.error('Error loading events:', err)
    }
  } finally {
    isLoading.value = false
  }
})

onUnmounted(() => {
  abortController.abort()
})
</script>

<style scoped>
.app-container {
  display: flex;
  flex-direction: column;
  min-height: 100vh;
}

.main-content {
  display: flex;
  flex: 1;
}

.content-wrapper {
  flex: 1;
  padding: 20px;
  margin-left: 250px; /* Ширина сайдбара */
  transition: margin-left 0.3s;
}

@media (max-width: 992px) {
  .content-wrapper {
    margin-left: 0;
  }
}
</style>
