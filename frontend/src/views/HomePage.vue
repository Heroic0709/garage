<template>
  <div class="dashboard">
    <!-- Stats Cards (admin only) -->
    <div class="stats-grid" v-if="isAdmin">
      <div class="stat-card">
        <div class="stat-icon stat-icon--blue">
          <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="2" y="4" width="20" height="16" rx="2"/><path d="M12 9v5M9 12h6"/></svg>
        </div>
        <div class="stat-info">
          <div class="stat-value">{{ stats.today_income }}</div>
          <div class="stat-label">今日收入 (元)</div>
        </div>
      </div>
      <div class="stat-card">
        <div class="stat-icon stat-icon--purple">
          <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="2" y="4" width="20" height="16" rx="2"/><path d="M2 10h20"/></svg>
        </div>
        <div class="stat-info">
          <div class="stat-value">{{ stats.month_income }}</div>
          <div class="stat-label">本月收入 (元)</div>
        </div>
      </div>
      <div class="stat-card">
        <div class="stat-icon stat-icon--green">
          <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="9"/><path d="M12 7v5l3 3"/></svg>
        </div>
        <div class="stat-info">
          <div class="stat-value">{{ stats.total_income }}</div>
          <div class="stat-label">总收入 (元)</div>
        </div>
      </div>
      <div class="stat-card">
        <div class="stat-icon stat-icon--amber">
          <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="3" y="3" width="18" height="18" rx="3"/><path d="M9 9h6M9 13h6M9 17h4"/></svg>
        </div>
        <div class="stat-info">
          <div class="stat-value">{{ stats.parked_count }}</div>
          <div class="stat-label">当前在场 (辆)</div>
        </div>
      </div>
    </div>

    <!-- Welcome Banner (non-admin) -->
    <div class="welcome-banner" v-else>
      <div class="welcome-icon">
        <svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="3" y="3" width="18" height="18" rx="3"/><path d="M9 9h6M9 13h6M9 17h4"/></svg>
      </div>
      <div class="welcome-text">
        <h3>欢迎使用停车场智能管控系统</h3>
        <p>选择下方功能开始操作</p>
      </div>
    </div>

    <!-- Quick Actions -->
    <div class="section-title">快捷操作</div>
    <div class="quick-actions">
      <div class="action-card" @click="$router.push('/app/entry')">
        <div class="action-ring">
          <svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><circle cx="12" cy="12" r="9"/><path d="M12 8v8M8 12h8"/></svg>
        </div>
        <span>车辆入场</span>
        <small>识别车牌并登记</small>
      </div>
      <div class="action-card" @click="$router.push('/app/pay')">
        <div class="action-ring">
          <svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><circle cx="12" cy="12" r="9"/><path d="M12 10v4M12 15.5v.5"/></svg>
        </div>
        <span>停车缴费</span>
        <small>查询费用并结算</small>
      </div>
      <div class="action-card" @click="$router.push('/app/exit')">
        <div class="action-ring">
          <svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><circle cx="12" cy="12" r="9"/><path d="M16 8l-8 8M8 8l8 8"/></svg>
        </div>
        <span>车辆出场</span>
        <small>核验缴费状态</small>
      </div>
      <div class="action-card" @click="$router.push('/app/membership')">
        <div class="action-ring">
          <svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><path d="M12 15l-2 5l-3-1l1-4M17.6 18.6a9 9 0 10-12.8 1.2"/><circle cx="12" cy="9" r="2"/></svg>
        </div>
        <span>会员中心</span>
        <small>开通会员享优惠</small>
      </div>
      <div class="action-card" v-if="isAdmin" @click="$router.push('/app/admin')">
        <div class="action-ring">
          <svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><path d="M4 21v-7M4 10V3M12 21v-9M12 8V3M20 21v-5M20 12V3"/><path d="M1 14h6M9 8h6M17 16h6"/></svg>
        </div>
        <span>管理后台</span>
        <small>记录与统计</small>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { getStatistics } from '../api/admin'

const stats = ref({ today_income: 0, month_income: 0, total_income: 0, parked_count: 0 })

const isAdmin = computed(() => {
  try { return JSON.parse(localStorage.getItem('user') || '{}').role === 'admin' }
  catch { return false }
})

onMounted(async () => {
  if (isAdmin.value) {
    try { const res = await getStatistics(); stats.value = res.data } catch (e) {}
  }
})
</script>

<style scoped>
.dashboard { max-width: 900px; margin: 0 auto; }

/* Stats */
.stats-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 16px;
  margin-bottom: 32px;
}
.stat-card {
  background: #131822;
  border: 1px solid #252C3A;
  border-radius: 12px;
  padding: 20px;
  display: flex;
  align-items: center;
  gap: 16px;
  transition: border-color 0.2s, box-shadow 0.2s;
}
.stat-card:hover {
  border-color: #2D3548;
  box-shadow: 0 2px 12px rgba(0,0,0,0.2);
}
/* Welcome Banner */
.welcome-banner {
  background: #131822;
  border: 1px solid #252C3A;
  border-radius: 12px;
  padding: 32px;
  display: flex;
  align-items: center;
  gap: 16px;
  margin-bottom: 32px;
}
.welcome-icon {
  width: 56px; height: 56px;
  border-radius: 12px;
  background: rgba(79,140,255,0.1);
  display: flex; align-items: center; justify-content: center;
  color: #4F8CFF;
  flex-shrink: 0;
}
.welcome-text h3 {
  font-size: 16px; font-weight: 600; color: #E2E6ED; margin: 0;
}
.welcome-text p {
  font-size: 13px; color: #7C8496; margin: 4px 0 0;
}
.stat-icon {
  width: 48px; height: 48px;
  border-radius: 10px;
  display: flex; align-items: center; justify-content: center;
  flex-shrink: 0;
}
.stat-icon--blue { background: rgba(79,140,255,0.12); color: #4F8CFF; }
.stat-icon--purple { background: rgba(99,102,241,0.12); color: #818CF8; }
.stat-icon--green { background: rgba(34,197,94,0.12); color: #22C55E; }
.stat-icon--amber { background: rgba(245,158,11,0.12); color: #F59E0B; }
.stat-info { display: flex; flex-direction: column; }
.stat-value {
  font-size: 28px; font-weight: 700; color: #E2E6ED;
  font-variant-numeric: tabular-nums;
  line-height: 1.2;
}
.stat-label { font-size: 12px; color: #5C6378; margin-top: 2px; font-weight: 500; }

/* Quick Actions */
.section-title {
  font-size: 15px; font-weight: 600; color: #B0B8C8;
  margin-bottom: 16px;
  letter-spacing: 0.5px;
}
.quick-actions {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 16px;
}
.action-card {
  background: #131822;
  border: 1px solid #252C3A;
  border-radius: 12px;
  padding: 24px 16px;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 8px;
  cursor: pointer;
  transition: all 0.25s ease;
}
.action-card:hover {
  border-color: #4F8CFF;
  box-shadow: 0 0 20px rgba(79,140,255,0.08);
  transform: translateY(-2px);
}
.action-ring {
  width: 56px; height: 56px;
  border-radius: 50%;
  background: rgba(79,140,255,0.08);
  border: 1px solid rgba(79,140,255,0.15);
  display: flex; align-items: center; justify-content: center;
  color: #4F8CFF;
  transition: all 0.25s ease;
}
.action-card:hover .action-ring {
  background: rgba(79,140,255,0.15);
  border-color: rgba(79,140,255,0.3);
  box-shadow: 0 0 16px rgba(79,140,255,0.12);
}
.action-card span {
  font-size: 14px; font-weight: 600; color: #E2E6ED;
}
.action-card small {
  font-size: 12px; color: #5C6378; font-weight: 400;
}

@media (max-width: 768px) {
  .stats-grid { grid-template-columns: repeat(2, 1fr); gap: 10px; }
  .stat-card { padding: 14px; gap: 10px; }
  .stat-icon { width: 38px; height: 38px; }
  .stat-value { font-size: 22px; }
  .quick-actions { grid-template-columns: repeat(2, 1fr); gap: 10px; }
  .action-card { padding: 16px 10px; }
  .action-ring { width: 44px; height: 44px; }
  .action-ring svg { width: 22px; height: 22px; }
}

@media (max-width: 480px) {
  .welcome-banner { flex-direction: column; text-align: center; padding: 24px; }
  .welcome-icon { width: 44px; height: 44px; }
  .quick-actions { grid-template-columns: repeat(2, 1fr); gap: 8px; }
  .action-card { padding: 14px 8px; }
  .action-card span { font-size: 13px; }
}
</style>
