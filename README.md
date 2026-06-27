# 停车场智能管控系统

基于 Vue 3 + FastAPI 的全栈停车场管理系统，支持车辆入场识别、停车缴费、出场核验、会员管理、钱包充值、黑名单管理等功能，适配 PC 与手机端。

## 功能模块

| 模块 | 说明 |
|------|------|
| 登录/注册 | JWT 认证，普通用户/管理员角色分离 |
| 首页概览 | 管理员看收入统计，普通用户看快捷入口 |
| 车辆入场 | 支持上传图片识别车牌或手动输入车牌 |
| 停车缴费 | 按首小时 5 元 + 后续 3 元/小时计费，会员 3 元/小时 |
| 车辆出场 | 核验缴费状态，过期补缴，黑名单拦截 |
| 会员中心 | ¥20/月开通会员享优惠费率，从钱包扣款 |
| 我的钱包 | 余额充值（¥20/50/100/200 快捷金额）、交易流水 |
| 管理后台 | 停车消费/会员消费双视图、收入统计、记录筛选 |
| 黑名单管理 | 永久/临时拉黑，拦截入场和出场 |
| 响应式适配 | 移动端汉堡菜单，车牌键盘自适应，表格堆叠 |

## 技术栈

**后端** (Python)

| 组件 | 版本 |
|------|------|
| FastAPI | 0.115 |
| SQLAlchemy | 2.0 |
| MySQL (PyMySQL) | — |
| JWT (python-jose) | 3.3 |
| bcrypt | 4.0 |

**前端** (Node.js)

| 组件 | 版本 |
|------|------|
| Vue 3 | 3.5 |
| Vue Router | 4.6 |
| Element Plus | 2.14 |
| Axios | 1.18 |
| Vite | 8.1 |

## 项目结构

```
recognize-car-plate/
├── backend/                  # 后端（FastAPI）
│   ├── routes/               # API 路由
│   │   ├── auth.py           # 登录/注册
│   │   ├── entry.py          # 车辆入场（图片识别 + 手动）
│   │   ├── payment.py        # 停车缴费
│   │   ├── exit.py           # 车辆出场核验
│   │   ├── admin.py          # 管理后台（统计 + 记录）
│   │   ├── blacklist.py      # 黑名单管理
│   │   ├── membership.py     # 会员开通/续费
│   │   └── wallet.py         # 钱包充值/余额/流水
│   ├── services/             # 业务逻辑
│   │   ├── billing.py        # 计费引擎（普通/会员费率）
│   │   └── plate_service.py  # 车牌识别服务
│   ├── models.py             # 数据库模型（SQLAlchemy ORM）
│   ├── schemas.py            # Pydantic 请求/响应模型
│   ├── config.py             # 系统配置（费率/有效期/JWT）
│   ├── database.py           # 数据库连接
│   ├── auth.py               # 认证依赖（JWT + bcrypt）
│   ├── main.py               # FastAPI 入口 + 路由注册
│   └── requirements.txt      # Python 依赖
├── frontend/                 # 前端（Vue 3 + Vite）
│   ├── src/
│   │   ├── views/            # 页面组件
│   │   │   ├── LoginPage.vue
│   │   │   ├── MainLayout.vue  # 主布局（含响应式侧栏）
│   │   │   ├── HomePage.vue
│   │   │   ├── EntryPage.vue
│   │   │   ├── PayPage.vue
│   │   │   ├── ExitPage.vue
│   │   │   ├── MembershipPage.vue
│   │   │   ├── WalletPage.vue
│   │   │   ├── AdminPage.vue
│   │   │   └── BlacklistPage.vue
│   │   ├── api/              # API 封装（axios）
│   │   └── router/           # Vue Router 路由配置
│   ├── package.json
│   └── vite.config.js        # Vite 配置（含 API 代理）
└── README.md
```

## 快速开始

### 环境要求

- Python 3.10+
- Node.js 22+
- MySQL 8.0+

### 1. 创建数据库

```sql
CREATE DATABASE parking_system
  DEFAULT CHARACTER SET utf8mb4
  COLLATE utf8mb4_unicode_ci;
```

### 2. 后端启动

```bash
# 创建虚拟环境
python -m venv venv

# 激活（Windows）
venv\Scripts\activate

# 安装依赖
pip install -r backend\requirements.txt

# 启动服务（默认 8001 端口）
python -m uvicorn backend.main:app --host 0.0.0.0 --port 8001 --reload
```

### 3. 前端启动

```bash
cd frontend
npm install
npm run dev -- --host 0.0.0.0
```

前端运行在 `http://localhost:5173`，API 请求通过 Vite proxy 转发到后端。

### 4. 初始化管理员账号

数据库部署时会自动创建：

| 账号 | 密码 | 角色 |
|------|------|------|
| admin | admin123 | 管理员 |
| user001 | test123 | 普通用户 |

## 计费规则

| 场景 | 费率 |
|------|------|
| 普通用户 | 首小时 ¥5 + 后续 ¥3/小时 |
| 会员 | ¥3/小时（统一费率） |
| 会员月费 | ¥20/30天 |

缴费后 20 分钟内出场有效，超时需补缴。

## 数据库表

| 表名 | 说明 |
|------|------|
| parking_record | 停车记录（入场→出场完整生命周期） |
| payment_record | 缴费记录（每笔缴费明细） |
| users | 用户表（含角色/会员到期/钱包余额） |
| user_cars | 用户绑定车牌 |
| wallet_transaction | 钱包交易流水（充值/消费） |
| blacklist | 黑名单（永久/临时拉黑） |

## API 概览

| 路由 | 说明 | 权限 |
|------|------|------|
| POST /api/auth/register | 注册 | 公开 |
| POST /api/auth/login | 登录 | 公开 |
| POST /api/entry/upload | 上传图片识别入场 | 登录 |
| POST /api/entry/manual | 手动输入车牌入场 | 登录 |
| GET /api/payment/query | 查询停车费用 | 登录 |
| POST /api/payment/pay | 确认缴费（钱包扣款） | 登录 |
| POST /api/exit/upload | 上传图片识别出场 | 登录 |
| POST /api/exit/manual | 手动输入车牌出场 | 登录 |
| GET /api/membership/status | 会员状态查询 | 登录 |
| POST /api/membership/activate | 开通/续费会员 | 登录 |
| GET /api/wallet/balance | 钱包余额 | 登录 |
| POST /api/wallet/recharge | 钱包充值 | 登录 |
| GET /api/wallet/transactions | 交易流水 | 登录 |
| GET /api/admin/statistics | 收入统计 | 管理员 |
| GET /api/admin/records | 停车记录列表 | 管理员 |
| GET /api/admin/consumption | 会员消费记录 | 管理员 |
| GET/POST/DELETE /api/blacklist | 黑名单管理 | 管理员 |

完整 API 文档：启动后端后访问 `http://localhost:8001/docs`

## 移动端访问

手机和电脑连同一网络（Wi-Fi 或热点），启动前端时使用 `--host 0.0.0.0`，然后在手机浏览器输入 `http://<电脑IP>:5173`。
