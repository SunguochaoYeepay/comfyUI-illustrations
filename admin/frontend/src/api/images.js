import request from '@/utils/request';

export function getImages(params) {
  return request({
    url: '/images/',
    method: 'get',
    params,
  });
}

export function createImage(data) {
  return request({
    url: '/images/',
    method: 'post',
    data,
  });
}

export function updateImage(id, data) {
  return request({
    url: `/images/${id}`,
    method: 'put',
    data,
  });
}

export function deleteImage(id) {
  return request({
    url: `/images/${id}`,
    method: 'delete',
  });
}