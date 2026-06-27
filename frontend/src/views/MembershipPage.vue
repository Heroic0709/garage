<template>
  <div class="page-wrap">
    <div class="member-card" v-if="!isMember">
      <div class="member-icon">
        <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><path d="M12 2L2 7l10 5 10-5-10-5zM2 17l10 5 10-5M2 12l10 5 10-5"/></svg>
      </div>
      <h3>开通会员享优惠</h3>
      <p>会员停车费仅 {{ memberRate }} 元/小时，每月 {{ monthlyFee }} 元</p>
      <el-button type="primary" size="large" @click="handleActivate" :loading="activating">立即开通</el-button>
      <small class="hint">将从钱包余额扣款，请确保余额充足</small>
    </div>

    <div class="member-card member-active" v-else>
      <div class="member-badge">会员</div>
      <div class="member-icon">
        <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><path d="M12 2L2 7l10 5 10-5-10-5zM2 17l10 5 10-5M2 12l10 5 10-5"/></svg>
      </div>
      <h3>您已是会员</h3>
      <p>到期时间：<strong>{{ expireAt }}</strong></p>
      <p>停车费率：<strong>{{ memberRate }} 元/小时</strong></p>
      <el-button type="primary" size="large" @click="handleActivate" :loading="activating">续费会员 ({{ monthlyFee }} 元/月)</el-button>
      <small class="hint">续费后到期时间自动延长 30 天</small>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { getMembershipStatus, activateMembership } from '../api/membership'

const isMember = ref(false)
const expireAt = ref('')
const memberRate = ref(3)
const monthlyFee = ref(20)
const activating = ref(false)

async function fetchStatus() {
  try {
    const res = await getMembershipStatus()
    isMember.value = res.data.is_member
    expireAt.value = res.data.expire_at?.slice(0, 10) || ''
    memberRate.value = res.data.member_rate
    monthlyFee.value = res.data.monthly_fee
  } catch {}
}

async function handleActivate() {
  activating.value = true
  try {
    const res = await activateMembership()
    ElMessage.success(res.data.message)
    fetchStatus()
  } finally {
    activating.value = false
  }
}

onMounted(fetchStatus)
</script>

<style scoped>
.page-wrap { max-width: 500px; margin: 0 auto; }
.member-card {
  background: #131822;
  border: 1px solid #252C3A;
  border-radius: 16px;
  padding: 40px 32px;
  text-align: center;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 12px;
}
.member-active {
  border-color: rgba(34,197,94,0.3);
  background: linear-gradient(135deg, rgba(34,197,94,0.04), rgba(79,140,255,0.04));
}
.member-icon { color: #4F8CFF; }
.member-badge {
  background: linear-gradient(135deg, #22C55E, #16A34A);
  color: #fff;
  font-size: 12px;
  font-weight: 700;
  padding: 4px 14px;
  border-radius: 20px;
  letter-spacing: 1px;
}
h3 { font-size: 18px; color: #E2E6ED; margin: 0; }
p { font-size: 14px; color: #7C8496; margin: 0; }
p strong { color: #E2E6ED; }
.hint { font-size: 12px; color: #5C6378; }

@media (max-width: 768px) {
  .page-wrap { max-width: 100%; padding: 0 4px; }
  .member-card { padding: 28px 20px; }
}
</style>
