import api from './index'

export function getBalance() {
  return api.get('/wallet/balance')
}

export function recharge(amount) {
  return api.post('/wallet/recharge', { amount })
}

export function getTransactions(params) {
  return api.get('/wallet/transactions', { params })
}
