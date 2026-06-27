# 停车场管控系统 Phase 2 实现计划

> **For agentic workers:** 按阶段顺序执行，每完成一个阶段需由用户完成手动测试文档，测试通过后方可进入下一阶段。

**Goal:** 在现有 v1.2 系统基础上新增用户登录/权限、黑名单、会员系统、手机端响应式适配、以及增强功能（钱包、记录查询、多车绑定、操作日志、数据导出）。

**Architecture:** 后端保持 FastAPI + SQLAlchemy + PyMySQL 架构，新增 5 张数据库表、JWT 认证中间件、auth/blacklist/membership 三个路由模块。前端在现有 Vue3 + Element Plus 暗色主题基础上新增登录页和会员中心页，路由增加守卫。

**Tech Stack:** FastAPI 0.115.6, SQLAlchemy 2.0.36, PyMySQL 1.1.1, python-jose 3.3.0, passlib 1.7.4, Vue3 + Vite + Element Plus, Axios

## Global Constraints

- Python: 3.12.10（venv）, 后端端口 8000
- MySQL: 8.1, root/123456, localhost:3306, 数据库 parking_system
- 前端端口: 5173, Vite proxy 代理 /api → localhost:8000
- 工作目录: `c:\Users\31167\Documents\trae_projects\recognize-car-plate`
- 所有新增模型使用 SQLAlchemy `Column(String)` 而非 MySQL ENUM（保持与现有模型一致）
- 前端新增页面沿用暗色主题（#131822 背景, #E2E6ED 文字, #4F8CFF 主色调）
- 不得修改 `main.py`（车牌识别引擎）
- 每个阶段至少一次 `git commit`

---

## 阶段 7: 用户登录与 JWT 认证

> **前置条件：** 无（可在现有系统上直接构建）
> **完成标准：** 用户可以注册、登录，管理员可访问管理后台，普通用户被拒绝访问管理后台。

### Task 7.1: 安装后端新依赖

**Files:**
- Modify: `backend/requirements.txt`

**Interfaces:**
- Produces: python-jose, passlib, bcrypt 包已安装

**Step 1: 更新 requirements.txt**

在 `backend/requirements.txt` 末尾追加：

```txt
python-jose[cryptography]==3.3.0
passlib[bcrypt]==1.7.4
bcrypt==4.0.1
```

**Step 2: 安装依赖**

在终端执行：

```powershell
cd c:\Users\31167\Documents\trae_projects\recognize-car-plate
.\venv\Scripts\pip.exe install python-jose[cryptography]==3.3.0 passlib[bcrypt]==1.7.4 bcrypt==4.0.1
```

**Step 3: 验证安装**

```powershell
.\venv\Scripts\python.exe -c "from jose import jwt; from passlib.context import CryptContext; print('OK')"
```

预期输出: `OK`

---

### Task 7.2: 创建 users 表

**Files:**
- Create: `sql/init_v2_users.sql`

**Interfaces:**
- Produces: MySQL 表 `users` 已存在，含预设管理员账户

**Step 1: 执行建表 SQL**

```powershell
cd c:\Users\31167\Documents\trae_projects\recognize-car-plate
& "C:\Program Files\MySQL\MySQL Server 8.1\bin\mysql.exe" -u root -p123456 parking_system -e "
CREATE TABLE IF NOT EXISTS users (
    id                INT             NOT NULL AUTO_INCREMENT,
    username          VARCHAR(50)     NOT NULL COMMENT '用户名',
    password_hash     VARCHAR(255)    NOT NULL COMMENT 'bcrypt哈希密码',
    role              VARCHAR(20)     NOT NULL DEFAULT 'user' COMMENT '角色：admin/user',
    phone             VARCHAR(20)     NULL COMMENT '手机号',
    membership_expire DATETIME        NULL COMMENT '会员到期时间',
    wallet_balance    DECIMAL(10,2)   NOT NULL DEFAULT 0.00 COMMENT '钱包余额',
    is_active         TINYINT(1)      NOT NULL DEFAULT 1 COMMENT '是否启用',
    created_at        DATETIME        NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '注册时间',
    PRIMARY KEY (id),
    UNIQUE INDEX idx_username (username)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='用户表';
"
```

**Step 2: 预设管理员账户**

```powershell
# 先生成 bcrypt 密码哈希
.\venv\Scripts\python.exe -c "
from passlib.context import CryptContext
pwd_context = CryptContext(schemes=['bcrypt'], deprecated='auto')
print(pwd_context.hash('admin123'))
"
```

记录输出的哈希值，然后：

```powershell
& "C:\Program Files\MySQL\MySQL Server 8.1\bin\mysql.exe" -u root -p123456 parking_system -e "INSERT INTO users (username, password_hash, role) VALUES ('admin', '<上一步输出的哈希值>', 'admin');"
```

**Step 3: 验证**

```powershell
& "C:\Program Files\MySQL\MySQL Server 8.1\bin\mysql.exe" -u root -p123456 parking_system -e "SELECT id, username, role FROM users;"
```

预期输出：

```
id  username  role
1   admin     admin
```

---

### Task 7.3: 创建 JWT 工具模块

**Files:**
- Create: `backend/auth.py`

**Interfaces:**
- Produces:
  - `create_access_token(user_id: int, role: str, username: str) -> str`
  - `verify_token(token: str) -> dict`
  - `get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)) -> User`
  - `require_admin(current_user: User = Depends(get_current_user)) -> User`
- Consumes: `backend.models.User` (待 Task 7.4 添加), `backend.database.get_db`, `backend.config` (SECRET_KEY)

**Step 1: 在 config.py 中添加 JWT 配置**

Modify: `backend/config.py`（在文件末尾追加）：

```python
# ============================================================
# JWT 认证配置
# ============================================================
SECRET_KEY = "parking-system-secret-key-change-in-production"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_DAYS = 7
```

**Step 2: 创建 `backend/auth.py`**

```python
"""
JWT 认证工具模块
- 生成/验证 JWT token
- FastAPI 依赖注入：获取当前用户、管理员权限检查
"""

from datetime import datetime, timedelta
from typing import Optional

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlalchemy.orm import Session

from backend.config import SECRET_KEY, ALGORITHM, ACCESS_TOKEN_EXPIRE_DAYS
from backend.database import get_db

# --- 密码哈希 ---
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# --- OAuth2 scheme（从 Header 中提取 Bearer token）---
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login", auto_error=False)

# --- Token 工具 ---

def create_access_token(user_id: int, role: str, username: str) -> str:
    """生成 JWT token，默认 7 天有效"""
    expire = datetime.utcnow() + timedelta(days=ACCESS_TOKEN_EXPIRE_DAYS)
    payload = {
        "sub": str(user_id),
        "role": role,
        "username": username,
        "exp": expire,
    }
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)


def verify_token(token: str) -> dict:
    """验证 token，返回 payload；失败抛出 401"""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="登录已过期，请重新登录",
        )


def get_current_user(
    token: Optional[str] = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
):
    """
    FastAPI Depends: 从 Authorization Header 解析 token，
    查询数据库返回 User 对象。未登录返回 401。
    """
    from backend.models import User

    if token is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="请先登录",
        )
    payload = verify_token(token)
    user_id = int(payload["sub"])
    user = db.query(User).filter(User.id == user_id, User.is_active == True).first()
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="用户不存在或已被禁用",
        )
    return user


def require_admin(current_user=Depends(get_current_user)):
    """
    FastAPI Depends: 仅允许 admin 角色，否则返回 403。
    在 get_current_user 之后调用。
    """
    from backend.models import User

    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="仅管理员可执行此操作",
        )
    return current_user
```

**Step 3: 验证模块可导入**

```powershell
cd c:\Users\31167\Documents\trae_projects\recognize-car-plate
.\venv\Scripts\python.exe -c "import sys; sys.path.insert(0,'.'); from backend.config import SECRET_KEY; print('SECRET_KEY:', SECRET_KEY[:8] + '...'); print('OK')"
```

预期输出:

```
SECRET_KEY: parking-...
OK
```

---

### Task 7.4: 添加 User 模型到 models.py

**Files:**
- Modify: `backend/models.py`（在文件末尾追加）

**Interfaces:**
- Produces: `User` 模型类（`users` 表）
- Consumes: `backend.database.Base`

**Step 1: 在 `backend/models.py` 末尾追加 User 模型**

```python
# ============================================================
# Phase 2 新增模型 (v2.0)
# ============================================================

class User(Base):
    """用户表 - 对应数据库 users"""
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, autoincrement=True, comment="主键")
    username = Column(
        String(50), unique=True, nullable=False,
        comment="用户名"
    )
    password_hash = Column(
        String(255), nullable=False,
        comment="bcrypt 哈希密码"
    )
    role = Column(
        String(20), nullable=False, default="user",
        comment="角色：admin / user"
    )
    phone = Column(
        String(20), nullable=True,
        comment="手机号"
    )
    membership_expire = Column(
        DateTime, nullable=True,
        comment="会员到期时间（NULL=非会员）"
    )
    wallet_balance = Column(
        DECIMAL(10, 2), nullable=False, default=0.00,
        comment="钱包余额"
    )
    is_active = Column(
        Integer, nullable=False, default=1,
        comment="是否启用：1-启用 0-禁用"
    )
    created_at = Column(
        DateTime, nullable=False, server_default=func.current_timestamp(),
        comment="注册时间"
    )

    def __repr__(self):
        return f"<User(id={self.id}, username='{self.username}', role='{self.role}')>"
```

**Step 2: 验证模型**

```powershell
cd c:\Users\31167\Documents\trae_projects\recognize-car-plate
.\venv\Scripts\python.exe -c "
import sys; sys.path.insert(0,'.')
from backend.models import User
print('User table:', User.__tablename__)
print('Columns:', [c.name for c in User.__table__.columns])
"
```

预期输出:

```
User table: users
Columns: ['id', 'username', 'password_hash', 'role', 'phone', 'membership_expire', 'wallet_balance', 'is_active', 'created_at']
```

---

### Task 7.5: 创建认证路由

**Files:**
- Create: `backend/routes/auth.py`

**Interfaces:**
- Produces:
  - `POST /api/auth/register` - 注册，返回 `{token, user}`
  - `POST /api/auth/login` - 登录，返回 `{token, user}`
  - `GET /api/auth/me` - 获取当前用户信息（需登录）
- Consumes: `backend.auth` (全部函数), `backend.models.User`, `backend.database.get_db`, `backend.schemas` (新增)

**Step 1: 在 `backend/schemas.py` 末尾追加认证相关 Schema**

```python
# ============================================================
# Phase 2 新增 Schema：认证 (v2.0)
# ============================================================

class AuthRegisterRequest(BaseModel):
    """注册请求"""
    username: str = Field(description="用户名", min_length=2, max_length=50)
    password: str = Field(description="密码", min_length=6, max_length=100)


class AuthLoginRequest(BaseModel):
    """登录请求"""
    username: str = Field(description="用户名")
    password: str = Field(description="密码")


class UserInfo(BaseModel):
    """用户信息（不含密码）"""
    id: int
    username: str
    role: str
    phone: Optional[str] = None
    membership_expire: Optional[datetime] = None
    wallet_balance: float = 0.0

    class Config:
        from_attributes = True


class AuthResponse(BaseModel):
    """认证响应（登录/注册）"""
    token: str = Field(description="JWT token")
    user: UserInfo = Field(description="用户信息")
```

注意：需要在文件顶部导入中添加 `UserInfo` 到不需要额外导入的部分——`UserInfo` 使用了已有类型，无需修改 import。

**Step 2: 创建 `backend/routes/auth.py`**

```python
"""
认证接口
POST /api/auth/register  注册
POST /api/auth/login     登录
GET  /api/auth/me        获取当前用户信息
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from backend.auth import (
    pwd_context,
    create_access_token,
    get_current_user,
)
from backend.database import get_db
from backend.models import User
from backend.schemas import (
    AuthRegisterRequest,
    AuthLoginRequest,
    AuthResponse,
    UserInfo,
)

router = APIRouter(tags=["认证"])


@router.post("/auth/register", response_model=AuthResponse)
def register(body: AuthRegisterRequest, db: Session = Depends(get_db)):
    """用户注册"""
    # 检查用户名是否已存在
    existing = db.query(User).filter(User.username == body.username).first()
    if existing:
        raise HTTPException(status_code=400, detail="用户名已存在")

    # 创建用户
    user = User(
        username=body.username,
        password_hash=pwd_context.hash(body.password),
        role="user",
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    # 生成 token
    token = create_access_token(user.id, user.role, user.username)
    return AuthResponse(
        token=token,
        user=UserInfo.model_validate(user),
    )


@router.post("/auth/login", response_model=AuthResponse)
def login(body: AuthLoginRequest, db: Session = Depends(get_db)):
    """用户登录"""
    # 查找用户
    user = db.query(User).filter(
        User.username == body.username,
        User.is_active == 1,
    ).first()

    if not user or not pwd_context.verify(body.password, user.password_hash):
        raise HTTPException(status_code=401, detail="用户名或密码错误")

    # 生成 token
    token = create_access_token(user.id, user.role, user.username)
    return AuthResponse(
        token=token,
        user=UserInfo.model_validate(user),
    )


@router.get("/auth/me", response_model=UserInfo)
def get_me(current_user: User = Depends(get_current_user)):
    """获取当前登录用户信息"""
    return UserInfo.model_validate(current_user)
```

**Step 3: 验证路由**

重启后端服务后使用 curl 测试（或使用 Swagger UI `http://localhost:8000/docs`）：

```powershell
# 测试注册
curl -X POST http://localhost:8000/api/auth/register -H "Content-Type: application/json" -d '{"username":"testuser","password":"123456"}'
```

预期: 返回 `{token: "...", user: {id: 2, username: "testuser", role: "user"}}`

```powershell
# 测试登录
curl -X POST http://localhost:8000/api/auth/login -H "Content-Type: application/json" -d '{"username":"admin","password":"admin123"}'
```

预期: 返回 `{token: "...", user: {id: 1, username: "admin", role: "admin"}}`

```powershell
# 测试 /me（用上一步的 token）
curl http://localhost:8000/api/auth/me -H "Authorization: Bearer <token>"
```

预期: 返回用户信息。

---

### Task 7.6: 在 FastAPI 入口注册认证路由

**Files:**
- Modify: `backend/main.py`

**Step 1: 修改 `backend/main.py`**

在路由挂载部分增加一行：

```python
# 在现有的路由挂载之前插入
from backend.routes import entry, payment, exit, admin, auth  # 新增 auth

# ...

# 挂载路由
app.include_router(auth.router, prefix="/api")     # 新增
app.include_router(entry.router, prefix="/api")
app.include_router(payment.router, prefix="/api")
app.include_router(exit.router, prefix="/api")
app.include_router(admin.router, prefix="/api")
```

**Step 2: 验证**

重启后端，访问 `http://localhost:8000/docs`，确认 Swagger UI 中出现 "认证" 标签组。

---

### Task 7.7: 创建前端 Axios 拦截器（自动附加 token）

**Files:**
- Modify: `frontend/src/api/index.js`

**Interfaces:**
- Consumes: 现有 Axios 实例
- Produces: 所有请求自动附带 `Authorization: Bearer <token>`

**Step 1: 修改 `frontend/src/api/index.js`**

```javascript
import axios from 'axios'
import { ElMessage } from 'element-plus'

const api = axios.create({
  baseURL: '/api',
  timeout: 30000,
})

// 请求拦截器：自动附加 token
api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('token')
    if (token) {
      config.headers.Authorization = `Bearer ${token}`
    }
    return config
  },
  (error) => Promise.reject(error)
)

// 响应拦截器：401 时清除 token 并跳转登录页
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      localStorage.removeItem('token')
      localStorage.removeItem('user')
      if (window.location.pathname !== '/login' && !window.location.pathname.startsWith('/app')) {
        // 仅当不在登录页或落地页时跳转
      }
      // 跳转到登录页
      if (!window.location.pathname.includes('/login')) {
        window.location.href = '/login'
      }
    }
    const msg = error.response?.data?.detail?.message || error.response?.data?.detail || error.message || '请求失败'
    ElMessage.error(typeof msg === 'string' ? msg : JSON.stringify(msg))
    return Promise.reject(error)
  }
)

export default api
```

---

### Task 7.8: 创建前端认证 API

**Files:**
- Create: `frontend/src/api/auth.js`

**Interfaces:**
- Produces:
  - `login(username, password) -> {token, user}`
  - `register(username, password) -> {token, user}`
  - `getMe() -> user`

```javascript
import api from './index'

export function login(username, password) {
  return api.post('/auth/login', { username, password })
}

export function register(username, password) {
  return api.post('/auth/register', { username, password })
}

export function getMe() {
  return api.get('/auth/me')
}
```

---

### Task 7.9: 创建 LoginPage.vue

**Files:**
- Create: `frontend/src/views/LoginPage.vue`

**Interfaces:**
- Consumes: `../api/auth` 的 login/register 函数
- Produces: 登录成功后存储 token 到 localStorage 并跳转 `/app/home`

```vue
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
            prefix-icon="User"
            :disabled="loading"
          />
        </el-form-item>
        <el-form-item>
          <el-input
            v-model="password"
            type="password"
            placeholder="密码"
            size="large"
            prefix-icon="Lock"
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
    // 错误已在拦截器处理
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
</style>
```

---

### Task 7.10: 更新路由（增加登录页 + 路由守卫）

**Files:**
- Modify: `frontend/src/router/index.js`

**Interfaces:**
- Consumes: 新增的 LoginPage.vue
- Produces: `/login` 路由 + MainLayout 路由守卫

```javascript
import { createRouter, createWebHistory } from 'vue-router'

const routes = [
  {
    path: '/',
    name: 'Splash',
    component: () => import('../views/SplashPage.vue'),
  },
  {
    path: '/login',
    name: 'Login',
    component: () => import('../views/LoginPage.vue'),
  },
  {
    path: '/app',
    component: () => import('../views/MainLayout.vue'),
    redirect: '/app/home',
    meta: { requiresAuth: true },
    children: [
      { path: 'home', name: 'Home', meta: { title: '首页' }, component: () => import('../views/HomePage.vue') },
      { path: 'entry', name: 'Entry', meta: { title: '车辆入场' }, component: () => import('../views/EntryPage.vue') },
      { path: 'pay', name: 'Pay', meta: { title: '停车缴费' }, component: () => import('../views/PayPage.vue') },
      { path: 'exit', name: 'Exit', meta: { title: '车辆出场' }, component: () => import('../views/ExitPage.vue') },
      { path: 'admin', name: 'Admin', meta: { title: '管理后台', requiresAdmin: true }, component: () => import('../views/AdminPage.vue') },
    ]
  },
]

const router = createRouter({
  history: createWebHistory(),
  routes,
})

// 全局路由守卫
router.beforeEach((to, from, next) => {
  const token = localStorage.getItem('token')

  // /app 开头的路由需要登录
  if (to.matched.some(r => r.meta.requiresAuth)) {
    if (!token) {
      return next('/login')
    }
    // 管理后台需要 admin 角色
    if (to.meta.requiresAdmin) {
      try {
        const user = JSON.parse(localStorage.getItem('user') || '{}')
        if (user.role !== 'admin') {
          // 非管理员，留在当前页
          return next(false)
        }
      } catch (e) {
        return next('/login')
      }
    }
  }

  // 已登录用户访问 /login → 重定向到 /app/home
  if (to.path === '/login' && token) {
    return next('/app/home')
  }

  next()
})

export default router
```

---

### Task 7.11: 更新 MainLayout.vue（退出登录按钮 + 用户信息）

**Files:**
- Modify: `frontend/src/views/MainLayout.vue`

**说明:** 在 MainLayout 的 `content-header` 区域增加用户信息展示和退出按钮，管理员可见管理后台菜单。

在 `<template>` 的 `<div class="content-header">` 中修改：

```html
<div class="content-header">
  <h1 class="page-title">{{ $route.meta.title }}</h1>
  <div class="header-right">
    <div class="header-time">{{ currentTime }}</div>
    <div class="user-info">
      <span class="user-name">{{ userName }}</span>
      <span class="user-role">{{ userRole }}</span>
      <el-button text size="small" @click="logout" class="logout-btn">退出</el-button>
    </div>
  </div>
</div>
```

在 `<script setup>` 中添加：

```javascript
import { computed } from 'vue'
import { useRouter } from 'vue-router'

const router = useRouter()

const userInfo = computed(() => {
  try { return JSON.parse(localStorage.getItem('user') || '{}') } catch { return {} }
})
const userName = computed(() => userInfo.value.username || '未登录')
const userRole = computed(() => userInfo.value.role === 'admin' ? '管理员' : '普通用户')

function logout() {
  localStorage.removeItem('token')
  localStorage.removeItem('user')
  router.push('/login')
}
```

在 `<style scoped>` 中添加：

```css
.header-right { display: flex; align-items: center; gap: 20px; }
.user-info { display: flex; align-items: center; gap: 8px; }
.user-name { font-size: 13px; color: #E2E6ED; font-weight: 500; }
.user-role { font-size: 11px; color: #4F8CFF; background: rgba(79,140,255,0.1); padding: 2px 8px; border-radius: 4px; }
.logout-btn { color: #7C8496 !important; font-size: 12px; }
.logout-btn:hover { color: #EF4444 !important; }
```

---

### Task 7.12: 更新 SplashPage.vue（从落地页进入登录页）

**Files:**
- Modify: `frontend/src/views/SplashPage.vue`

**说明:** 将"进入系统"按钮的跳转目标从 `/app/home` 改为 `/login`（如果未登录）或 `/app/home`（已登录）。

在 `<script setup>` 中修改 `enterSystem` 函数：

```javascript
import { useRouter } from 'vue-router'
const router = useRouter()

function enterSystem() {
  const token = localStorage.getItem('token')
  if (token) {
    router.push('/app/home')
  } else {
    router.push('/login')
  }
}
```

---

### Task 7.13: 为现有路由添加权限保护

**Files:**
- Modify: `backend/routes/entry.py`
- Modify: `backend/routes/payment.py`
- Modify: `backend/routes/exit.py`
- Modify: `backend/routes/admin.py`

**说明:** 为各路由增加 `Depends(get_current_user)` 或 `Depends(require_admin)`。

**entry.py** — 在函数签名中添加（两个函数均需要）:

```python
from backend.auth import get_current_user
# recognize_plate 和 entry_car_manual 的函数签名各加：
# current_user = Depends(get_current_user)
```

**payment.py** — 同样处理 `query_payment` 和 `pay_fee`:

```python
from backend.auth import get_current_user
# 函数签名各加: current_user = Depends(get_current_user)
```

**exit.py** — 同样处理:

```python
from backend.auth import get_current_user
# 函数签名各加: current_user = Depends(get_current_user)
```

**admin.py** — 使用 `require_admin`:

```python
from backend.auth import require_admin
# get_records 和 get_statistics 函数签名各加:
# current_user = Depends(require_admin)
```

> **注意:** 参数加在 `db: Session = Depends(get_db)` 之后即可。修改后不影响原有功能逻辑。

---

### 测试文档: 阶段 7 — 用户登录与 JWT 认证

> **测试人：** ___________  
> **测试日期：** ___________  
> **测试前提：** 后端服务运行中（`http://localhost:8000`），MySQL 已执行建表 SQL，前端开发服务器运行中（`http://localhost:5173`）。

#### 测试 1: 访问系统入口

| 步骤 | 操作 | 预期结果 | 通过/不通过 |
|------|------|----------|-------------|
| 1 | 浏览器打开 `http://localhost:5173` | 显示精美落地页（SplashPage） | [ ] 通过 |
| 2 | 点击"进入系统"按钮 | 跳转到登录页 `/login` | [ ] 通过 |
| 3 | 登录页显示"停车场智能管控系统"标题 + 用户名/密码输入框 | 页面居中，暗色主题 | [ ] 通过 |

#### 测试 2: 管理员登录

| 步骤 | 操作 | 预期结果 | 通过/不通过 |
|------|------|----------|-------------|
| 1 | 输入用户名 `admin`，密码 `admin123` | — | — |
| 2 | 点击"登 录" | 提示"登录成功"，跳转到首页 `/app/home` | [ ] 通过 |
| 3 | 查看页面右上角用户信息 | 显示"admin" + "管理员"标签 | [ ] 通过 |
| 4 | 点击左侧导航"管理后台" | 能正常进入管理后台页面 `/app/admin` | [ ] 通过 |

#### 测试 3: 普通用户注册与登录

| 步骤 | 操作 | 预期结果 | 通过/不通过 |
|------|------|----------|-------------|
| 1 | 退出登录（点击右上角"退出"） | 跳转到登录页 | [ ] 通过 |
| 2 | 点击"去注册" | 切换为注册模式（按钮变为"注册"） | [ ] 通过 |
| 3 | 输入用户名 `user001`，密码 `123456`，点击"注册" | 提示"注册成功"，跳转到首页 | [ ] 通过 |
| 4 | 查看页面右上角用户信息 | 显示"user001" + "普通用户"标签 | [ ] 通过 |
| 5 | 尝试访问 `/app/admin`（直接在地址栏输入） | 无法进入管理后台（权限不足） | [ ] 通过 |
| 6 | 左侧导航是否显示"管理后台"菜单 | 普通用户不应看到管理后台入口 | [ ] 通过 |

#### 测试 4: Token 持久化

| 步骤 | 操作 | 预期结果 | 通过/不通过 |
|------|------|----------|-------------|
| 1 | 关闭浏览器标签页 | — | — |
| 2 | 重新打开 `http://localhost:5173`，进入系统 | 直接进入首页，无需重新登录 | [ ] 通过 |

#### 测试 5: 未登录拦截

| 步骤 | 操作 | 预期结果 | 通过/不通过 |
|------|------|----------|-------------|
| 1 | 清除 localStorage（F12 → Application → Clear storage） | — | — |
| 2 | 直接访问 `http://localhost:5173/app/home` | 自动跳转到登录页 `/login` | [ ] 通过 |
| 3 | 直接访问 `http://localhost:5173/app/entry` | 自动跳转到登录页 | [ ] 通过 |

#### 测试 6: 停车业务功能验证（登录后）

| 步骤 | 操作 | 预期结果 | 通过/不通过 |
|------|------|----------|-------------|
| 1 | 使用 `admin` 登录 | — | — |
| 2 | 进入"车辆入场"，上传测试图片 | 正常识别，入场成功 | [ ] 通过 |
| 3 | 进入"停车缴费"，输入车牌查询并缴费 | 正常查询和缴费 | [ ] 通过 |
| 4 | 进入"车辆出场"，上传图片 | 正常出场 | [ ] 通过 |

---

## 阶段 8: 黑名单功能

> **前置条件：** 阶段 7 测试通过
> **完成标准：** 管理员可添加/编辑/移除黑名单，黑名单车辆入场被拦截。

### Task 8.1: 创建 blacklist 表

**Files:**
- None（直接执行 SQL）

```powershell
cd c:\Users\31167\Documents\trae_projects\recognize-car-plate
& "C:\Program Files\MySQL\MySQL Server 8.1\bin\mysql.exe" -u root -p123456 parking_system -e "
CREATE TABLE IF NOT EXISTS blacklist (
    id           INT             NOT NULL AUTO_INCREMENT,
    plate_number VARCHAR(20)     NOT NULL COMMENT '车牌号',
    reason       VARCHAR(255)    NOT NULL COMMENT '拉黑原因',
    black_type   VARCHAR(20)     NOT NULL DEFAULT 'permanent' COMMENT '类型：permanent/temporary',
    expire_at    DATETIME        NULL COMMENT '限时到期时间',
    status       VARCHAR(20)     NOT NULL DEFAULT 'active' COMMENT '状态：active/expired/removed',
    created_by   INT             NOT NULL COMMENT '操作管理员ID',
    created_at   DATETIME        NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    PRIMARY KEY (id),
    INDEX idx_plate_number (plate_number),
    INDEX idx_status (status),
    CONSTRAINT fk_blacklist_admin
        FOREIGN KEY (created_by) REFERENCES users (id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='黑名单表';
"
```

验证:

```powershell
& "C:\Program Files\MySQL\MySQL Server 8.1\bin\mysql.exe" -u root -p123456 parking_system -e "DESC blacklist;"
```

---

### Task 8.2: 添加 Blacklist 模型

**Files:**
- Modify: `backend/models.py`（在 User 模型之后追加）

```python
class Blacklist(Base):
    """黑名单表 - 对应数据库 blacklist"""
    __tablename__ = "blacklist"

    id = Column(Integer, primary_key=True, autoincrement=True, comment="主键")
    plate_number = Column(
        String(20), nullable=False, index=True,
        comment="车牌号"
    )
    reason = Column(
        String(255), nullable=False,
        comment="拉黑原因"
    )
    black_type = Column(
        String(20), nullable=False, default="permanent",
        comment="类型：permanent-永久 / temporary-限时"
    )
    expire_at = Column(
        DateTime, nullable=True,
        comment="限时到期时间"
    )
    status = Column(
        String(20), nullable=False, default="active",
        comment="状态：active-生效 / expired-已过期 / removed-已移除"
    )
    created_by = Column(
        Integer,
        ForeignKey("users.id"),
        nullable=False,
        comment="操作管理员ID"
    )
    created_at = Column(
        DateTime, nullable=False, server_default=func.current_timestamp(),
        comment="创建时间"
    )

    def __repr__(self):
        return f"<Blacklist(id={self.id}, plate='{self.plate_number}', type='{self.black_type}')>"
```

---

### Task 8.3: 添加黑名单 Schema

**Files:**
- Modify: `backend/schemas.py`（在文件末尾追加）

```python
# ============================================================
# Phase 2 新增 Schema：黑名单 (v2.0)
# ============================================================

class BlacklistCreateRequest(BaseModel):
    """添加黑名单请求"""
    plate_number: str = Field(description="车牌号")
    reason: str = Field(description="拉黑原因")
    black_type: str = Field(default="permanent", description="类型：permanent / temporary")
    expire_days: Optional[int] = Field(default=None, description="限时天数（仅 temporary 有效）")


class BlacklistItem(BaseModel):
    """黑名单列表项"""
    id: int
    plate_number: str
    reason: str
    black_type: str
    expire_at: Optional[datetime] = None
    status: str
    created_by: int
    created_by_name: str = ""
    created_at: datetime

    class Config:
        from_attributes = True


class BlacklistListResponse(BaseModel):
    """黑名单列表响应"""
    total: int
    items: List[BlacklistItem]
```

---

### Task 8.4: 创建黑名单路由

**Files:**
- Create: `backend/routes/blacklist.py`

```python
"""
黑名单管理接口（仅管理员）
POST   /api/blacklist       添加黑名单
GET    /api/blacklist       查询黑名单列表
DELETE /api/blacklist/{id}  移除黑名单
"""

from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from backend.auth import require_admin
from backend.database import get_db
from backend.models import User, Blacklist
from backend.schemas import (
    BlacklistCreateRequest,
    BlacklistItem,
    BlacklistListResponse,
)

router = APIRouter(tags=["黑名单"])


@router.post("/blacklist", response_model=BlacklistItem)
def add_blacklist(
    body: BlacklistCreateRequest,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """管理员添加黑名单"""
    # 检查是否已存在 active 状态的黑名单
    existing = db.query(Blacklist).filter(
        Blacklist.plate_number == body.plate_number,
        Blacklist.status == "active",
    ).first()
    if existing:
        raise HTTPException(status_code=400, detail="该车牌已在黑名单中")

    # 计算到期时间
    expire_at = None
    if body.black_type == "temporary" and body.expire_days:
        expire_at = datetime.now() + timedelta(days=body.expire_days)

    black = Blacklist(
        plate_number=body.plate_number,
        reason=body.reason,
        black_type=body.black_type,
        expire_at=expire_at,
        status="active",
        created_by=current_user.id,
    )
    db.add(black)
    db.commit()
    db.refresh(black)

    return BlacklistItem(
        id=black.id,
        plate_number=black.plate_number,
        reason=black.reason,
        black_type=black.black_type,
        expire_at=black.expire_at,
        status=black.status,
        created_by=black.created_by,
        created_by_name=current_user.username,
        created_at=black.created_at,
    )


@router.get("/blacklist", response_model=BlacklistListResponse)
def list_blacklist(
    status: str = Query(default=None, description="状态筛选：active/expired/removed"),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    """查询黑名单列表"""
    query = db.query(Blacklist)
    if status:
        query = query.filter(Blacklist.status == status)
    total = query.count()
    items = query.order_by(Blacklist.created_at.desc()).all()

    return BlacklistListResponse(
        total=total,
        items=[
            BlacklistItem(
                id=item.id,
                plate_number=item.plate_number,
                reason=item.reason,
                black_type=item.black_type,
                expire_at=item.expire_at,
                status=item.status,
                created_by=item.created_by,
                created_by_name="",
                created_at=item.created_at,
            )
            for item in items
        ],
    )


@router.delete("/blacklist/{blacklist_id}")
def remove_blacklist(
    blacklist_id: int,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """移除黑名单（软删除：status → removed）"""
    black = db.query(Blacklist).filter(Blacklist.id == blacklist_id).first()
    if not black:
        raise HTTPException(status_code=404, detail="黑名单记录不存在")
    black.status = "removed"
    db.commit()
    return {"message": "已移除黑名单"}
```

---

### Task 8.5: 注册黑名单路由 + 入场拦截

**Files:**
- Modify: `backend/main.py`
- Modify: `backend/routes/entry.py`

**Step 1: main.py 注册路由**

```python
from backend.routes import entry, payment, exit, admin, auth, blacklist  # 新增 blacklist

# ...
app.include_router(blacklist.router, prefix="/api")  # 新增
```

**Step 2: entry.py 添加黑名单拦截**

在 `entry_car_manual` 函数中（创建 parking_record 之前）增加黑名单检查：

```python
from backend.models import ParkingRecord, Blacklist  # 新增 Blacklist
from backend.auth import get_current_user  # 新增

# 在创建 parking_record 之前：
# 黑名单检查
black = db.query(Blacklist).filter(
    Blacklist.plate_number == plate,
    Blacklist.status == "active",
).first()

if black:
    # 检查限时黑名单是否到期
    if black.black_type == "temporary" and black.expire_at:
        if black.expire_at < datetime.now():
            # 已过期，更新状态后放行
            black.status = "expired"
            db.commit()
        else:
            raise HTTPException(
                status_code=403,
                detail={
                    "message": f"该车牌已被列入黑名单，禁止入场",
                    "reason": black.reason,
                },
            )
    else:
        raise HTTPException(
            status_code=403,
            detail={
                "message": f"该车牌已被列入黑名单，禁止入场",
                "reason": black.reason,
            },
        )

# 然后是原来的创建 parking_record 逻辑...
```

---

### Task 8.6: 创建前端黑名单 API

**Files:**
- Create: `frontend/src/api/blacklist.js`

```javascript
import api from './index'

export function getBlacklist(params) {
  return api.get('/blacklist', { params })
}

export function addBlacklist(data) {
  return api.post('/blacklist', data)
}

export function removeBlacklist(id) {
  return api.delete(`/blacklist/${id}`)
}
```

---

### Task 8.7: 在管理后台嵌入黑名单标签页

**Files:**
- Modify: `frontend/src/views/AdminPage.vue`

**说明:** 在 AdminPage 顶部增加 Tab 切换（停车记录 / 黑名单管理），黑名单 Tab 包含表格 + 添加按钮。

> 由于 AdminPage 代码较长，完整代码详见文件编辑。核心变更：
> 1. 增加 `el-tabs` 包裹原有内容
> 2. 新增"黑名单管理" tab-pane
> 3. 黑名单表格：车牌号 | 原因 | 类型 | 状态 | 操作
> 4. 添加弹窗：车牌号 + 原因 + 类型（永久/限时）+ 天数

---

### 测试文档: 阶段 8 — 黑名单功能

> **测试人：** ___________  
> **测试日期：** ___________  

#### 测试 1: 管理员添加黑名单

| 步骤 | 操作 | 预期结果 | 通过/不通过 |
|------|------|----------|-------------|
| 1 | 使用 `admin` 登录，进入管理后台 | — | — |
| 2 | 点击"黑名单管理"标签 | 切换到黑名单列表（初始为空） | [ ] 通过 |
| 3 | 点击"添加黑名单"，输入车牌号 `豫A·H6X21`，原因"测试黑名单"，类型选"限时"，天数填 `1`，点击确认 | 列表中出现该记录，显示"生效中" | [ ] 通过 |
| 4 | 再次添加相同车牌 | 提示"该车牌已在黑名单中"，添加失败 | [ ] 通过 |

#### 测试 2: 黑名单车辆入场被拦截

| 步骤 | 操作 | 预期结果 | 通过/不通过 |
|------|------|----------|-------------|
| 1 | 进入"车辆入场"，上传 `豫A·H6X21` 的测试图片 | 识别成功后弹出警告"该车牌已被列入黑名单，禁止入场"，无法入场 | [ ] 通过 |
| 2 | 尝试手动输入 `豫A·H6X21` 入场 | 同样显示黑名单警告 | [ ] 通过 |

#### 测试 3: 移除黑名单后正常入场

| 步骤 | 操作 | 预期结果 | 通过/不通过 |
|------|------|----------|-------------|
| 1 | 在管理后台黑名单中点击 `豫A·H6X21` 的"移除" | 状态变为"已移除" | [ ] 通过 |
| 2 | 再次尝试入场 `豫A·H6X21` | 正常入场成功 | [ ] 通过 |

#### 测试 4: 普通用户无法操作黑名单

| 步骤 | 操作 | 预期结果 | 通过/不通过 |
|------|------|----------|-------------|
| 1 | 使用 `user001` 登录，进入管理后台 | 管理后台 Tab 不显示"黑名单管理"（或普通用户无法进入管理后台） | [ ] 通过 |

---

## 阶段 9: 会员系统

> **前置条件：** 阶段 7 + 8 测试通过
> **完成标准：** 用户可开通会员（¥20/月），会员享受 ¥3/小时停车费率，到期自动降为非会员。

### Task 9.1: 计费服务增加会员费率

**Files:**
- Modify: `backend/services/billing.py`
- Modify: `backend/config.py`

**Step 1: config.py 新增会员费率配置**

```python
# ============================================================
# 会员配置
# ============================================================
MEMBER_RATE = 3             # 会员每小时费率（元）
MEMBER_MONTHLY_FEE = 20     # 会员月费（元）
MEMBER_DAYS = 30            # 会员有效天数
```

**Step 2: billing.py 修改 calculate_fee 签名**

将 `calculate_fee` 函数增加 `is_member` 参数：

```python
def calculate_fee(
    entry_time: datetime,
    exit_time: Optional[datetime] = None,
    is_member: bool = False,
) -> Tuple[int, float]:
    if exit_time is None:
        exit_time = datetime.now()

    park_hours = _calc_hours(entry_time, exit_time)

    if is_member:
        amount = float(park_hours * MEMBER_RATE)
    else:
        if park_hours <= 1:
            amount = float(FIRST_HOUR_RATE)
        else:
            amount = float(FIRST_HOUR_RATE + (park_hours - 1) * SUBSEQUENT_HOUR_RATE)

    return park_hours, amount
```

注意：文件顶部增加 import：

```python
from backend.config import FIRST_HOUR_RATE, SUBSEQUENT_HOUR_RATE, MEMBER_RATE
```

---

### Task 9.2: 缴费接口适配会员费率

**Files:**
- Modify: `backend/routes/payment.py`

**说明:** 在 `query_payment` 函数中，查询用户时判断会员状态，将会员状态传给 `calculate_fee`。

在 `query_payment` 函数中增加：

```python
from backend.auth import get_current_user
from backend.models import User  # 新增

# query_payment 函数签名增加 current_user 参数：
def query_payment(
    plate: str = Query(...),
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user),  # 新增
):
    # ... 查询 parking_record 逻辑不变 ...

    # 判断会员
    is_member = (
        current_user.membership_expire is not None
        and current_user.membership_expire > datetime.now()
    )

    park_hours, amount = calculate_fee(
        record.entry_time,
        is_member=is_member,
    )

    return PaymentQueryResponse(
        plate_number=record.plate_number,
        entry_time=record.entry_time,
        park_hours=park_hours,
        amount=round(amount, 2),
    )
```

类似地修改 `pay_fee` 函数。

---

### Task 9.3: 创建会员路由

**Files:**
- Create: `backend/routes/membership.py`

```python
"""
会员接口
POST /api/membership/activate  开通/续费会员
GET  /api/membership/status    查询会员状态
"""

from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from backend.auth import get_current_user
from backend.config import MEMBER_MONTHLY_FEE, MEMBER_DAYS
from backend.database import get_db
from backend.models import User
from backend.schemas import UserInfo

router = APIRouter(tags=["会员"])


@router.post("/membership/activate", response_model=UserInfo)
def activate_membership(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """开通/续费会员，扣款 20 元"""
    # 获取数据库最新状态
    user = db.query(User).filter(User.id == current_user.id).first()

    if user.wallet_balance < MEMBER_MONTHLY_FEE:
        raise HTTPException(status_code=400, detail="余额不足，请先充值")

    # 扣款
    user.wallet_balance = float(user.wallet_balance) - MEMBER_MONTHLY_FEE

    # 延长会员有效期
    now = datetime.now()
    if user.membership_expire and user.membership_expire > now:
        user.membership_expire = user.membership_expire + timedelta(days=MEMBER_DAYS)
    else:
        user.membership_expire = now + timedelta(days=MEMBER_DAYS)

    db.commit()
    db.refresh(user)
    return UserInfo.model_validate(user)


@router.get("/membership/status", response_model=UserInfo)
def membership_status(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """查询会员状态"""
    user = db.query(User).filter(User.id == current_user.id).first()
    return UserInfo.model_validate(user)
```

---

### Task 9.4: 创建前端会员中心页

**Files:**
- Create: `frontend/src/views/MembershipPage.vue`
- Create: `frontend/src/api/membership.js`
- Modify: `frontend/src/router/index.js`

**membership.js:**

```javascript
import api from './index'

export function getMembershipStatus() {
  return api.get('/membership/status')
}

export function activateMembership() {
  return api.post('/membership/activate')
}
```

**路由注册（在 router/index.js 的 children 中增加）：**

```javascript
{ path: 'membership', name: 'Membership', meta: { title: '会员中心' }, component: () => import('../views/MembershipPage.vue') },
```

**MembershipPage.vue 完整代码：**

```vue
<template>
  <div class="page-wrap">
    <!-- 加载中 -->
    <div v-if="loading" class="loading-block">
      <div class="spinner"></div>
    </div>

    <!-- 会员信息卡片 -->
    <template v-else>
      <div class="membership-card" :class="{ active: userInfo.membership_expire && new Date(userInfo.membership_expire) > new Date() }">
        <div class="card-badge">
          {{ isMember ? 'VIP 会员' : '普通用户' }}
        </div>
        <div class="card-icon">
          <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
            <polygon points="12 2 15.09 8.26 22 9.27 17 14.14 18.18 21.02 12 17.77 5.82 21.02 7 14.14 2 9.27 8.91 8.26 12 2"/>
          </svg>
        </div>
        <div class="card-info">
          <h3>{{ isMember ? '会员尊享' : '开通会员' }}</h3>
          <p v-if="isMember">到期时间：{{ expireDate }}</p>
          <p v-else>¥{{ memberPrice }}/月，停车 ¥{{ memberRate }}/小时</p>
        </div>
      </div>

      <!-- 余额 -->
      <div class="balance-row">
        <span>钱包余额</span>
        <strong>¥{{ userInfo.wallet_balance }}</strong>
      </div>

      <!-- 开通/续费按钮 -->
      <el-button
        type="primary"
        size="large"
        :loading="activating"
        :disabled="userInfo.wallet_balance < memberPrice"
        @click="doActivate"
        style="width:100%"
      >
        {{ isMember ? '续费会员 (¥' + memberPrice + ')' : '开通会员 (¥' + memberPrice + ')' }}
      </el-button>
      <p v-if="userInfo.wallet_balance < memberPrice" class="hint">余额不足，请先充值</p>
    </template>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { getMembershipStatus, activateMembership } from '../api/membership'

const userInfo = ref({ wallet_balance: 0, membership_expire: null })
const loading = ref(true)
const activating = ref(false)
const memberPrice = 20
const memberRate = 3

const isMember = computed(() => {
  return userInfo.value.membership_expire && new Date(userInfo.value.membership_expire) > new Date()
})
const expireDate = computed(() => {
  if (!userInfo.value.membership_expire) return ''
  return new Date(userInfo.value.membership_expire).toLocaleDateString()
})

onMounted(async () => {
  try {
    const res = await getMembershipStatus()
    userInfo.value = res.data
  } catch (e) {} finally { loading.value = false }
})

async function doActivate() {
  activating.value = true
  try {
    const res = await activateMembership()
    userInfo.value = res.data
    ElMessage.success(isMember.value ? '续费成功' : '开通成功')
  } catch (e) {} finally { activating.value = false }
}
</script>

<style scoped>
.page-wrap { max-width: 420px; margin: 0 auto; }
.membership-card {
  text-align: center; padding: 32px 16px 24px;
  background: #131822; border: 1px solid #252C3A; border-radius: 16px;
  position: relative; margin-bottom: 20px;
}
.membership-card.active {
  border-color: rgba(245,158,11,0.4); background: rgba(245,158,11,0.03);
}
.card-badge {
  position: absolute; top: 12px; right: 12px;
  font-size: 11px; font-weight: 600; padding: 4px 10px; border-radius: 20px;
}
.membership-card.active .card-badge { background: rgba(245,158,11,0.15); color: #F59E0B; }
.membership-card:not(.active) .card-badge { background: rgba(79,140,255,0.1); color: #4F8CFF; }
.card-icon { color: #F59E0B; margin-bottom: 8px; }
.membership-card:not(.active) .card-icon { color: #4A5168; }
.card-info h3 { font-size: 20px; font-weight: 700; color: #E2E6ED; margin: 0 0 4px; }
.card-info p { font-size: 13px; color: #7C8496; margin: 0; }
.balance-row { display: flex; justify-content: space-between; padding: 12px 16px; background: #131822; border: 1px solid #252C3A; border-radius: 10px; margin-bottom: 16px; font-size: 14px; }
.balance-row span { color: #7C8496; }
.balance-row strong { color: #E2E6ED; }
.hint { text-align: center; font-size: 12px; color: #F59E0B; margin-top: 8px; }
.loading-block { text-align: center; padding: 80px 0; }
.spinner { width: 40px; height: 40px; border: 3px solid #252C3A; border-top-color: #4F8CFF; border-radius: 50%; margin: 0 auto; animation: spin 0.8s linear infinite; }
@keyframes spin { to { transform: rotate(360deg); } }
</style>
```

---

### 测试文档: 阶段 9 — 会员系统

> **测试人：** ___________  
> **测试日期：** ___________  

#### 测试 1: 查看会员状态

| 步骤 | 操作 | 预期结果 | 通过/不通过 |
|------|------|----------|-------------|
| 1 | 使用 `user001` 登录 | — | — |
| 2 | 点击左侧导航"会员中心" | 显示"普通用户"标签 + "¥20/月，停车 ¥3/小时" | [ ] 通过 |
| 3 | 查看钱包余额 | 显示 ¥0.00 | [ ] 通过 |
| 4 | 检查开通按钮状态 | 按钮禁用（余额不足） | [ ] 通过 |

#### 测试 2: 管理员为用户充值

| 步骤 | 操作 | 预期结果 | 通过/不通过 |
|------|------|----------|-------------|
| 1 | 手动 SQL 充值 `user001` 余额 | — | — |
| | `UPDATE users SET wallet_balance = 100 WHERE username = 'user001';` | — | — |
| 2 | 刷新会员中心页面 | 余额显示 ¥100，开通按钮可用 | [ ] 通过 |

#### 测试 3: 开通会员

| 步骤 | 操作 | 预期结果 | 通过/不通过 |
|------|------|----------|-------------|
| 1 | 点击"开通会员"按钮 | 提示"开通成功"，标签变为"VIP 会员"，显示到期时间（30 天后） | [ ] 通过 |
| 2 | 查看余额 | 变为 ¥80（已扣 20） | [ ] 通过 |

#### 测试 4: 会员费率验证

| 步骤 | 操作 | 预期结果 | 通过/不通过 |
|------|------|----------|-------------|
| 1 | 用 `user001` 进行停车操作：入场 → 等 2 小时后查询缴费 | — | — |
| 2 | 查看缴费金额 | 停车 2 小时，会员价 = 2×3 = ¥6（非会员应为 ¥8） | [ ] 通过 |

#### 测试 5: 会员到期后恢复非会员费率

| 步骤 | 操作 | 预期结果 | 通过/不通过 |
|------|------|----------|-------------|
| 1 | 手动 SQL 将 `user001` 的 `membership_expire` 改为昨天 | — | — |
| 2 | 刷新会员中心页面 | 标签变为"普通用户" | [ ] 通过 |
| 3 | 查询缴费 | 按非会员费率计算 | [ ] 通过 |

#### 测试 6: 续费会员

| 步骤 | 操作 | 预期结果 | 通过/不通过 |
|------|------|----------|-------------|
| 1 | 将 `user001` 余额恢复为 100，membership_expire 改为 3 天后 | — | — |
| 2 | 点击"续费会员 (¥20)" | 到期时间在原基础上延长 30 天（= 33 天后） | [ ] 通过 |

---

## 阶段 10: 手机响应式适配

> **前置条件：** 阶段 7 测试通过
> **完成标准：** 手机浏览器访问系统时，左侧导航变为汉堡菜单，所有页面自适应。

### Task 10.1: MainLayout 汉堡菜单

**Files:**
- Modify: `frontend/src/views/MainLayout.vue`

**核心变更：**
1. 增加 `< 768px` 媒体查询，sidebar 默认 `transform: translateX(-100%)`
2. 顶部 content-header 增加汉堡按钮
3. 展开时 sidebar `transform: translateX(0)` + 遮罩层

```html
<!-- 在 sidebar 之前添加 mobile overlay -->
<div v-if="sidebarOpen" class="sidebar-overlay" @click="sidebarOpen = false"></div>
```

```javascript
const sidebarOpen = ref(false)
function toggleSidebar() { sidebarOpen.value = !sidebarOpen.value }
```

CSS 媒体查询（在 `<style scoped>` 末尾添加）：

```css
.menu-toggle { display: none; background: none; border: none; color: #E2E6ED; cursor: pointer; padding: 4px; }
.menu-toggle svg { width: 24px; height: 24px; }
.sidebar-overlay { display: none; }

@media (max-width: 768px) {
  .menu-toggle { display: flex; align-items: center; }
  .shell { flex-direction: column; }
  .sidebar {
    position: fixed; top: 0; left: 0; z-index: 100;
    height: 100vh; transform: translateX(-100%);
    transition: transform 0.25s ease;
  }
  .sidebar.open { transform: translateX(0); }
  .sidebar-overlay {
    display: block; position: fixed; top: 0; left: 0;
    width: 100vw; height: 100vh; background: rgba(0,0,0,0.5);
    z-index: 99;
  }
  .main-content { padding: 16px; }
  .content-header { flex-wrap: wrap; }
}
```

---

### Task 10.2: 所有页面 responsive 适配

**Files:**
- Modify: `frontend/src/views/EntryPage.vue`
- Modify: `frontend/src/views/PayPage.vue`
- Modify: `frontend/src/views/ExitPage.vue`
- Modify: `frontend/src/views/AdminPage.vue`

**通用 CSS 变更（在每个页面的 `<style scoped>` 末尾添加）：**

```css
@media (max-width: 768px) {
  .page-wrap { max-width: 100% !important; padding: 0; }
  .plate-char-box { width: 36px !important; height: 44px !important; font-size: 17px !important; }
  .kb-key { min-width: 28px !important; height: 30px !important; font-size: 12px !important; }
  .result-actions { flex-direction: column; }
}
```

AdminPage 额外：
```css
@media (max-width: 768px) {
  .stats-row { grid-template-columns: repeat(2, 1fr) !important; }
  .filter-bar { flex-direction: column; }
}
```

---

### 测试文档: 阶段 10 — 手机端响应式适配

> **测试人：** ___________  
> **测试日期：** ___________  
> **测试方式：** Chrome DevTools → Toggle Device Toolbar (Ctrl+Shift+M) → 选择 iPhone 12 Pro (390×844)

#### 测试 1: 汉堡菜单

| 步骤 | 操作 | 预期结果 | 通过/不通过 |
|------|------|----------|-------------|
| 1 | 以手机视口打开系统，登录 | 左侧导航栏隐藏，顶部左上角出现汉堡菜单图标 | [ ] 通过 |
| 2 | 点击汉堡菜单图标 | 左侧导航栏滑入，背景有半透明遮罩 | [ ] 通过 |
| 3 | 点击遮罩层 | 侧边栏滑出关闭 | [ ] 通过 |
| 4 | 点击导航中的菜单项（如"停车缴费"） | 页面跳转，侧边栏自动关闭 | [ ] 通过 |

#### 测试 2: 入场页适配

| 步骤 | 操作 | 预期结果 | 通过/不通过 |
|------|------|----------|-------------|
| 1 | 进入车辆入场页 | 上传区域、车牌输入框、键盘在小屏幕上正常显示，无溢出 | [ ] 通过 |
| 2 | 输入车牌 | 输入框自适应缩小，键盘按键可点击 | [ ] 通过 |

#### 测试 3: 缴费页适配

| 步骤 | 操作 | 预期结果 | 通过/不通过 |
|------|------|----------|-------------|
| 1 | 进入停车缴费页 | 车牌输入框和键盘自适应 | [ ] 通过 |

---

## 阶段 11: 增强功能

> **前置条件：** 阶段 7 测试通过
> **完成标准：** 储值钱包充值、用户车辆绑定、停车记录查询、操作日志、数据导出均可正常工作。

### Task 11.1: 创建 wallet_transaction / user_cars / audit_log 表

执行以下 SQL：

```powershell
cd c:\Users\31167\Documents\trae_projects\recognize-car-plate
& "C:\Program Files\MySQL\MySQL Server 8.1\bin\mysql.exe" -u root -p123456 parking_system -e "

CREATE TABLE IF NOT EXISTS user_cars (
    id           INT             NOT NULL AUTO_INCREMENT,
    user_id      INT             NOT NULL COMMENT '用户ID',
    plate_number VARCHAR(20)     NOT NULL COMMENT '车牌号',
    created_at   DATETIME        NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '绑定时间',
    PRIMARY KEY (id),
    INDEX idx_user_id (user_id),
    INDEX idx_plate_number (plate_number),
    UNIQUE INDEX idx_user_plate (user_id, plate_number),
    CONSTRAINT fk_user_cars_user
        FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS wallet_transaction (
    id            INT             NOT NULL AUTO_INCREMENT,
    user_id       INT             NOT NULL COMMENT '用户ID',
    type          VARCHAR(20)     NOT NULL COMMENT '交易类型：recharge/payment/refund',
    amount        DECIMAL(10,2)   NOT NULL COMMENT '金额（正=充值/退款，负=消费）',
    balance_after DECIMAL(10,2)   NOT NULL COMMENT '交易后余额',
    related_id    INT             NULL COMMENT '关联记录ID',
    created_at    DATETIME        NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '交易时间',
    PRIMARY KEY (id),
    INDEX idx_user_id (user_id),
    CONSTRAINT fk_wallet_tx_user
        FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS audit_log (
    id         INT             NOT NULL AUTO_INCREMENT,
    user_id    INT             NOT NULL COMMENT '操作人ID',
    username   VARCHAR(50)     NOT NULL COMMENT '操作人用户名',
    action     VARCHAR(50)     NOT NULL COMMENT '操作类型',
    target     VARCHAR(200)    NOT NULL COMMENT '操作对象',
    detail     TEXT            NULL COMMENT '操作详情JSON',
    ip_address VARCHAR(45)     NULL COMMENT '操作IP',
    created_at DATETIME        NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '操作时间',
    PRIMARY KEY (id),
    INDEX idx_user_id (user_id),
    INDEX idx_created_at (created_at),
    CONSTRAINT fk_audit_user
        FOREIGN KEY (user_id) REFERENCES users (id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

"
```

---

### Task 11.2: 添加增强功能模型到 models.py

在 `backend/models.py` 末尾追加：

```python
class UserCar(Base):
    """用户车辆绑定表"""
    __tablename__ = "user_cars"
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    plate_number = Column(String(20), nullable=False, index=True)
    created_at = Column(DateTime, nullable=False, server_default=func.current_timestamp())


class WalletTransaction(Base):
    """钱包交易记录表"""
    __tablename__ = "wallet_transaction"
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    type = Column(String(20), nullable=False)
    amount = Column(DECIMAL(10,2), nullable=False)
    balance_after = Column(DECIMAL(10,2), nullable=False)
    related_id = Column(Integer, nullable=True)
    created_at = Column(DateTime, nullable=False, server_default=func.current_timestamp())


class AuditLog(Base):
    """操作日志表"""
    __tablename__ = "audit_log"
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    username = Column(String(50), nullable=False)
    action = Column(String(50), nullable=False)
    target = Column(String(200), nullable=False)
    detail = Column(String(500), nullable=True)
    ip_address = Column(String(45), nullable=True)
    created_at = Column(DateTime, nullable=False, server_default=func.current_timestamp())
```

---

### Task 11.3: 创建前端新增 API 文件

| 文件 | 路径 | 内容 |
|------|------|------|
| 钱包 API | `frontend/src/api/wallet.js` | `getWallet()` / `recharge(amount)` |
| 用户 API | `frontend/src/api/user.js` | `getRecords(params)` / `bindCar(plate)` / `unbindCar(plate)` |

```javascript
// frontend/src/api/wallet.js
import api from './index'
export function getWallet() { return api.get('/user/wallet') }
export function recharge(amount) { return api.post('/user/wallet/recharge', { amount }) }
```

```javascript
// frontend/src/api/user.js
import api from './index'
export function getMyRecords(params) { return api.get('/user/records', { params }) }
export function bindCar(plate_number) { return api.post('/user/bind-car', { plate_number }) }
export function unbindCar(plate_number) { return api.delete('/user/unbind-car', { data: { plate_number } }) }
```

---

### Task 11.4: 创建后端用户增强路由

**Files:**
- Create: `backend/routes/user.py`

核心接口：`GET /user/wallet`, `POST /user/wallet/recharge`, `GET /user/records`, `POST /user/bind-car`, `DELETE /user/unbind-car`

```python
"""
用户增强接口
GET    /api/user/wallet           查询钱包余额
POST   /api/user/wallet/recharge  充值
GET    /api/user/records          用户停车记录
POST   /api/user/bind-car         绑定车辆
DELETE /api/user/unbind-car       解绑车辆
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import func, and_

from backend.auth import get_current_user
from backend.database import get_db
from backend.models import User, UserCar, WalletTransaction, ParkingRecord, PaymentRecord
from backend.schemas import RecordItem, RecordListResponse

router = APIRouter(tags=["用户"])


@router.get("/user/wallet")
def get_wallet(current_user=Depends(get_current_user), db: Session = Depends(get_db)):
    user = db.query(User).filter(User.id == current_user.id).first()
    return {"balance": float(user.wallet_balance)}


@router.post("/user/wallet/recharge")
def recharge_wallet(body: dict, current_user=Depends(get_current_user), db: Session = Depends(get_db)):
    amount = float(body.get("amount", 0))
    if amount <= 0:
        raise HTTPException(status_code=400, detail="充值金额必须大于0")
    user = db.query(User).filter(User.id == current_user.id).first()
    user.wallet_balance = float(user.wallet_balance) + amount
    tx = WalletTransaction(user_id=user.id, type="recharge", amount=amount, balance_after=float(user.wallet_balance))
    db.add(tx)
    db.commit()
    return {"balance": float(user.wallet_balance)}


@router.get("/user/records", response_model=RecordListResponse)
def get_user_records(
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    # 获取用户绑定的所有车牌
    cars = db.query(UserCar.plate_number).filter(UserCar.user_id == current_user.id).all()
    plates = [c[0] for c in cars]
    if not plates:
        return RecordListResponse(total=0, page=page, page_size=page_size, items=[])

    query = db.query(ParkingRecord).filter(ParkingRecord.plate_number.in_(plates))
    total = query.count()
    records = query.order_by(ParkingRecord.entry_time.desc()).offset((page-1)*page_size).limit(page_size).all()

    items = []
    for r in records:
        paid = db.query(func.coalesce(func.sum(PaymentRecord.amount), 0)).filter(
            PaymentRecord.parking_record_id == r.id, PaymentRecord.status == "valid"
        ).scalar()
        items.append(RecordItem(id=r.id, plate_number=r.plate_number, entry_time=r.entry_time, exit_time=r.exit_time, status=r.status, paid_amount=float(paid)))
    return RecordListResponse(total=total, page=page, page_size=page_size, items=items)


@router.post("/user/bind-car")
def bind_car(body: dict, current_user=Depends(get_current_user), db: Session = Depends(get_db)):
    plate = body.get("plate_number", "").strip()
    if not plate:
        raise HTTPException(status_code=400, detail="请输入车牌号")
    existing = db.query(UserCar).filter(UserCar.user_id == current_user.id, UserCar.plate_number == plate).first()
    if existing:
        raise HTTPException(status_code=400, detail="该车牌已绑定")
    # 检查是否被其他用户绑定
    other = db.query(UserCar).filter(UserCar.plate_number == plate, UserCar.user_id != current_user.id).first()
    if other:
        raise HTTPException(status_code=400, detail="该车牌已被其他用户绑定")
    car = UserCar(user_id=current_user.id, plate_number=plate)
    db.add(car)
    db.commit()
    return {"message": "绑定成功"}


@router.delete("/user/unbind-car")
def unbind_car(body: dict, current_user=Depends(get_current_user), db: Session = Depends(get_db)):
    plate = body.get("plate_number", "").strip()
    db.query(UserCar).filter(UserCar.user_id == current_user.id, UserCar.plate_number == plate).delete()
    db.commit()
    return {"message": "解绑成功"}
```

注册路由在 `backend/main.py`：

```python
from backend.routes import entry, payment, exit, admin, auth, blacklist, membership, user
app.include_router(user.router, prefix="/api")
```

---

### Task 11.5: 操作日志中间件（添加黑名单时自动记录）

**Files:**
- Create: `backend/middleware/audit.py`
- Modify: `backend/routes/blacklist.py`

```python
# backend/middleware/audit.py
def log_audit(db, user_id, username, action, target, detail=None, ip=None):
    from backend.models import AuditLog
    log = AuditLog(user_id=user_id, username=username, action=action, target=target, detail=detail, ip_address=ip)
    db.add(log)
```

在 `blacklist.py` 的 `add_blacklist` 中增加调用：

```python
from backend.middleware.audit import log_audit
# 在 db.commit() 之前
log_audit(db, current_user.id, current_user.username, "blacklist_add", body.plate_number, body.reason)
```

---

### Test Document: Phase 11 — Enhanced Features

#### Test 1: Wallet Recharge

| Step | Action | Expected | Pass/Fail |
|------|--------|----------|-----------|
| 1 | Login as `user001`, use curl to recharge | `curl -X POST http://localhost:8000/api/user/wallet/recharge -H "Authorization: Bearer <token>" -H "Content-Type: application/json" -d '{"amount":100}'` | Returns `{"balance": 100.0}` |
| 2 | Check DB `wallet_transaction` table | Record exists with type="recharge", amount=100 |

#### Test 2: Car Binding

| Step | Action | Expected | Pass/Fail |
|------|--------|----------|-----------|
| 1 | Bind car `豫B·60P70` | `curl -X POST http://localhost:8000/api/user/bind-car -H "Authorization: Bearer <token>" -H "Content-Type: application/json" -d '{"plate_number":"豫B·60P70"}'` | Returns success |
| 2 | Bind same car again | Returns 400 "already bound" |

#### Test 3: User Records

| Step | Action | Expected | Pass/Fail |
|------|--------|----------|-----------|
| 1 | Query records | `curl "http://localhost:8000/api/user/records" -H "Authorization: Bearer <token>"` | Returns records for bound plates |

#### Test 4: Audit Log

| Step | Action | Expected | Pass/Fail |
|------|--------|----------|-----------|
| 1 | Admin adds a blacklist entry | — | audit_log table has new row with action="blacklist_add" |

---

## Update MainLayout Navigation Items

After Phase 9 completion, update `frontend/src/views/MainLayout.vue` navItems:

````javascript
const navItems = [
  { path: '/app/home', label: '首页', icon: 'M3 3h7v7H3V3z M14 3h7v7h-7V3z M3 14h7v7H3v-7z M14 14h7v7h-7v-7z' },
  { path: '/app/entry', label: '车辆入场', icon: 'M5 17h14M5 12h14M5 7h14' },
  { path: '/app/pay', label: '停车缴费', icon: 'M12 2a10 10 0 1010 10M12 6v6l4 2' },
  { path: '/app/exit', label: '车辆出场', icon: 'M5 12h14M12 5l7 7-7 7' },
  computed: admin routes conditional
]
````

Show membership nav only when user is logged in (always).

---

## Execution Handoff

Plan complete and saved to `docs/superpowers/plans/2026-06-25-phase2-implementation.md`.

**Two execution approaches:**

1. **Inline Execution (recommended for this project)** — We'll execute each phase in sequence right here. After each phase, you fill out the test document, confirm it passes, then we proceed to the next phase.

2. **Subagent-Driven** — I dispatch fresh subagent per task, review between tasks (overhead is high for this codebase size).

**Recommended next step:** Start with Phase 7 (User Auth) — the foundation for everything else. Shall I begin? <｜end▁of▁thinking｜>

<｜｜DSML｜｜tool_calls>
<｜｜DSML｜｜invoke name="TodoWrite">
<｜｜DSML｜｜parameter name="merge" string="false">true

