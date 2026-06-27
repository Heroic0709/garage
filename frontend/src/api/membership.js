import api from './index'

export function getMembershipStatus() {
  return api.get('/membership/status')
}

export function activateMembership() {
  return api.post('/membership/activate')
}
