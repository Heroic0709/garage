<template>
  <div class="splash">
    <div class="bg-gradient"></div>
    <div class="bg-grid"></div>

    <div class="splash-content">
      <!-- Animated license plate -->
      <div class="plate-scene">
        <div class="plate-frame">
          <div class="plate-glow"></div>
          <div class="plate-body">
            <div class="plate-province" ref="provinceRef">豫</div>
            <div class="plate-dot">·</div>
            <div class="plate-chars" ref="charsRef">
              <span v-for="(c, i) in plateChars" :key="i" class="plate-char" :style="{ animationDelay: (2.5 + i * 0.3) + 's' }">{{ c }}</span>
            </div>
          </div>
          <div class="scan-line"></div>
        </div>
        <div class="plate-confidence">
          <span class="conf-dot"></span>
          Recognition confidence <strong>99.3%</strong>
        </div>
      </div>

      <!-- Title -->
      <div class="splash-title">
        <h1 class="title-main">停车场智能管控系统</h1>
        <p class="title-sub">基于深度学习的车牌识别 · 全流程自动化管理</p>
      </div>

      <!-- CTA -->
      <button class="enter-btn" @click="enterSystem">
        <span>进入系统</span>
        <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">
          <path d="M5 12h14M12 5l7 7-7 7"/>
        </svg>
      </button>

      <!-- Features -->
      <div class="feature-row">
        <div class="feature-item">
          <div class="feature-icon">
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8"><rect x="2" y="2" width="20" height="20" rx="4"/><circle cx="12" cy="12" r="3"/></svg>
          </div>
          <span>智能识别</span>
        </div>
        <div class="feature-dot-sep">·</div>
        <div class="feature-item">
          <div class="feature-icon">
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8"><path d="M12 2L2 7l10 5 10-5-10-5z"/><path d="M2 17l10 5 10-5M2 12l10 5 10-5"/></svg>
          </div>
          <span>自动计费</span>
        </div>
        <div class="feature-dot-sep">·</div>
        <div class="feature-item">
          <div class="feature-icon">
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8"><path d="M22 12h-4l-3 9L9 3l-3 9H2"/></svg>
          </div>
          <span>实时监控</span>
        </div>
      </div>
    </div>

    <div class="splash-footer">v2.0 · Powered by PaddleOCR + FastAPI</div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'

const router = useRouter()
const plateChars = ref(['A', 'H', '6', 'X', '2', '1'])

function enterSystem() {
  const token = localStorage.getItem('token')
  router.push(token ? '/app/home' : '/login')
}

onMounted(() => {
  // stagger the character reveal
  setTimeout(() => {
    plateChars.value = ['A', 'H', '6', 'X', '2', '1']
  }, 200)
})
</script>

<style scoped>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800;900&display=swap');

.splash {
  width: 100vw;
  height: 100vh;
  background: #0B0F15;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  position: relative;
  overflow: hidden;
  font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
}

.bg-gradient {
  position: absolute;
  inset: 0;
  background:
    radial-gradient(ellipse 60% 50% at 50% 30%, rgba(79, 140, 255, 0.08) 0%, transparent 70%),
    radial-gradient(ellipse 40% 40% at 80% 70%, rgba(99, 102, 241, 0.06) 0%, transparent 60%),
    radial-gradient(ellipse 30% 30% at 20% 60%, rgba(34, 197, 94, 0.04) 0%, transparent 50%);
  pointer-events: none;
}

.bg-grid {
  position: absolute;
  inset: 0;
  background-image:
    linear-gradient(rgba(255,255,255,0.015) 1px, transparent 1px),
    linear-gradient(90deg, rgba(255,255,255,0.015) 1px, transparent 1px);
  background-size: 60px 60px;
  mask-image: radial-gradient(ellipse 80% 80% at 50% 50%, black 20%, transparent 70%);
  pointer-events: none;
}

.splash-content {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 32px;
  z-index: 1;
  animation: fadeInUp 0.8s ease-out;
}
@keyframes fadeInUp {
  from { opacity: 0; transform: translateY(24px); }
  to { opacity: 1; transform: translateY(0); }
}

/* ==================== License Plate ==================== */
.plate-scene {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 12px;
}
.plate-frame {
  position: relative;
  width: 340px;
  height: 88px;
}
.plate-glow {
  position: absolute;
  inset: -4px;
  border-radius: 16px;
  background: linear-gradient(135deg, rgba(79,140,255,0.3), rgba(99,102,241,0.2), rgba(34,197,94,0.15));
  filter: blur(8px);
  animation: glowPulse 3s ease-in-out infinite;
}
@keyframes glowPulse {
  0%, 100% { opacity: 0.5; }
  50% { opacity: 0.8; }
}
.plate-body {
  position: relative;
  z-index: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 2px;
  height: 100%;
  background: linear-gradient(180deg, #1E2A4A 0%, #162040 100%);
  border: 1.5px solid rgba(79, 140, 255, 0.4);
  border-radius: 12px;
  font-family: 'Inter', sans-serif;
  font-weight: 700;
  color: #fff;
  letter-spacing: 6px;
  box-shadow: 0 0 40px rgba(79, 140, 255, 0.15), inset 0 1px 0 rgba(255,255,255,0.05);
}
.plate-province {
  font-size: 38px;
  color: #fff;
  text-shadow: 0 0 20px rgba(79,140,255,0.5);
}
.plate-dot {
  font-size: 24px;
  color: rgba(255,255,255,0.5);
  margin: 0 2px;
}
.plate-chars {
  display: flex;
  gap: 2px;
}
.plate-char {
  font-size: 38px;
  color: #fff;
  text-shadow: 0 0 20px rgba(79,140,255,0.5);
  animation: charReveal 0.4s ease-out both;
}
@keyframes charReveal {
  from { opacity: 0; transform: translateY(-8px); filter: blur(4px); }
  to { opacity: 1; transform: translateY(0); filter: blur(0); }
}

.scan-line {
  position: absolute;
  top: 0; left: 8px; right: 8px;
  height: 2px;
  background: linear-gradient(90deg, transparent, rgba(79,140,255,0.9), transparent);
  border-radius: 1px;
  z-index: 2;
  box-shadow: 0 0 12px rgba(79,140,255,0.6), 0 0 30px rgba(79,140,255,0.3);
  animation: scan 2.5s ease-in-out infinite;
}
@keyframes scan {
  0% { top: 8px; opacity: 0; }
  15% { opacity: 1; }
  50% { top: calc(100% - 10px); opacity: 1; }
  65% { opacity: 0; }
  100% { top: 8px; opacity: 0; }
}

.plate-confidence {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 13px;
  color: #7C8496;
}
.plate-confidence strong { color: #22C55E; font-weight: 600; }
.conf-dot {
  width: 6px; height: 6px;
  border-radius: 50%;
  background: #22C55E;
  box-shadow: 0 0 8px rgba(34,197,94,0.5);
}

/* ==================== Title ==================== */
.splash-title { text-align: center; }
.title-main {
  font-size: 40px;
  font-weight: 800;
  color: #E2E6ED;
  letter-spacing: -1px;
  line-height: 1.2;
}
.title-sub {
  margin-top: 8px;
  font-size: 15px;
  color: #5C6378;
  font-weight: 400;
  letter-spacing: 0.5px;
}

/* ==================== CTA ==================== */
.enter-btn {
  display: inline-flex;
  align-items: center;
  gap: 10px;
  padding: 14px 36px;
  background: linear-gradient(135deg, #4F8CFF, #6366F1);
  border: none;
  border-radius: 12px;
  color: #fff;
  font-size: 16px;
  font-weight: 600;
  cursor: pointer;
  letter-spacing: 1px;
  transition: all 0.3s ease;
  box-shadow: 0 4px 24px rgba(79, 140, 255, 0.3);
  animation: btnPulse 2.5s ease-in-out infinite;
}
@keyframes btnPulse {
  0%, 100% { box-shadow: 0 4px 24px rgba(79, 140, 255, 0.3); }
  50% { box-shadow: 0 4px 36px rgba(79, 140, 255, 0.5); }
}
.enter-btn:hover {
  transform: translateY(-2px);
  box-shadow: 0 8px 32px rgba(79, 140, 255, 0.45);
}
.enter-btn:active {
  transform: translateY(0);
}

/* ==================== Features ==================== */
.feature-row {
  display: flex;
  align-items: center;
  gap: 24px;
}
.feature-item {
  display: flex;
  align-items: center;
  gap: 8px;
  color: #7C8496;
  font-size: 13px;
  font-weight: 500;
}
.feature-icon { color: #5C6378; display: flex; }
.feature-dot-sep { color: #3A4260; font-size: 18px; }

/* ==================== Footer ==================== */
.splash-footer {
  position: absolute;
  bottom: 24px;
  font-size: 12px;
  color: #3A4260;
  font-weight: 500;
  letter-spacing: 1px;
}
</style>
