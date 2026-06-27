import api from './index'

/** 车辆入场（仅识别不入库） */
export function recognizePlate(formData) {
  return api.post('/entry/recognize', formData, {
    headers: { 'Content-Type': 'multipart/form-data' }
  })
}

/** 车辆入场（图片识别 + 入库 — 旧接口，已弃用） */
export function entryCar(formData) {
  return api.post('/entry', formData, {
    headers: { 'Content-Type': 'multipart/form-data' }
  })
}

/** 车辆入场（手动输入车牌号确认入库） */
export function entryCarManual(plateNumber) {
  return api.post('/entry/manual', { plate_number: plateNumber })
}
