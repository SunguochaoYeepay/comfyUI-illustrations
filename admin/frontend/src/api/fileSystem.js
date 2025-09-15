import request from '@/utils/request';

export function browseFiles(params) {
  return request({
    url: '/fs/browse',
    method: 'get',
    params,
  });
}