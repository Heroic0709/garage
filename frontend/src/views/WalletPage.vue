<template>
  <div class="page-wrap">
    <!-- Balance Card -->
    <div class="balance-card">
      <div class="balance-label">我的余额</div>
      <div class="balance-value">¥ <span>{{ balance.toFixed(2) }}</span></div>
      <div class="balance-actions">
        <el-button type="primary" @click="showRecharge = true">充值</el-button>
      </div>
    </div>

    <!-- Recharge Dialog -->
    <el-dialog v-model="showRecharge" title="钱包充值" width="380px">
      <div class="recharge-body">
        <div class="amount-presets">
          <div
            v-for="n in [20, 50, 100, 200]"
            :key="n"
            class="amount-tag"
            :class="{ active: amount === n }"
            @click="amount = n"
          >¥{{ n }}</div>
        </div>
        <el-input-number v-model="amount" :min="1" :max="9999" size="large" class="custom-amount" />
      </div>
      <template #footer>
        <el-button @click="showRecharge = false">取消</el-button>
        <el-button type="primary" @click="handleRecharge" :loading="recharging">确认充值</el-button>
      </template>
    </el-dialog>

    <!-- Transactions -->
    <div class="section-title">交易流水</div>
    <el-table :data="txList" v-loading="loading" style="width:100%">
      <el-table-column label="类型" width="80">
        <template #default="{ row }">
          <el-tag :type="row.type === 'recharge' ? 'success' : 'danger'" size="small">
            {{ row.type === 'recharge' ? '充值' : row.type === 'payment' ? '缴费' : row.type }}
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column label="金额" width="100">
        <template #default="{ row }">
          <span :class="row.amount > 0 ? 'amount-plus' : 'amount-minus'">
            {{ row.amount > 0 ? '+' : '' }}{{ row.amount.toFixed(2) }}
          </span>
        </template>
      </el-table-column>
      <el-table-column label="余额" width="100">
        <template #default="{ row }">{{ row.balance_after.toFixed(2) }}</template>
      </el-table-column>
      <el-table-column prop="created_at" label="时间" min-width="160" />
    </el-table>
    <div class="pager">
      <el-pagination
        v-model:current-page="page"
        :page-size="pageSize"
        :total="total"
        layout="prev, pager, next"
        size="small"
        @current-change="fetchTx"
      />
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { getBalance, recharge, getTransactions } from '../api/wallet'

const balance = ref(0)
const showRecharge = ref(false)
const amount = ref(50)
const recharging = ref(false)

const txList = ref([])
const total = ref(0)
const page = ref(1)
const pageSize = ref(10)
const loading = ref(false)

async function fetchBalance() {
  try { const r = await getBalance(); balance.value = r.data.balance } catch {}
}

async function handleRecharge() {
  recharging.value = true
  try {
    await recharge(amount.value)
    ElMessage.success('充值成功')
    showRecharge.value = false
    fetchBalance()
    fetchTx()
  } finally {
    recharging.value = false
  }
}

async function fetchTx() {
  loading.value = true
  try {
    const r = await getTransactions({ page: page.value, page_size: pageSize.value })
    txList.value = r.data.items
    total.value = r.data.total
  } finally {
    loading.value = false
  }
}

onMounted(() => { fetchBalance(); fetchTx() })
</script>

<style scoped>
.page-wrap { max-width: 600px; margin: 0 auto; }
.balance-card {
  background: linear-gradient(135deg, #1A2540 0%, #162040 100%);
  border: 1px solid rgba(79,140,255,0.2);
  border-radius: 16px;
  padding: 28px 32px;
  margin-bottom: 28px;
  text-align: center;
}
.balance-label { font-size: 13px; color: #7C8496; margin-bottom: 8px; }
.balance-value { font-size: 36px; font-weight: 700; color: #E2E6ED; }
.balance-value span { color: #4F8CFF; font-variant-numeric: tabular-nums; }
.balance-actions { margin-top: 16px; }

.recharge-body { display: flex; flex-direction: column; gap: 16px; align-items: center; }
.amount-presets { display: flex; gap: 10px; }
.amount-tag {
  width: 60px; padding: 10px 0;
  border: 1px solid #252C3A;
  border-radius: 8px;
  text-align: center;
  cursor: pointer;
  color: #B0B8C8;
  font-size: 14px; font-weight: 600;
  transition: all .15s;
}
.amount-tag:hover, .amount-tag.active {
  border-color: #4F8CFF;
  background: rgba(79,140,255,0.1);
  color: #4F8CFF;
}
.custom-amount { width: 200px; }

.section-title {
  font-size: 15px; font-weight: 600; color: #B0B8C8;
  margin-bottom: 12px;
}
.amount-plus { color: #22C55E; font-weight: 600; }
.amount-minus { color: #EF4444; font-weight: 600; }
.pager { margin-top: 12px; display: flex; justify-content: flex-end; }

@media (max-width: 768px) {
  .page-wrap { max-width: 100%; padding: 0 4px; }
  .balance-card { padding: 20px; }
  .balance-value { font-size: 28px; }
}
@media (max-width: 480px) {
  .amount-presets { flex-wrap: wrap; gap: 6px; }
  .amount-tag { width: 50px; padding: 8px 0; font-size: 13px; }
  .custom-amount { width: 160px; }
}
</style>
