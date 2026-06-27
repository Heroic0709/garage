<template>
  <div class="page-wrap">
    <div class="page-head">
      <h2>黑名单管理</h2>
      <el-button type="primary" @click="showAdd = true">添加黑名单</el-button>
    </div>

    <!-- Add Dialog -->
    <el-dialog v-model="showAdd" title="添加黑名单" width="460px">
      <el-form label-position="top">
        <el-form-item label="车牌号">
          <el-input v-model="form.plate_number" placeholder="如 豫A·88888" />
        </el-form-item>
        <el-form-item label="拉黑原因">
          <el-input v-model="form.reason" placeholder="如 多次逃费" />
        </el-form-item>
        <el-form-item label="类型">
          <el-radio-group v-model="form.black_type">
            <el-radio value="permanent">永久</el-radio>
            <el-radio value="temporary">限时</el-radio>
          </el-radio-group>
        </el-form-item>
        <el-form-item v-if="form.black_type === 'temporary'" label="限时天数">
          <el-input-number v-model="form.expire_days" :min="1" :max="365" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showAdd = false">取消</el-button>
        <el-button type="primary" @click="handleAdd" :loading="adding">确认添加</el-button>
      </template>
    </el-dialog>

    <!-- Table -->
    <el-table :data="list" v-loading="loading" style="width:100%">
      <el-table-column prop="plate_number" label="车牌号" width="150" />
      <el-table-column prop="reason" label="原因" min-width="200" />
      <el-table-column label="类型" width="80">
        <template #default="{ row }">
          <el-tag :type="row.black_type === 'permanent' ? 'danger' : 'warning'" size="small">
            {{ row.black_type === 'permanent' ? '永久' : '限时' }}
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column label="到期时间" width="170">
        <template #default="{ row }">{{ row.expire_at || '—' }}</template>
      </el-table-column>
      <el-table-column label="状态" width="80">
        <template #default="{ row }">
          <el-tag :type="row.status === 'active' ? 'danger' : 'info'" size="small">
            {{ row.status === 'active' ? '生效中' : row.status }}
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column label="添加时间" width="170">
        <template #default="{ row }">{{ row.created_at }}</template>
      </el-table-column>
      <el-table-column label="操作" width="100">
        <template #default="{ row }">
          <el-button v-if="row.status === 'active'" type="danger" size="small" plain @click="handleRemove(row.plate_number)">移除</el-button>
        </template>
      </el-table-column>
    </el-table>

    <div class="pager">
      <el-pagination
        v-model:current-page="page"
        :page-size="pageSize"
        :total="total"
        layout="prev, pager, next"
        @current-change="fetchList"
      />
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { getBlacklist, addBlacklist, removeBlacklist } from '../api/blacklist'

const loading = ref(false)
const adding = ref(false)
const showAdd = ref(false)
const list = ref([])
const total = ref(0)
const page = ref(1)
const pageSize = ref(10)

const form = ref({
  plate_number: '',
  reason: '',
  black_type: 'permanent',
  expire_days: null,
})

async function fetchList() {
  loading.value = true
  try {
    const res = await getBlacklist({ page: page.value, page_size: pageSize.value })
    list.value = res.data.items
    total.value = res.data.total
  } finally {
    loading.value = false
  }
}

async function handleAdd() {
  if (!form.value.plate_number || !form.value.reason) {
    ElMessage.warning('请填写车牌号和原因')
    return
  }
  adding.value = true
  try {
    await addBlacklist(form.value)
    ElMessage.success('添加成功')
    showAdd.value = false
    form.value = { plate_number: '', reason: '', black_type: 'permanent', expire_days: null }
    fetchList()
  } finally {
    adding.value = false
  }
}

async function handleRemove(plate) {
  try {
    await ElMessageBox.confirm(`确认将 ${plate} 移出黑名单？`, '确认操作', { confirmButtonText: '确认', cancelButtonText: '取消', type: 'warning' })
    await removeBlacklist(plate)
    ElMessage.success('已移除')
    fetchList()
  } catch {}
}

onMounted(fetchList)
</script>

<style scoped>
.page-wrap { max-width: 900px; margin: 0 auto; }
.page-head {
  display: flex; align-items: center; justify-content: space-between;
  margin-bottom: 20px;
}
.page-head h2 { margin: 0; font-size: 18px; }
.pager { margin-top: 16px; display: flex; justify-content: flex-end; }

@media (max-width: 768px) {
  .page-wrap { max-width: 100%; padding: 0 4px; }
  .add-row { flex-direction: column; }
  .add-row .el-input { width: 100% !important; }
  .add-row .el-select { width: 100% !important; }
  .add-row .el-button { width: 100%; }
}
</style>
