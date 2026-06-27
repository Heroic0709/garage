<template>
  <div class="login-shell">
    <div class="login-card">
      <div class="login-header">
        <div class="login-logo">
          <svg width="40" height="40" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <rect x="3" y="3" width="18" height="18" rx="3"/>
            <path d="M9 9h6M9 13h6M9 17h4"/>
          </svg>
        </div>
        <h2>停车场智能管控系统</h2>
        <p>{{ isRegister ? '创建新账户' : '登录您的账户' }}</p>
      </div>

      <el-form @submit.prevent="handleSubmit" class="login-form">
        <el-form-item>
          <el-input
            v-model="username"
            placeholder="用户名"
            size="large"
            :disabled="loading"
          />
        </el-form-item>
        <el-form-item>
          <el-input
            v-model="password"
            type="password"
            placeholder="密码"
            size="large"
            show-password
            :disabled="loading"
          />
        </el-form-item>
        <el-button
          type="primary"
          size="large"
          native-type="submit"
          :loading="loading"
          class="login-btn"
        >
          {{ isRegister ? '注册' : '登 录' }}
        </el-button>
      </el-form>

      <div class="login-footer">
        <span>{{ isRegister ? '已有账户？' : '没有账户？' }}</span>
        <a href="#" @click.prevent="isRegister = !isRegister">
          {{ isRegister ? '去登录' : '去注册' }}
        </a>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { login, register } from '../api/auth'

const router = useRouter()
const username = ref('')
const password = ref('')
const loading = ref(false)
const isRegister = ref(false)

async function handleSubmit() {
  if (!username.value || !password.value) {
    ElMessage.warning('请输入用户名和密码')
    return
  }
  loading.value = true
  try {
    const fn = isRegister.value ? register : login
    const res = await fn(username.value, password.value)
    localStorage.setItem('token', res.data.token)
    localStorage.setItem('user', JSON.stringify(res.data.user))
    ElMessage.success(isRegister.value ? '注册成功' : '登录成功')
    router.push('/app/home')
  } catch (e) {
    // handled by interceptor
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.login-shell {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  background: #0D1117;
  background-image:
    radial-gradient(ellipse at 50% 0%, rgba(79,140,255,0.08) 0%, transparent 60%),
    radial-gradient(ellipse at 80% 100%, rgba(34,197,94,0.04) 0%, transparent 50%);
}
.login-card {
  width: 380px;
  padding: 40px 32px;
  background: #131822;
  border: 1px solid #252C3A;
  border-radius: 16px;
}
.login-header { text-align: center; margin-bottom: 32px; }
.login-logo { color: #4F8CFF; margin-bottom: 12px; }
.login-header h2 { font-size: 18px; font-weight: 700; color: #E2E6ED; margin: 0 0 6px; }
.login-header p { font-size: 13px; color: #7C8496; margin: 0; }
.login-form :deep(.el-input__wrapper) {
  background: #0F131D;
  border-color: #252C3A;
  box-shadow: none;
}
.login-btn { width: 100%; margin-top: 8px; }
.login-footer { text-align: center; margin-top: 20px; font-size: 13px; color: #7C8496; }
.login-footer a { color: #4F8CFF; text-decoration: none; margin-left: 4px; }

@media (max-width: 480px) {
  .login-wrapper { padding: 20px; }
  .login-card { padding: 32px 24px; }
  .login-title { font-size: 20px; }
}
</style>
