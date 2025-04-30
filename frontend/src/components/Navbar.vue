<template>
  <nav class="navbar navbar-expand-lg navbar-dark bg-primary">
    <div class="container-fluid">
      <router-link class="navbar-brand" to="/">
        <i class="fas fa-calendar-alt me-2"></i>Бронирование столов
      </router-link>
      <button
        class="navbar-toggler"
        type="button"
        @click="toggleMenu"
      >
        <span class="navbar-toggler-icon"></span>
      </button>
      <div class="collapse navbar-collapse" :class="{ show: menuOpen }">
        <ul class="navbar-nav me-auto">
          <li class="nav-item">
            <router-link class="nav-link" to="/">
              <i class="fas fa-home me-1"></i>Главная
            </router-link>
          </li>
          <li class="nav-item">
            <router-link class="nav-link" to="/tables">
              <i class="fas fa-table me-1"></i>Столы
            </router-link>
          </li>
        </ul>
        <div class="d-flex">
          <div v-if="isAuthenticated" class="dropdown">
            <button class="btn btn-outline-light dropdown-toggle" type="button" id="userDropdown" data-bs-toggle="dropdown">
              <i class="fas fa-user me-1"></i>{{ userEmail }}
            </button>
            <ul class="dropdown-menu dropdown-menu-end">
              <li><router-link class="dropdown-item" to="/profile">Профиль</router-link></li>
              <li><hr class="dropdown-divider"></li>
              <li><button class="dropdown-item" @click="logout">Выйти</button></li>
            </ul>
          </div>
          <router-link v-else class="btn btn-outline-light" to="/login">
            Войти
          </router-link>
        </div>
      </div>
    </div>
  </nav>
</template>

<script setup>
import { computed, ref } from 'vue'
import { useStore } from 'vuex'
import { useRouter } from 'vue-router'

const store = useStore()
const router = useRouter()
const menuOpen = ref(false)

const isAuthenticated = computed(() => store.getters.isAuthenticated)
const userEmail = computed(() => store.getters.userEmail)

const toggleMenu = () => {
  menuOpen.value = !menuOpen.value
}

const logout = async () => {
  await store.dispatch('logout')
  router.push('/login')
}
</script>

<style scoped>
.navbar {
  box-shadow: 0 2px 10px rgba(0, 0, 0, 0.1);
}

.navbar-brand {
  font-weight: 600;
}

.nav-link {
  display: flex;
  align-items: center;
}

@media (max-width: 992px) {
  .navbar-collapse {
    padding-top: 15px;
  }
}
</style>
