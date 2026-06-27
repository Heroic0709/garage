import api from './index'

/** 查询待缴费信息 */
export function queryPayment(plate) {
  return api.get('/payment/query', { params: { plate } })
}

/** 确认缴费 */
export function payFee(plateNumber) {
  return api.post('/payment/pay', { plate_number: plateNumber })
}
