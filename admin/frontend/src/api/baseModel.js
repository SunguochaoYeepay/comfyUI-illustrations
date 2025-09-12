import request from '@/utils/request';

export function getBaseModels(params) {
  return request({
    url: '/base_models/',
    method: 'get',
    params
  });
}

export function createBaseModel(data) {
  return request({
    url: '/base_models/',
    method: 'post',
    data,
  });
}

export function updateBaseModel(id, data) {
  return request({
    url: `/base_models/${id}`,
    method: 'put',
    data,
  });
}

export function deleteBaseModel(id) {
  return request({
    url: `/base_models/${id}`,
    method: 'delete',
  });
}