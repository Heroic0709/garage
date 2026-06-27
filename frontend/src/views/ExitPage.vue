<template>
  <div class="page-wrap">
    <!-- 结果区 -->
    <template v-if="exitResult">
      <!-- 放行 -->
      <template v-if="exitResult.can_exit">
        <div class="result-card">
          <div class="result-icon success">
            <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="9"/><path d="M8 12l3 3 5-5"/></svg>
          </div>
          <h3>请通行</h3>
          <p class="plate-display">{{ exitResult.plate_number }}</p>
          <div class="result-actions"><el-button type="primary" @click="resetAll">继续核验</el-button></div>
        </div>
      </template>
      <!-- 未缴费 -->
      <template v-else-if="exitResult.reason === 'not_paid'">
        <div class="result-card">
          <div class="result-icon warn">
            <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="9"/><path d="M12 8v4M12 16h.01"/></svg>
          </div>
          <h3>请先缴费</h3>
          <p class="plate-display">{{ exitResult.plate_number }}</p>
          <p class="msg-text">{{ exitResult.message }}</p>
          <div class="result-actions">
            <el-button type="primary" @click="$router.push('/app/pay')">前往缴费</el-button>
            <el-button text @click="resetAll">重新核验</el-button>
          </div>
        </div>
      </template>
      <!-- 已过期 -->
      <template v-else-if="exitResult.reason === 'expired'">
        <div class="result-card">
          <div class="result-icon error">
            <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="9"/><path d="M15 9l-6 6M9 9l6 6"/></svg>
          </div>
          <h3>缴费已过期</h3>
          <p class="plate-display">{{ exitResult.plate_number }}</p>
          <div class="expired-fee">
            <div class="ef-row"><span>当前总费用</span><strong>¥{{ exitResult.total_amount }}</strong></div>
            <div class="ef-row"><span>已缴金额</span><strong class="deduct">¥{{ exitResult.paid_amount }}</strong></div>
            <div class="ef-row"><span>需补缴</span><strong class="need">¥{{ exitResult.need_pay }}</strong></div>
          </div>
          <div class="result-actions">
            <el-button type="primary" @click="$router.push('/app/pay')">前往补缴</el-button>
            <el-button text @click="resetAll">重新核验</el-button>
          </div>
        </div>
      </template>
      <!-- 无记录 -->
      <template v-else-if="exitResult.reason === 'no_record'">
        <div class="result-card">
          <div class="result-icon info">
            <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="9"/><path d="M12 16v-4M12 8h.01"/></svg>
          </div>
          <h3>未找到入场记录</h3>
          <p class="msg-text">请确认车牌是否正确</p>
          <div class="result-actions"><el-button type="primary" @click="resetAll">重新输入</el-button></div>
        </div>
      </template>
    </template>

    <!-- 输入区 -->
    <template v-else>
      <div class="mode-tabs">
        <div class="mode-tab" :class="{ active: mode === 'upload' }" @click="mode = 'upload'">上传图片识别</div>
        <div class="mode-tab" :class="{ active: mode === 'manual' }" @click="mode = 'manual'">手动输入车牌</div>
      </div>

      <template v-if="mode === 'upload'">
        <el-upload class="upload-area" drag :auto-upload="false" :show-file-list="false" :on-change="handleUpload" accept="image/*">
          <div class="upload-inner">
            <svg width="40" height="40" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><path d="M21 15v4a2 2 0 01-2 2H5a2 2 0 01-2-2v-4M17 8l-5-5-5 5M12 3v12"/></svg>
            <span>点击或拖拽上传出场车牌图片</span>
          </div>
        </el-upload>
        <div v-if="loading" class="loading-block">
          <div class="spinner"></div>
          <p>正在核验...</p>
        </div>
      </template>

      <template v-if="mode === 'manual'">
        <div class="plate-boxes">
          <template v-for="(ch, idx) in plateChars" :key="idx">
            <div class="plate-char-box" :class="{ active: activeIndex === idx }" @click="activeIndex = idx">{{ ch || '' }}</div>
            <div v-if="idx === 1" class="plate-dot">·</div>
          </template>
        </div>
        <div class="keyboard">
          <div class="kb-hint">{{ activeIndex === 0 ? '省份简称' : activeIndex === 1 ? '发牌机关代号' : '数字/字母' }}</div>
          <div class="kb-grid"><div v-for="key in currentKeys" :key="key" class="kb-key" @click="onKeyPress(key)">{{ key }}</div></div>
          <div class="kb-actions"><div class="kb-key kb-del" @click="onDelete">删除</div><div class="kb-key kb-clear" @click="onClear">清空</div></div>
        </div>
        <el-button type="primary" size="large" style="width:100%;margin-top:16px" :disabled="!isPlateComplete" :loading="loading" @click="manualExit">确认出场</el-button>
      </template>
    </template>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import { ElMessage } from 'element-plus'
import { exitCar, exitCarManual } from '../api/exit'

const pKeys = '京津沪渝冀豫云辽黑湘皖鲁新苏浙赣鄂桂甘晋蒙陕吉闽贵粤川青藏琼宁'.split('')
const lKeys = 'ABCDEFGHJKLMNPQRSTUVWXYZ'.split('')
const mKeys = '1234567890ABCDEFGHJKLMNPQRSTUVWXYZ'.split('')

const mode = ref('upload')
const loading = ref(false)
const exitResult = ref(null)
const plateChars = ref(['', '', '', '', '', '', ''])
const activeIndex = ref(0)

const currentKeys = computed(() => activeIndex.value === 0 ? pKeys : activeIndex.value === 1 ? lKeys : mKeys)
const isPlateComplete = computed(() => plateChars.value.every(ch => ch !== ''))

function getFullPlate() { return plateChars.value[0] + plateChars.value[1] + '·' + plateChars.value.slice(2).join('') }
function onKeyPress(k) { plateChars.value[activeIndex.value] = k; if (activeIndex.value < 6) activeIndex.value++ }
function onDelete() { plateChars.value[activeIndex.value] = ''; if (activeIndex.value > 0) activeIndex.value-- }
function onClear() { plateChars.value = ['', '', '', '', '', '', '']; activeIndex.value = 0 }

async function handleUpload(file) {
  loading.value = true; exitResult.value = null
  try {
    const fd = new FormData(); fd.append('image', file.raw)
    const res = await exitCar(fd)
    exitResult.value = res.data
    if (res.data.can_exit) ElMessage.success('放行')
  } catch (e) { exitResult.value = null } finally { loading.value = false }
}

async function manualExit() {
  loading.value = true; exitResult.value = null
  try {
    const res = await exitCarManual(getFullPlate())
    exitResult.value = res.data
    if (res.data.can_exit) ElMessage.success('放行')
  } catch (e) { exitResult.value = null } finally { loading.value = false }
}

function resetAll() { exitResult.value = null; mode.value = 'upload'; onClear() }
</script>

<style scoped>
.page-wrap { max-width: 500px; margin: 0 auto; }

.result-card { text-align: center; padding: 16px 0; }
.result-icon { width: 80px; height: 80px; border-radius: 50%; display: flex; align-items: center; justify-content: center; margin: 0 auto 16px; }
.result-icon.success { background: rgba(34,197,94,0.1); color: #22C55E; }
.result-icon.warn { background: rgba(245,158,11,0.1); color: #F59E0B; }
.result-icon.error { background: rgba(239,68,68,0.1); color: #EF4444; }
.result-icon.info { background: rgba(79,140,255,0.1); color: #4F8CFF; }
.result-card h3 { font-size: 20px; font-weight: 700; color: #E2E6ED; margin-bottom: 8px; }
.plate-display { font-size: 20px; color: #B0B8C8; font-weight: 600; letter-spacing: 2px; }
.msg-text { color: #7C8496; font-size: 14px; margin-top: 4px; }

.expired-fee { margin: 16px auto; max-width: 260px; }
.ef-row { display: flex; justify-content: space-between; padding: 8px 0; font-size: 14px; border-bottom: 1px solid #1A1F2B; }
.ef-row span { color: #7C8496; }
.ef-row strong { color: #E2E6ED; }
.deduct { color: #7C8496 !important; text-decoration: line-through; }
.need { color: #EF4444 !important; font-size: 18px !important; }

.result-actions { margin-top: 20px; display: flex; gap: 12px; justify-content: center; }

.mode-tabs { display: flex; margin-bottom: 20px; background: #0F131D; border-radius: 8px; padding: 3px; }
.mode-tab { flex: 1; text-align: center; padding: 10px 0; font-size: 13px; color: #5C6378; cursor: pointer; border-radius: 6px; transition: all 0.2s; font-weight: 500; }
.mode-tab.active { background: #131822; color: #4F8CFF; font-weight: 600; box-shadow: 0 1px 3px rgba(0,0,0,0.3); }

.upload-area { width: 100%; }
.upload-inner { padding: 40px 0; text-align: center; color: #5C6378; }
.upload-inner svg { color: #3A4260; margin-bottom: 8px; }
.upload-inner span { display: block; font-size: 14px; color: #B0B8C8; }

.loading-block { text-align: center; padding: 40px 0; }
.spinner { width: 36px; height: 36px; border: 3px solid #252C3A; border-top-color: #4F8CFF; border-radius: 50%; margin: 0 auto 12px; animation: spin 0.8s linear infinite; }
@keyframes spin { to { transform: rotate(360deg); } }

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
  .result-actions { flex-direction: column; gap: 8px; }
}
@media (max-width: 480px) {
  .plate-char-box { width: 36px; height: 44px; font-size: 16px; }
  .plate-boxes { gap: 3px; }
  .plate-dot { width: 14px; height: 44px; font-size: 16px; }
  .upload-inner { padding: 24px 0; }
  .mode-tab { font-size: 12px; padding: 8px 0; }
}
</style>
