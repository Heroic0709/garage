<template>
  <div class="page-wrap">
    <!-- 结果区 -->
    <template v-if="payResult">
      <div class="result-card">
        <div class="result-icon success">
          <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="9"/><path d="M8 12l3 3 5-5"/></svg>
        </div>
        <h3>缴费成功</h3>
        <div class="result-details">
          <div class="detail-row"><span>缴费金额</span><strong class="fee">¥{{ payResult.amount }}</strong></div>
          <div class="detail-row"><span>缴费时间</span><strong>{{ payResult.pay_time }}</strong></div>
        </div>
        <p class="expire-warn">请在 <strong>{{ countdownText }}</strong> 内出场，超时缴费失效</p>
        <div class="result-actions">
          <el-button type="primary" @click="$router.push('/app/exit')">前往出场</el-button>
          <el-button text @click="resetPay">继续缴费</el-button>
        </div>
      </div>
    </template>

    <!-- 查询结果 -->
    <template v-else-if="queryResult">
      <div class="fee-card">
        <div class="fee-plate">{{ queryResult.plate_number }}</div>
        <div class="fee-grid">
          <div class="fee-item"><span>入场时间</span><strong>{{ queryResult.entry_time }}</strong></div>
          <div class="fee-item"><span>已停时长</span><strong>{{ queryResult.park_hours }} 小时</strong></div>
          <div class="fee-item total"><span>应付金额</span><strong>¥{{ queryResult.amount }}</strong></div>
        </div>
        <el-button type="success" size="large" style="width:100%;margin-top:20px" :loading="payLoading" @click="doPay">确认缴费</el-button>
        <el-button text size="small" style="width:100%;margin-top:8px" @click="queryResult = null">重新查询</el-button>
      </div>
    </template>

    <!-- 输入区 -->
    <template v-else>
      <div class="plate-boxes">
        <template v-for="(ch, idx) in plateChars" :key="idx">
          <div class="plate-char-box" :class="{ active: activeIndex === idx }" @click="activeIndex = idx">{{ ch || '' }}</div>
          <div v-if="idx === 1" class="plate-dot">·</div>
        </template>
      </div>
      <div class="keyboard">
        <div class="kb-hint">{{ activeIndex === 0 ? '省份简称' : activeIndex === 1 ? '发牌机关代号' : '数字/字母' }}</div>
        <div class="kb-grid">
          <div v-for="key in currentKeys" :key="key" class="kb-key" @click="onKeyPress(key)">{{ key }}</div>
        </div>
        <div class="kb-actions">
          <div class="kb-key kb-del" @click="onDelete">删除</div>
          <div class="kb-key kb-clear" @click="onClear">清空</div>
        </div>
      </div>
      <el-button type="primary" size="large" style="width:100%;margin-top:16px" :disabled="!isPlateComplete" @click="queryFee">查询费用</el-button>
    </template>
  </div>
</template>

<script setup>
import { ref, computed, onBeforeUnmount } from 'vue'
import { ElMessage } from 'element-plus'
import { queryPayment, payFee } from '../api/payment'

const pKeys = '京津沪渝冀豫云辽黑湘皖鲁新苏浙赣鄂桂甘晋蒙陕吉闽贵粤川青藏琼宁'.split('')
const lKeys = 'ABCDEFGHJKLMNPQRSTUVWXYZ'.split('')
const mKeys = '1234567890ABCDEFGHJKLMNPQRSTUVWXYZ'.split('')

const plateChars = ref(['', '', '', '', '', '', ''])
const activeIndex = ref(0)
const queryResult = ref(null)
const payResult = ref(null)
const payLoading = ref(false)
let timer = null
const countdownSeconds = ref(0)

const currentKeys = computed(() => activeIndex.value === 0 ? pKeys : activeIndex.value === 1 ? lKeys : mKeys)
const isPlateComplete = computed(() => plateChars.value.every(ch => ch !== ''))
const countdownText = computed(() => {
  const m = Math.floor(countdownSeconds.value / 60)
  const s = countdownSeconds.value % 60
  return `${m}分${s.toString().padStart(2, '0')}秒`
})

function getFullPlate() { return plateChars.value[0] + plateChars.value[1] + '·' + plateChars.value.slice(2).join('') }
function onKeyPress(k) { plateChars.value[activeIndex.value] = k; if (activeIndex.value < 6) activeIndex.value++ }
function onDelete() { plateChars.value[activeIndex.value] = ''; if (activeIndex.value > 0) activeIndex.value-- }
function onClear() { plateChars.value = ['', '', '', '', '', '', '']; activeIndex.value = 0 }

async function queryFee() {
  try {
    const res = await queryPayment(getFullPlate())
    queryResult.value = { ...res.data, entry_time: new Date(res.data.entry_time).toLocaleString() }
    ElMessage.success('查询成功')
  } catch (e) { queryResult.value = null }
}

async function doPay() {
  payLoading.value = true
  try {
    const res = await payFee(getFullPlate())
    payResult.value = { ...res.data, pay_time: new Date(res.data.pay_time).toLocaleString() }
    countdownSeconds.value = res.data.expire_minutes * 60
    timer = setInterval(() => { if (countdownSeconds.value > 0) countdownSeconds.value--; else { clearInterval(timer); timer = null } }, 1000)
    ElMessage.success('缴费成功')
  } catch (e) {} finally { payLoading.value = false }
}

function resetPay() {
  queryResult.value = null; payResult.value = null; onClear()
  if (timer) { clearInterval(timer); timer = null }
}

onBeforeUnmount(() => { if (timer) clearInterval(timer) })
</script>

<style scoped>
.page-wrap { max-width: 480px; margin: 0 auto; }

/* Success */
.result-card { text-align: center; padding: 24px 0; }
.result-icon { width: 80px; height: 80px; border-radius: 50%; display: flex; align-items: center; justify-content: center; margin: 0 auto 16px; }
.result-icon.success { background: rgba(34,197,94,0.1); color: #22C55E; }
.result-card h3 { font-size: 20px; font-weight: 700; color: #E2E6ED; margin-bottom: 16px; }
.result-details { text-align: left; display: inline-block; margin-bottom: 16px; }
.detail-row { display: flex; justify-content: space-between; gap: 40px; padding: 8px 0; font-size: 14px; border-bottom: 1px solid #1A1F2B; }
.detail-row span { color: #7C8496; }
.detail-row strong { color: #E2E6ED; }
.fee { color: #F59E0B !important; font-size: 18px !important; }
.expire-warn { color: #F59E0B; font-size: 14px; margin: 8px 0; }

/* Fee card */
.fee-card { text-align: center; padding: 12px 0; }
.fee-plate { font-size: 36px; font-weight: 700; color: #E2E6ED; letter-spacing: 4px; margin-bottom: 20px; }
.fee-grid { text-align: left; }
.fee-item { display: flex; justify-content: space-between; padding: 12px 0; font-size: 14px; border-bottom: 1px solid #1A1F2B; }
.fee-item span { color: #7C8496; }
.fee-item strong { color: #E2E6ED; }
.fee-item.total strong { font-size: 24px; color: #F59E0B; }

/* Plate & Keyboard */
.plate-boxes { display: flex; gap: 6px; justify-content: center; margin-bottom: 16px; }
.plate-char-box { width: 48px; height: 56px; border: 1.5px solid #252C3A; border-radius: 8px; display: flex; align-items: center; justify-content: center; font-size: 22px; font-weight: 600; cursor: pointer; background: #0F131D; color: #E2E6ED; transition: all 0.15s; }
.plate-char-box.active { border-color: #4F8CFF; box-shadow: 0 0 0 2px rgba(79,140,255,0.15); }
.plate-dot { width: 20px; height: 56px; display: flex; align-items: center; justify-content: center; font-size: 20px; color: #4A5168; }
.keyboard { background: #0F131D; border-radius: 10px; padding: 12px; border: 1px solid #1A1F2B; }
.kb-hint { text-align: center; font-size: 11px; color: #5C6378; margin-bottom: 8px; }
.kb-grid { display: flex; flex-wrap: wrap; gap: 5px; justify-content: center; }
.kb-key { min-width: 36px; height: 36px; border: 1px solid #1E2432; border-radius: 6px; display: flex; align-items: center; justify-content: center; font-size: 14px; cursor: pointer; background: #131822; color: #B0B8C8; user-select: none; transition: all 0.15s; padding: 0 6px; }
.kb-key:hover { background: rgba(79,140,255,0.1); border-color: #4F8CFF; color: #4F8CFF; }
.kb-actions { display: flex; gap: 8px; margin-top: 8px; justify-content: center; }
.kb-del, .kb-clear { min-width: 56px; height: 32px; font-size: 12px; }

@media (max-width: 768px) {
  .page-wrap { max-width: 100%; padding: 0 4px; }
  .plate-char-box { width: 40px; height: 48px; font-size: 18px; }
  .plate-boxes { gap: 4px; }
  .kb-key { min-width: 30px; height: 30px; font-size: 12px; padding: 0 4px; }
  .kb-grid { gap: 3px; }
  .fee-plate { font-size: 26px; }
  .result-actions { flex-direction: column; gap: 8px; }
}
@media (max-width: 480px) {
  .plate-char-box { width: 36px; height: 44px; font-size: 16px; }
  .plate-boxes { gap: 3px; }
  .plate-dot { width: 14px; height: 44px; font-size: 16px; }
}
</style>
