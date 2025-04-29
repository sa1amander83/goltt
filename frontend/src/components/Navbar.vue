<template>
  <header class="app-header">
    <RouterLink class="app-header__logo" to="/calendar">Table tennis</RouterLink>
    <a class="app-sidebar__toggle" href="#" @click="$emit('toggleSidebar')" aria-label="Hide Sidebar"></a>

    <ul class="app-nav">
      <template v-if="user.is_authenticated">
        <li>
          <div v-if="messages.length" class="container mt-3">
            <p v-for="(msg, index) in messages" :key="index"
               class="alert alert-danger bg-light text-danger text-center font-weight-bold text-lg-center">
              <i class="fa fa-exclamation-triangle"></i> {{ msg }}
            </p>
          </div>
        </li>
        <li><p class="mt-2 mr-3">{{ user.email }}</p></li>
        <li>
          <RouterLink class="dropdown-item mt-2" to="/logout">
            <i class="fa fa-sign-out fa-lg"></i> Выйти
          </RouterLink>
        </li>
      </template>

      <template v-else>
        <li>
          <RouterLink class="dropdown-item mt-2" to="/login">
            <i class="fa fa-sign-in fa-lg"></i> Войти
          </RouterLink>
        </li>
        <li class="ml-3">
          <RouterLink class="dropdown-item mt-2" to="/register">
            <i class="fa fa-user-plus fa-md"></i> Регистрация
          </RouterLink>
        </li>
      </template>
    </ul>
  </header>
</template>

<script>
export default {
  props: {
    user: {
      type: Object,
      required: true
    },
    messages: {
      type: Array,
      default: () => []
    }
  }
};
</script>

<style scoped>
/* При необходимости стилизуйте */
</style>
