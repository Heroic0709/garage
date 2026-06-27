import api from './index'

/** 停车记录列表 */
export function getRecords(params) {
  return api.get('/admin/records', { params })
}

/** 收费统计 */
export function getStatistics() {
  return api.get('/admin/statistics')
}

/** 会员消费记录 */
export function getConsumption(params) {
  return api.get('/admin/consumption', { params })
}
