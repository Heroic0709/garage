<template>
  <div class="page-wrap">
    <!-- 成功结果 -->
    <template v-if="state === 'success'">
      <div class="result-card">
        <div class="result-icon success">
          <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="9"/><path d="M8 12l3 3 5-5"/></svg>
        </div>
        <h3>入场成功</h3>
        <div class="result-details">
          <div class="detail-row"><span>车牌号</span><strong>{{ resultPlate }}</strong></div>
          <div class="detail-row"><span>入场时间</span><strong>{{ entryTime }}</strong></div>
          <div class="detail-row"><span>状态</span><el-tag type="success">在场</el-tag></div>
        </div>
        <div class="result-actions">
          <el-button type="primary" @click="resetForm">继续入场</el-button>
          <el-button text @click="$router.push('/app/home')">返回首页</el-button>
        </div>
      </div>
    </template>

    <!-- 识别确认 -->
    <template v-else-if="state === 'review'">
      <div class="review-block">
        <div class="recognized-plate">{{ recognizedPlate }}</div>
        <div class="confidence-bar">
          <div class="confidence-fill" :style="{ width: recognizedConfidence + '%' }"></div>
        </div>
        <div class="confidence-text">识别置信度 {{ recognizedConfidence }}%</div>
        <el-alert v-if="recognizedConfidence < 90" title="置信度较低，建议核对车牌是否正确" type="warning" show-icon :closable="false" style="margin-top:16px" />
        <div class="review-btns">
          <el-button type="primary" size="large" @click="confirmEntry">确认无误，立即入场</el-button>
          <el-button size="large" @click="editPlate">识别有误，手动修改</el-button>
        </div>
      </div>
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
            <span>点击或拖拽上传车牌图片</span>
            <small>支持 JPG / PNG 格式</small>
          </div>
        </el-upload>
        <div v-if="state === 'recognizing'" class="loading-block">
          <div class="spinner"></div>
          <p>正在识别车牌...</p>
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
          <div class="kb-grid">
            <div v-for="key in currentKeys" :key="key" class="kb-key" @click="onKeyPress(key)">{{ key }}</div>
          </div>
          <div class="kb-actions">
            <div class="kb-key kb-del" @click="onDelete">删除</div>
            <div class="kb-key kb-clear" @click="onClear">清空</div>
          </div>
        </div>
        <el-button type="primary" size="large" style="width:100%;margin-top:16px" :disabled="!isPlateComplete" @click="manualEntry">确认入场</el-button>
      </template>
    </template>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import { ElMessage } from 'element-plus'
import { recognizePlate, entryCarManual } from '../api/entry'

const pKeys = '京津沪渝冀豫云辽黑湘皖鲁新苏浙赣鄂桂甘晋蒙陕吉闽贵粤川青藏琼宁'.split('')
const lKeys = 'ABCDEFGHJKLMNPQRSTUVWXYZ'.split('')
const mKeys = '1234567890ABCDEFGHJKLMNPQRSTUVWXYZ'.split('')

const state = ref('input')
const mode = ref('upload')
const resultPlate = ref('')
const entryTime = ref('')
const recognizedPlate = ref('')
const recognizedConfidence = ref(0)
const plateChars = ref(['', '', '', '', '', '', ''])
const activeIndex = ref(0)

const currentKeys = computed(() => activeIndex.value === 0 ? pKeys : activeIndex.value === 1 ? lKeys : mKeys)
const isPlateComplete = computed(() => plateChars.value.every(ch => ch !== ''))

function getFullPlate() { return plateChars.value[0] + plateChars.value[1] + '·' + plateChars.value.slice(2).join('') }
function onKeyPress(k) { plateChars.value[activeIndex.value] = k; if (activeIndex.value < 6) activeIndex.value++ }
function onDelete() { plateChars.value[activeIndex.value] = ''; if (activeIndex.value > 0) activeIndex.value-- }
function onClear() { plateChars.value = ['', '', '', '', '', '', '']; activeIndex.value = 0 }

async function handleUpload(file) {
  state.value = 'recognizing'
  try {
    const fd = new FormData(); fd.append('image', file.raw)
    const res = await recognizePlate(fd)
    recognizedPlate.value = res.data.plate_number
    recognizedConfidence.value = (res.data.confidence * 100).toFixed(1)
    state.value = 'review'
  } catch (e) { state.value = 'input' }
}

function editPlate() {
  mode.value = 'manual'
  plateChars.value = [(recognizedPlate.value && recognizedPlate.value[0]) || '', (recognizedPlate.value && recognizedPlate.value[1]) || '', '', '', '', '', '']
  activeIndex.value = 2
  state.value = 'input'
}

async function confirmEntry() {
  try {
    const res = await entryCarManual(recognizedPlate.value)
    resultPlate.value = res.data.plate_number
    entryTime.value = new Date(res.data.entry_time).toLocaleString()
    state.value = 'success'
    ElMessage.success('入场成功')
  } catch (e) { state.value = 'review' }
}

async function manualEntry() {
  state.value = 'recognizing'
  try {
    const res = await entryCarManual(getFullPlate())
    resultPlate.value = res.data.plate_number
    entryTime.value = new Date(res.data.entry_time).toLocaleString()
    state.value = 'success'
    ElMessage.success('入场成功')
  } catch (e) { state.value = 'input' }
}

function resetForm() {
  state.value = 'input'; mode.value = 'upload'
  resultPlate.value = ''; entryTime.value = ''
  recognizedPlate.value = ''; recognizedConfidence.value = 0
  onClear()
}
</script>

<style scoped>
.page-wrap { max-width: 500px; margin: 0 auto; }

/* Success */
.result-card { text-align: center; padding: 24px 0; }
.result-icon { width: 80px; height: 80px; border-radius: 50%; display: flex; align-items: center; justify-content: center; margin: 0 auto 16px; }
.result-icon.success { background: rgba(34,197,94,0.1); color: #22C55E; }
.result-card h3 { font-size: 20px; font-weight: 700; color: #E2E6ED; margin-bottom: 16px; }
.result-details { text-align: left; display: inline-block; margin-bottom: 20px; }
.detail-row { display: flex; justify-content: space-between; gap: 40px; padding: 8px 0; font-size: 14px; border-bottom: 1px solid #1A1F2B; }
.detail-row span { color: #7C8496; }
.detail-row strong { color: #E2E6ED; }

/* Review */
.review-block { text-align: center; padding: 16px 0; }
.recognized-plate { font-size: 48px; font-weight: 800; color: #E2E6ED; letter-spacing: 6px; margin-bottom: 16px; }
.confidence-bar { width: 240px; height: 4px; background: #1A1F2B; border-radius: 2px; margin: 0 auto 8px; overflow: hidden; }
.confidence-fill { height: 100%; background: linear-gradient(90deg, #4F8CFF, #22C55E); border-radius: 2px; transition: width 0.6s ease; }
.confidence-text { font-size: 13px; color: #7C8496; }
.review-btns { display: flex; gap: 12px; justify-content: center; margin-top: 20px; }

/* Mode tabs */
.mode-tabs { display: flex; margin-bottom: 20px; background: #0F131D; border-radius: 8px; padding: 3px; }
.mode-tab { flex: 1; text-align: center; padding: 10px 0; font-size: 13px; color: #5C6378; cursor: pointer; border-radius: 6px; transition: all 0.2s; font-weight: 500; }
.mode-tab.active { background: #131822; color: #4F8CFF; font-weight: 600; box-shadow: 0 1px 3px rgba(0,0,0,0.3); }

/* Upload */
.upload-area { width: 100%; }
.upload-inner { padding: 40px 0; text-align: center; color: #5C6378; }
.upload-inner svg { color: #3A4260; margin-bottom: 8px; }
.upload-inner span { display: block; font-size: 14px; color: #B0B8C8; margin: 4px 0; }
.upload-inner small { font-size: 12px; color: #5C6378; }

/* Loading */
.loading-block { text-align: center; padding: 40px 0; }
.spinner { width: 36px; height: 36px; border: 3px solid #252C3A; border-top-color: #4F8CFF; border-radius: 50%; margin: 0 auto 12px; animation: spin 0.8s linear infinite; }
@keyframes spin { to { transform: rotate(360deg); } }
.loading-block p { color: #7C8496; font-size: 14px; }

/* Plate & Keyboard */
.plate-boxes { display: flex; gap: 6px; justify-content: center; margin-bottom: 16px; }
.plate-char-box {
  width: 48px; height: 56px; border: 1.5px solid #252C3A; border-radius: 8px;
  display: flex; align-items: center; justify-content: center;
  font-size: 22px; font-weight: 600; cursor: pointer;
  background: #0F131D; color: #E2E6ED; transition: all 0.15s;
}
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
  .recognized-plate { font-size: 32px; letter-spacing: 3px; }
  .review-btns { flex-direction: column; gap: 8px; }
  .review-btns .el-button { width: 100%; }
  .kb-key { min-width: 30px; height: 30px; font-size: 12px; padding: 0 4px; }
  .kb-grid { gap: 3px; }
  .result-details .detail-row { gap: 20px; }
}
@media (max-width: 480px) {
  .plate-char-box { width: 36px; height: 44px; font-size: 16px; }
  .plate-boxes { gap: 3px; }
  .plate-dot { width: 14px; height: 44px; font-size: 16px; }
  .recognized-plate { font-size: 26px; letter-spacing: 2px; }
  .upload-inner { padding: 24px 0; }
}
</style>
