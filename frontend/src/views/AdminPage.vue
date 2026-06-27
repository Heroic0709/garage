<template>
  <div class="admin">
    <!-- Stats -->
    <div class="stats-row">
      <div class="mini-stat">
        <div class="ms-value">{{ stats.today_income }}</div>
        <div class="ms-label">今日收入</div>
      </div>
      <div class="mini-stat">
        <div class="ms-value">{{ stats.month_income }}</div>
        <div class="ms-label">本月收入</div>
      </div>
      <div class="mini-stat">
        <div class="ms-value">{{ stats.total_income }}</div>
        <div class="ms-label">总收入</div>
      </div>
      <div class="mini-stat highlight">
        <div class="ms-value">{{ stats.parked_count }}</div>
        <div class="ms-label">当前在场</div>
      </div>
    </div>

    <!-- Filters -->
    <div class="filter-bar">
      <el-radio-group v-model="tab" @change="switchTab">
        <el-radio-button value="parking">停车消费</el-radio-button>
        <el-radio-button value="consumption">会员消费</el-radio-button>
      </el-radio-group>
    </div>

    <!-- Parking table -->
    <template v-if="tab === 'parking'">
      <div class="filter-bar">
        <el-select v-model="filterStatus" placeholder="状态筛选" clearable style="width:140px" @change="loadRecords">
          <el-option label="全部" value="" />
          <el-option label="在场" value="parking" />
          <el-option label="已缴费" value="paid" />
          <el-option label="已出场" value="exited" />
        </el-select>
        <el-input v-model="filterPlate" placeholder="搜索车牌号" clearable style="width:200px" @change="loadRecords" />
      </div>

      <el-table :data="records" stripe v-loading="tableLoading">
        <el-table-column prop="id" label="ID" width="55" />
        <el-table-column prop="plate_number" label="车牌号" width="130" />
        <el-table-column label="入场时间" width="170">
          <template #default="s">{{ s.row.entry_time ? new Date(s.row.entry_time).toLocaleString() : '-' }}</template>
        </el-table-column>
        <el-table-column label="出场时间" width="170">
          <template #default="s">{{ s.row.exit_time ? new Date(s.row.exit_time).toLocaleString() : '-' }}</template>
        </el-table-column>
        <el-table-column label="状态" width="90">
          <template #default="s">
            <el-tag v-if="s.row.status === 'parking'" type="warning">在场</el-tag>
            <el-tag v-else-if="s.row.status === 'paid'" type="success">已缴费</el-tag>
            <el-tag v-else-if="s.row.status === 'exited'" type="info">已出场</el-tag>
          </template>
        </el-table-column>
        <el-table-column label="缴费金额" width="110">
          <template #default="s">¥{{ s.row.paid_amount }}</template>
        </el-table-column>
      </el-table>
    </template>

    <!-- Consumption table -->
    <template v-if="tab === 'consumption'">
      <el-table :data="consumptionList" stripe v-loading="tableLoading">
        <el-table-column prop="id" label="ID" width="60" />
        <el-table-column prop="username" label="用户名" width="120" />
        <el-table-column label="金额" width="100">
          <template #default="s">¥{{ s.row.amount }}</template>
        </el-table-column>
        <el-table-column label="消费后余额" width="110">
          <template #default="s">¥{{ s.row.balance_after }}</template>
        </el-table-column>
        <el-table-column label="时间" min-width="170">
          <template #default="s">{{ new Date(s.row.created_at).toLocaleString() }}</template>
        </el-table-column>
      </el-table>
    </template>

    <div class="pager">
      <el-pagination v-model:current-page="page" v-model:page-size="pageSize" :page-sizes="[10,20,50]" :total="total" layout="total, sizes, prev, pager, next" @size-change="tab === 'parking' ? loadRecords() : loadConsumption()" @current-change="tab === 'parking' ? loadRecords() : loadConsumption()" />
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { getRecords, getStatistics, getConsumption } from '../api/admin'

const stats = ref({ today_income: 0, month_income: 0, total_income: 0, parked_count: 0 })
const records = ref([])
const consumptionList = ref([])
const total = ref(0)
const page = ref(1)
const pageSize = ref(10)
const filterStatus = ref('')
const filterPlate = ref('')
const tableLoading = ref(false)
const tab = ref('parking')

async function loadStats() {
  try { const res = await getStatistics(); stats.value = res.data } catch (e) {}
}

async function loadRecords() {
  tableLoading.value = true
  try {
    const params = { page: page.value, page_size: pageSize.value }
    if (filterStatus.value) params.status = filterStatus.value
    if (filterPlate.value) params.plate = filterPlate.value
    const res = await getRecords(params)
    records.value = res.data.items
    total.value = res.data.total
  } catch (e) {} finally { tableLoading.value = false }
}

async function loadConsumption() {
  tableLoading.value = true
  try {
    const res = await getConsumption({ page: page.value, page_size: pageSize.value })
    consumptionList.value = res.data.items
    total.value = res.data.total
  } catch (e) {} finally { tableLoading.value = false }
}

function switchTab() {
  page.value = 1
  if (tab.value === 'parking') loadRecords()
  else loadConsumption()
}

onMounted(() => { loadStats(); loadRecords() })
</script>

<style scoped>
.admin { max-width: 1100px; margin: 0 auto; }

.stats-row {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 12px;
  margin-bottom: 20px;
}
.mini-stat {
  background: #131822;
  border: 1px solid #252C3A;
  border-radius: 10px;
  padding: 16px;
  text-align: center;
}
.mini-stat.highlight { border-color: rgba(79,140,255,0.3); background: rgba(79,140,255,0.05); }
.ms-value {
  font-size: 24px; font-weight: 700; color: #E2E6ED;
  font-variant-numeric: tabular-nums;
}
.ms-label { font-size: 12px; color: #5C6378; margin-top: 4px; font-weight: 500; }

.filter-bar { display: flex; gap: 12px; margin-bottom: 16px; }
.pager { margin-top: 16px; display: flex; justify-content: flex-end; }

@media (max-width: 768px) {
  .admin { max-width: 100%; }
  .stats-row { grid-template-columns: repeat(2, 1fr); gap: 8px; }
  .mini-stat { padding: 12px; }
  .ms-value { font-size: 20px; }
  .filter-bar { flex-wrap: wrap; gap: 8px; }
  .filter-bar .el-select, .filter-bar .el-input { width: 100% !important; }
  .filter-bar .el-radio-group { width: 100%; }
  .el-radio-button { flex: 1; }
}
@media (max-width: 480px) {
  .el-table { font-size: 11px; }
}
</style>
