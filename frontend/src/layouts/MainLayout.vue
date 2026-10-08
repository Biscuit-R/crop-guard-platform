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
  background-color: #fffdf7;
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
  position: relative;
}

.content::before {
  content: '';
  position: fixed;
  top: 0; left: 0; right: 0; bottom: 0;
  background: url('/main-bg.jpg') no-repeat center center;
  background-size: cover;
  z-index: -2;
}

.content::after {
  content: '';
  position: fixed;
  top: 0; left: 0; right: 0; bottom: 0;
  background: rgba(254, 249, 239, 0.28);
  backdrop-filter: blur(4px);
  -webkit-backdrop-filter: blur(4px);
  z-index: -1;
}

.bottom-nav {
  height: 64px;
  background-color: #fffdf7;
  border-top: 1px solid var(--border-color);
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}
</style>
