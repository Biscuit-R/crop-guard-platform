<template>
  <div class="main-layout">
    <header class="header">
      <slot name="header"></slot>
    </header>
    <main class="content">
      <slot name="content"></slot>
    </main>
    <nav class="bottom-nav">
      <slot name="sidebar"></slot>
    </nav>
  </div>
</template>

<script setup>
</script>

<style scoped>
.main-layout {
  height: 100vh;
  overflow: hidden;
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
