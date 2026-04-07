import logging
import threading

from qcloud_cos import CosConfig, CosS3Client

logger = logging.getLogger(__name__)

_client = None
_client_lock = threading.Lock()


def _get_client(app_config):
    """获取或创建 COS 客户端（单例）。"""
    global _client
    if _client is not None:
        return _client
    with _client_lock:
        if _client is not None:
            return _client
        kwargs = {
            'Region': app_config['COS_REGION'],
            'SecretId': app_config['COS_SECRET_ID'],
            'SecretKey': app_config['COS_SECRET_KEY'],
            'Scheme': 'https',
        }
        endpoint = app_config.get('COS_INTERNAL_ENDPOINT', '')
        if endpoint:
            kwargs['Endpoint'] = endpoint
        _client = CosS3Client(CosConfig(**kwargs))
        return _client


def upload_to_cos(app_config, local_path, cos_key, file_size, progress_callback=None):
    """分片上传文件到 COS，支持进度回调 progress_callback(uploaded_bytes, total_bytes)。"""
    client = _get_client(app_config)
    bucket = app_config['COS_BUCKET']
    part_size = 5 * 1024 * 1024  # 5 MB

    if file_size <= part_size:
        # 小文件直接上传
        with open(local_path, 'rb') as fh:
            client.put_object(Bucket=bucket, Key=cos_key, Body=fh)
        if progress_callback:
            progress_callback(file_size, file_size)
        return

    # 大文件分片上传
    resp = client.create_multipart_upload(Bucket=bucket, Key=cos_key)
    upload_id = resp['UploadId']
    parts = []
    part_number = 1
    uploaded = 0

    try:
        with open(local_path, 'rb') as fh:
            while True:
                chunk = fh.read(part_size)
                if not chunk:
                    break
                r = client.upload_part(
                    Bucket=bucket,
                    Key=cos_key,
                    UploadId=upload_id,
                    PartNumber=part_number,
                    Body=chunk,
                )
                parts.append({'PartNumber': part_number, 'ETag': r['ETag']})
                uploaded += len(chunk)
                if progress_callback:
                    progress_callback(uploaded, file_size)
                part_number += 1

        client.complete_multipart_upload(
            Bucket=bucket,
            Key=cos_key,
            UploadId=upload_id,
            MultipartUpload={'Part': parts},
        )
    except Exception:
        try:
            client.abort_multipart_upload(Bucket=bucket, Key=cos_key, UploadId=upload_id)
        except Exception:
            pass
        raise


def delete_from_cos(app_config, cos_key):
    """删除 COS 上的对象。"""
    try:
        client = _get_client(app_config)
        client.delete_object(Bucket=app_config['COS_BUCKET'], Key=cos_key)
    except Exception as exc:
        logger.error('COS delete failed for %s: %s', cos_key, exc)


def get_cos_url(app_config, cos_key):
    """生成 COS 对象的外网下载 URL。"""
    bucket = app_config['COS_BUCKET']
    region = app_config['COS_REGION']
    return f'https://{bucket}.cos.{region}.myqcloud.com/{cos_key}'
