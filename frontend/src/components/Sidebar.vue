<template>
  <aside class="app-sidebar" v-if="user">
    <ul class="app-menu">
      <li>
        <RouterLink class="app-menu__item" to="/calendar">
          <i class="app-menu__icon fa fa-calendar"></i>
          <span class="app-menu__label">Календарь</span>
        </RouterLink>
      </li>
      <li>
        <a class="app-menu__item" href="#"><i class="app-menu__icon fa fa-users"></i><span class="app-menu__label">О клубе</span></a>
      </li>
      <li>
        <a class="app-menu__item" href="#"><i class="app-menu__icon fa fa-envelope"></i><span class="app-menu__label">Контакты</span></a>
      </li>

      <template v-if="user.is_superuser">
        <li>
          <RouterLink class="app-menu__item" to="/admin/bookings">
            <i class="app-menu__icon fa fa-dashboard"></i>
            <span class="app-menu__label">Бронирования</span>
          </RouterLink>
        </li>
        <li>
          <RouterLink class="app-menu__item" to="/admin/stats">
            <i class="app-menu__icon fa fa-bar-chart"></i>
            <span class="app-menu__label">Отчет</span>
          </RouterLink>
        </li>
        <li class="treeview">
          <a class="app-menu__item" href="#" @click.prevent="toggleEvents">
            <i class="app-menu__icon fa fa-th-list"></i>
            <span class="app-menu__label">События</span>
            <i class="treeview-indicator fa fa-angle-right"></i>
          </a>
          <ul v-if="eventsOpen" class="treeview-menu">
            <li><RouterLink class="treeview-item" to="/events/running"><i class="icon fa fa-circle-o"></i> Текущие</RouterLink></li>
            <li><RouterLink class="treeview-item" to="/events/upcoming"><i class="icon fa fa-circle-o"></i> Предстоящие</RouterLink></li>
            <li><RouterLink class="treeview-item" to="/events/completed"><i class="icon fa fa-circle-o"></i> Прошедшие</RouterLink></li>
            <li><RouterLink class="treeview-item" to="/events/all"><i class="icon fa fa-circle-o"></i> Все</RouterLink></li>
          </ul>
        </li>
        <li>
          <RouterLink class="app-menu__item" to="/admin/users">
            <i class="app-menu__icon fa fa-users"></i>
            <span class="app-menu__label">Посетители</span>
          </RouterLink>
        </li>
      </template>

      <template v-else-if="user.is_authenticated">
        <li>
          <RouterLink class="app-menu__item" to="/user/bookings">
            <i class="app-menu__icon fa fa-dashboard"></i>
            <span class="app-menu__label">Мои бронирования</span>
          </RouterLink>
        </li>
        <li class="treeview">
          <a class="app-menu__item" href="#" @click.prevent="toggleEvents">
            <i class="app-menu__icon fa fa-th-list"></i>
            <span class="app-menu__label">События</span>
            <i class="treeview-indicator fa fa-angle-right"></i>
          </a>
          <ul v-if="eventsOpen" class="treeview-menu">
            <li><RouterLink class="treeview-item" to="/events/running"><i class="icon fa fa-circle-o"></i> Текущие</RouterLink></li>
            <li><RouterLink class="treeview-item" to="/events/upcoming"><i class="icon fa fa-circle-o"></i> Предстоящие</RouterLink></li>
            <li><RouterLink class="treeview-item" to="/events/completed"><i class="icon fa fa-circle-o"></i> Прошедшие</RouterLink></li>
            <li><RouterLink class="treeview-item" to="/events/all"><i class="icon fa fa-circle-o"></i> Все</RouterLink></li>
          </ul>
        </li>
      </template>
    </ul>
  </aside>
</template>

<script>
export default {
  props: {
    user: {
      type: Object,
      required: true,
      default: () => ({})  // безопасное значение по умолчанию
    }
  },
  data() {
    return {
      eventsOpen: false
    };
  },
  methods: {
    toggleEvents() {
      this.eventsOpen = !this.eventsOpen;
    }
  }
};
</script>

<style scoped>
/* Стили при необходимости */
</style>
