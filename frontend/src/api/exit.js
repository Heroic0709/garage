import api from './index'

/** 车辆出场（图片识别） */
export function exitCar(formData) {
  return api.post('/exit', formData, {
    headers: { 'Content-Type': 'multipart/form-data' }
  })
}

/** 车辆出场（手动输入车牌号） */
export function exitCarManual(plateNumber) {
  return api.post('/exit/manual', { plate_number: plateNumber })
}
