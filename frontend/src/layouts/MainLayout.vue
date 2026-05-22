<template>
  <div class="main-layout" :class="{ 'landscape': isLandscape, 'portrait': !isLandscape }">
    <template v-if="isLandscape">
      <aside class="sidebar">
        <slot name="sidebar"></slot>
      </aside>
      <div class="main-container">
        <header class="header">
          <slot name="header"></slot>
        </header>
        <main class="content">
          <slot name="content"></slot>
        </main>
      </div>
    </template>

    <template v-else>
      <header class="header">
        <slot name="header"></slot>
      </header>
      <main class="content">
        <slot name="content"></slot>
      </main>
      <nav class="bottom-nav">
        <slot name="sidebar"></slot>
      </nav>
    </template>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted } from "vue";

const isLandscape = ref(window.innerWidth >= 900 && window.innerWidth > window.innerHeight);

const checkOrientation = () => {
  isLandscape.value = window.innerWidth >= 900 && window.innerWidth > window.innerHeight;
};

onMounted(() => window.addEventListener("resize", checkOrientation));
onUnmounted(() => window.removeEventListener("resize", checkOrientation));
</script>

<style scoped>
.main-layout {
  height: 100vh;
  overflow: hidden;
}

.landscape {
  display: flex;
}

.landscape .sidebar {
  width: 220px;
  background-color: #ffffff;
  border-right: 1px solid var(--border-color);
  display: flex;
  flex-direction: column;
  flex-shrink: 0;
}

.landscape .main-container {
  flex: 1;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.portrait {
  display: flex;
  flex-direction: column;
}

.header {
  height: 64px;
  background-color: #ffffff;
  border-bottom: 1px solid var(--border-color);
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 24px;
  flex-shrink: 0;
}

.content {
  flex: 1;
  padding: 24px 32px;
  overflow-y: auto;
  background-color: #f0fdfa;
}

.bottom-nav {
  height: 64px;
  background-color: #ffffff;
  border-top: 1px solid var(--border-color);
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}
</style>
