<template>
  <div class="shell">
    <!-- Mobile overlay backdrop -->
    <div v-if="sidebarOpen" class="sidebar-overlay" @click="sidebarOpen = false"></div>

    <aside class="sidebar" :class="{ 'sidebar-open': sidebarOpen }">
      <div class="sidebar-brand" @click="$router.push('/app/home')">
        <div class="brand-icon">
          <svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <rect x="3" y="3" width="18" height="18" rx="3"/>
            <path d="M9 9h6M9 13h6M9 17h4"/>
          </svg>
        </div>
        <div class="brand-text">
          <span class="brand-name">车场管控</span>
          <span class="brand-sub">Parking Control</span>
        </div>
      </div>

      <nav class="sidebar-nav">
        <router-link v-for="item in navItems" :key="item.path" :to="item.path" class="nav-item" active-class="nav-item--active" @click="sidebarOpen = false">
          <span class="nav-icon">
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">
              <path :d="item.icon" />
            </svg>
          </span>
          <span class="nav-label">{{ item.label }}</span>
          <span class="nav-dot"></span>
        </router-link>
      </nav>

      <div class="sidebar-footer">
        <div class="status-indicator">
          <span class="status-dot"></span>
          <span class="status-text">系统运行中</span>
        </div>
      </div>
    </aside>

    <main class="main-content">
      <div class="content-header">
        <div class="header-left">
          <button class="hamburger" @click="sidebarOpen = !sidebarOpen">
            <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round">
              <path d="M3 6h18M3 12h18M3 18h18"/>
            </svg>
          </button>
          <h1 class="page-title">{{ $route.meta.title }}</h1>
        </div>
        <div class="header-actions">
          <div class="header-time">{{ currentTime }}</div>
          <div class="header-user">
            <span class="user-avatar">{{ user.username?.charAt(0).toUpperCase() }}</span>
            <span class="user-name">{{ user.username }}</span>
            <span class="user-role">{{ user.role === 'admin' ? '管理员' : '普通用户' }}</span>
          </div>
          <button class="logout-btn" @click="handleLogout" title="退出登录">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M9 21H5a2 2 0 01-2-2V5a2 2 0 012-2h4M16 17l5-5-5-5M21 12H9"/></svg>
          </button>
        </div>
      </div>
      <div class="content-body">
        <router-view />
      </div>
    </main>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onBeforeUnmount } from 'vue'
import { useRouter } from 'vue-router'

const router = useRouter()

const sidebarOpen = ref(false)

const user = computed(() => {
  try { return JSON.parse(localStorage.getItem('user') || '{}') }
  catch { return {} }
})

const navItems = computed(() => {
  const items = [
    { label: '首页概览', path: '/app/home', icon: 'M3 12l2-2m0 0l7-7 7 7M5 10v10a1 1 0 001 1h3m10-11l2 2m-2-2v10a1 1 0 01-1 1h-3m-4 0a1 1 0 01-1-1v-4a1 1 0 011-1h2a1 1 0 011 1v4a1 1 0 01-1 1' },
    { label: '车辆入场', path: '/app/entry', icon: 'M12 5v14M5 12h14M7 7l5-5 5 5M5 5l5 5' },
    { label: '停车缴费', path: '/app/pay', icon: 'M12 2a9 9 0 110 18 9 9 0 010-18zm0 2a7 7 0 100 14 7 7 0 000-14zm0 3v4M12 15h.01' },
    { label: '车辆出场', path: '/app/exit', icon: 'M13 7l5 5m0 0l-5 5m5-5H6M9 4V3m6 3V3m-9 9H3m18 0h-2' },
    { label: '会员中心', path: '/app/membership', icon: 'M12 2L2 7l10 5 10-5-10-5z M2 17l10 5 10-5 M2 12l10 5 10-5' },
    { label: '我的钱包', path: '/app/wallet', icon: 'M21 12a9 9 0 01-9 9m9-9a9 9 0 00-9-9m9 9H3m9-9a9 9 0 019 9m-9-9c-2.67 0-5 4.03-5 9s2.33 9 5 9m0-18c2.67 0 5 4.03 5 9s-2.33 9-5 9' },
  ]
  if (user.value.role === 'admin') {
    items.push({ label: '黑名单管理', path: '/app/blacklist', icon: 'M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zM4 12c0-4.42 3.58-8 8-8 1.85 0 3.55.63 4.9 1.69L5.69 16.9C4.63 15.55 4 13.85 4 12zm8 8c-1.85 0-3.55-.63-4.9-1.69L18.31 7.1C19.37 8.45 20 10.15 20 12c0 4.42-3.58 8-8 8z' })
    items.push({ label: '管理后台', path: '/app/admin', icon: 'M12 15a3 3 0 100-6 3 3 0 000 6zM19.4 15a1.65 1.65 0 00.33 1.82l.06.06a2 2 0 010 2.83 2 2 0 01-2.83 0l-.06-.06a1.65 1.65 0 00-1.82-.33 1.65 1.65 0 00-1 1.51V21a2 2 0 01-4 0v-.09A1.65 1.65 0 009 19.4a1.65 1.65 0 00-1.82.33l-.06.06a2 2 0 01-2.83-2.83l.06-.06A1.65 1.65 0 004.68 15a1.65 1.65 0 00-1.51-1H3a2 2 0 010-4h.09A1.65 1.65 0 004.6 9a1.65 1.65 0 00-.33-1.82l-.06-.06a2 2 0 012.83-2.83l.06.06A1.65 1.65 0 009 4.68a1.65 1.65 0 001-1.51V3a2 2 0 014 0v.09a1.65 1.65 0 001 1.51 1.65 1.65 0 001.82-.33l.06-.06a2 2 0 012.83 2.83l-.06.06A1.65 1.65 0 0019.4 9a1.65 1.65 0 001.51 1H21a2 2 0 010 4h-.09a1.65 1.65 0 00-1.51 1z' })
  }
  return items
})

function handleLogout() {
  localStorage.removeItem('token')
  localStorage.removeItem('user')
  router.push('/login')
}

const currentTime = ref('')

let timer = null
onMounted(() => {
  const update = () => {
    const now = new Date()
    currentTime.value = now.toLocaleString('zh-CN', { hour: '2-digit', minute: '2-digit', second: '2-digit', year: 'numeric', month: '2-digit', day: '2-digit' })
  }
  update()
  timer = setInterval(update, 1000)
})
onBeforeUnmount(() => clearInterval(timer))
</script>

<style>
/* ==================== Global Reset ==================== */
* { margin: 0; padding: 0; box-sizing: border-box; }
body {
  font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
  background: #0B0F15;
  color: #E2E6ED;
  -webkit-font-smoothing: antialiased;
  overflow: hidden;
}

/* Element Plus dark theme overrides */
:root {
  --el-bg-color: #131822;
  --el-bg-color-overlay: #1A1F2B;
  --el-border-color: #252C3A;
  --el-border-color-light: #1E2432;
  --el-text-color-primary: #E2E6ED;
  --el-text-color-regular: #B0B8C8;
  --el-text-color-secondary: #7C8496;
  --el-fill-color-blank: #131822;
  --el-color-primary: #4F8CFF;
  --el-color-primary-light-3: #3A6FD9;
  --el-color-primary-light-5: #2E5AB5;
  --el-color-primary-light-7: #234691;
  --el-color-primary-light-9: #1A346D;
  --el-color-primary-dark-2: #6BA1FF;
  --el-color-success: #22C55E;
  --el-color-warning: #F59E0B;
  --el-color-danger: #EF4444;
  --el-disabled-bg-color: #1A1F2B;
  --el-disabled-text-color: #4A5168;
  --el-disabled-border-color: #252C3A;
  --el-input-bg-color: #0F131D;
  --el-input-border-color: #252C3A;
  --el-overlay-color-lighter: rgba(0, 0, 0, 0.5);
}

.el-card {
  background: #131822 !important;
  border: 1px solid #252C3A !important;
  border-radius: 12px !important;
  color: #E2E6ED !important;
}
.el-button--primary {
  background: linear-gradient(135deg, #4F8CFF, #3B6FE0) !important;
  border: none !important;
  font-weight: 500 !important;
  letter-spacing: 0.5px !important;
}
.el-button--primary:hover {
  background: linear-gradient(135deg, #6BA1FF, #4F8CFF) !important;
  box-shadow: 0 4px 16px rgba(79, 140, 255, 0.3) !important;
}
.el-button--success {
  background: linear-gradient(135deg, #22C55E, #16A34A) !important;
  border: none !important;
}
.el-result__title { color: #E2E6ED !important; }
.el-result__subtitle { color: #B0B8C8 !important; }
.el-table {
  --el-table-bg-color: #131822 !important;
  --el-table-tr-bg-color: #131822 !important;
  --el-table-header-bg-color: #1A1F2B !important;
  --el-table-border-color: #252C3A !important;
  --el-table-text-color: #E2E6ED !important;
  --el-table-header-text-color: #B0B8C8 !important;
  --el-table-row-hover-bg-color: #1C2230 !important;
}
.el-table th { border-bottom: 1px solid #252C3A !important; }
.el-table td { border-bottom: 1px solid #1E2432 !important; }
.el-table--striped .el-table__body tr.el-table__row--striped td {
  background: #161C28 !important;
}
.el-table .el-table__body tr:hover > td {
  background: #1A2130 !important;
}
.el-upload-dragger {
  background: #0F131D !important;
  border: 2px dashed #252C3A !important;
  border-radius: 12px !important;
}
.el-upload-dragger:hover {
  border-color: #4F8CFF !important;
}
.el-alert--warning { background: rgba(245, 158, 11, 0.1) !important; border-color: rgba(245, 158, 11, 0.2) !important; }
.el-alert--warning .el-alert__title { color: #F59E0B !important; }
.el-tag--success { background: rgba(34, 197, 94, 0.15) !important; border-color: rgba(34, 197, 94, 0.3) !important; color: #22C55E !important; }
.el-tag--warning { background: rgba(245, 158, 11, 0.15) !important; border-color: rgba(245, 158, 11, 0.3) !important; color: #F59E0B !important; }
.el-tag--info { background: rgba(124, 132, 150, 0.15) !important; border-color: rgba(124, 132, 150, 0.3) !important; color: #9CA3B4 !important; }
.el-pagination button, .el-pager li { background: #131822 !important; color: #B0B8C8 !important; }
.el-pager li.active { background: #4F8CFF !important; }
.el-input__wrapper { background: #0F131D !important; box-shadow: 0 0 0 1px #252C3A !important; }
.el-select .el-input__wrapper { background: #0F131D !important; }

.el-message { background: #1A1F2B !important; border-color: #252C3A !important; }
.el-message .el-message__content { color: #E2E6ED !important; }

.el-radio-group { --el-radio-button-bg-color: #131822; }
.el-radio-button__inner { background: #131822 !important; border-color: #252C3A !important; color: #B0B8C8 !important; }
.el-radio-button__inner:hover { color: #4F8CFF !important; }
.el-radio-button.is-active .el-radio-button__inner {
  background: rgba(79, 140, 255, 0.15) !important;
  border-color: #4F8CFF !important;
  color: #4F8CFF !important;
  box-shadow: none !important;
}

/* ==================== Responsive helpers ==================== */
@media (max-width: 768px) {
  body { overflow: hidden auto; }
  .stats-row { grid-template-columns: repeat(2, 1fr) !important; }
  .el-dialog { width: 92% !important; }
  .el-table { font-size: 12px; }
  .filter-bar { flex-wrap: wrap; }
}
@media (max-width: 480px) {
  .stats-row { grid-template-columns: repeat(2, 1fr) !important; gap: 8px; }
  .mini-stat { padding: 12px; }
  .ms-value { font-size: 20px; }
}
</style>

<style scoped>
.shell {
  display: flex;
  height: 100vh;
  width: 100vw;
  overflow: hidden;
}

/* ==================== Sidebar ==================== */
.sidebar {
  width: 240px;
  min-width: 240px;
  background: #0C1019;
  border-right: 1px solid #1A1F2B;
  display: flex;
  flex-direction: column;
  padding: 0;
  position: relative;
  z-index: 10;
}
.sidebar::after {
  content: '';
  position: absolute;
  top: 0; right: 0; bottom: 0;
  width: 1px;
  background: linear-gradient(180deg, transparent, rgba(79, 140, 255, 0.15), transparent);
}

.sidebar-brand {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 20px 20px 24px;
  cursor: pointer;
  border-bottom: 1px solid #1A1F2B;
}
.brand-icon {
  width: 40px; height: 40px;
  background: linear-gradient(135deg, #4F8CFF, #6366F1);
  border-radius: 10px;
  display: flex; align-items: center; justify-content: center;
  color: #fff;
  flex-shrink: 0;
}
.brand-text { display: flex; flex-direction: column; gap: 1px; }
.brand-name { font-size: 16px; font-weight: 700; color: #E2E6ED; letter-spacing: 1px; }
.brand-sub { font-size: 10px; color: #5C6378; text-transform: uppercase; letter-spacing: 1.5px; font-weight: 500; }

.sidebar-nav {
  flex: 1;
  padding: 12px 12px;
  display: flex;
  flex-direction: column;
  gap: 2px;
}
.nav-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px 14px;
  border-radius: 8px;
  color: #7C8496;
  text-decoration: none;
  font-size: 14px;
  font-weight: 500;
  position: relative;
  transition: all 0.2s ease;
}
.nav-item:hover {
  background: rgba(79, 140, 255, 0.06);
  color: #B0B8C8;
}
.nav-item--active {
  background: rgba(79, 140, 255, 0.1) !important;
  color: #4F8CFF !important;
}
.nav-item--active .nav-dot {
  box-shadow: 0 0 8px rgba(79, 140, 255, 0.6);
}
.nav-icon {
  display: flex; align-items: center; justify-content: center;
  width: 20px; height: 20px;
  flex-shrink: 0;
}
.nav-dot {
  position: absolute;
  left: 0; top: 50%;
  transform: translateY(-50%);
  width: 3px; height: 20px;
  border-radius: 0 3px 3px 0;
  background: transparent;
  transition: all 0.2s ease;
}
.nav-item--active .nav-dot {
  background: #4F8CFF;
  height: 28px;
}

.sidebar-footer {
  padding: 16px 20px;
  border-top: 1px solid #1A1F2B;
}
.status-indicator {
  display: flex; align-items: center; gap: 8px;
}
.status-dot {
  width: 8px; height: 8px;
  border-radius: 50%;
  background: #22C55E;
  box-shadow: 0 0 6px rgba(34, 197, 94, 0.5);
  animation: pulse-status 2s infinite;
}
@keyframes pulse-status {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.5; }
}
.status-text { font-size: 12px; color: #5C6378; font-weight: 500; }

/* ==================== Main Content ==================== */
.main-content {
  flex: 1;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  min-width: 0;
}
.content-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 20px 32px 0;
  flex-shrink: 0;
}
.page-title {
  font-size: 22px;
  font-weight: 700;
  color: #E2E6ED;
  letter-spacing: -0.3px;
}
.header-time {
  font-size: 13px;
  color: #5C6378;
  font-weight: 500;
  font-variant-numeric: tabular-nums;
  font-family: 'JetBrains Mono', 'Cascadia Code', 'Consolas', monospace;
}
.header-actions {
  display: flex;
  align-items: center;
  gap: 16px;
}
.header-user {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 6px 12px;
  background: #0F131D;
  border: 1px solid #252C3A;
  border-radius: 8px;
}
.user-avatar {
  width: 28px; height: 28px;
  background: #4F8CFF;
  color: #fff;
  border-radius: 6px;
  display: flex; align-items: center; justify-content: center;
  font-size: 12px; font-weight: 700;
}
.user-name { font-size: 13px; color: #E2E6ED; font-weight: 600; }
.user-role { font-size: 11px; color: #7C8496; background: #1A2130; padding: 2px 6px; border-radius: 4px; }
.logout-btn {
  background: none; border: none; color: #5C6378; cursor: pointer;
  padding: 6px; border-radius: 6px; transition: all .15s;
  display: flex; align-items: center;
}
.logout-btn:hover { color: #EF4444; background: rgba(239,68,68,0.1); }
.content-body {
  flex: 1;
  overflow-y: auto;
  padding: 24px 32px 32px;
}
.content-body::-webkit-scrollbar {
  width: 6px;
}
.content-body::-webkit-scrollbar-track {
  background: transparent;
}
.content-body::-webkit-scrollbar-thumb {
  background: #252C3A;
  border-radius: 3px;
}

/* ==================== Mobile Responsive ==================== */
.hamburger {
  display: none;
  background: none;
  border: none;
  color: #B0B8C8;
  cursor: pointer;
  padding: 6px;
  border-radius: 6px;
}
.hamburger:hover { background: #1A1F2B; }

.header-left {
  display: flex;
  align-items: center;
  gap: 12px;
}

.sidebar-overlay {
  display: none;
}

@media (max-width: 768px) {
  .hamburger { display: flex; align-items: center; justify-content: center; }
  .sidebar-overlay {
    display: block;
    position: fixed;
    inset: 0;
    background: rgba(0, 0, 0, 0.5);
    z-index: 99;
  }
  .sidebar {
    position: fixed;
    top: 0; left: 0; bottom: 0;
    transform: translateX(-100%);
    transition: transform 0.25s ease;
    z-index: 100;
    box-shadow: 4px 0 20px rgba(0, 0, 0, 0.3);
  }
  .sidebar.sidebar-open { transform: translateX(0); }
  .content-header {
    padding: 14px 16px 0;
    flex-wrap: wrap;
    gap: 8px;
  }
  .header-left { gap: 8px; }
  .page-title { font-size: 18px; }
  .header-time { display: none; }
  .header-actions { gap: 8px; }
  .user-role { display: none; }
  .content-body { padding: 16px 12px 20px; }
}

@media (max-width: 480px) {
  .user-name { display: none; }
  .header-user { padding: 6px 8px; }
}
</style>
