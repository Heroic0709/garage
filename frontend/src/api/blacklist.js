import api from './index'

export function getBlacklist(params) {
  return api.get('/blacklist', { params })
}

export function addBlacklist(data) {
  return api.post('/blacklist/add', data)
}

export function removeBlacklist(plate_number) {
  return api.delete('/blacklist/remove', { params: { plate_number } })
}
