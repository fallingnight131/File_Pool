import os
from datetime import datetime

import requests
from flask import Blueprint, current_app, jsonify, redirect, request, send_file
from sqlalchemy import func

from cos_client import delete_from_cos, get_cos_url
from models import File, db


bp = Blueprint('files', __name__)


def _remaining_seconds(file_item: File) -> int:
    """计算剩余秒数。"""
    if file_item.is_link:
        return -1
    if not file_item.expire_at:
        return 0
    return int((file_item.expire_at - datetime.utcnow()).total_seconds())


def _check_link_alive(url: str) -> bool:
    """检查外链可访问性。"""
    try:
        response = requests.head(url, timeout=5, allow_redirects=True)
        return response.status_code < 400
    except requests.RequestException:
        return False


@bp.route('/api/files', methods=['GET'])
def list_files():
    """获取文件池列表。"""
    records = File.query.order_by(File.created_at.desc()).all()

    updated = False
    result = []
    for item in records:
        if item.is_link:
            alive = _check_link_alive(item.url)
            new_status = 'alive' if alive else 'dead'
            if item.status != new_status:
                item.status = new_status
                updated = True

        result.append(
            {
                'id': item.id,
                'name': item.name,
                'size': item.size,
                'mime_type': item.mime_type,
                'is_link': item.is_link,
                'url': item.url,
                'status': item.status,
                'expire_at': item.expire_at.isoformat() if item.expire_at else None,
                'created_at': item.created_at.isoformat() if item.created_at else None,
                'remaining_seconds': _remaining_seconds(item),
            }
        )

    if updated:
        db.session.commit()

    return jsonify({'files': result})


@bp.route('/api/files', methods=['DELETE'])
def delete_files():
    """批量删除文件。"""
    payload = request.get_json(silent=True) or {}
    ids = payload.get('ids') or []

    if not isinstance(ids, list) or not ids:
        return jsonify({'error': 'ids 必须是非空数组'}), 400

    records = File.query.filter(File.id.in_(ids)).all()
    found_ids = []

    for item in records:
        found_ids.append(item.id)
        if not item.is_link and item.url:
            # 从 COS 删除
            if item.cos_status == 'done' and current_app.config.get('COS_ENABLED'):
                delete_from_cos(current_app.config, item.url)
            # 删除本地文件
            file_path = os.path.join(current_app.config['UPLOAD_FOLDER'], item.url)
            if os.path.exists(file_path):
                try:
                    os.remove(file_path)
                except OSError:
                    pass
        db.session.delete(item)

    db.session.commit()
    return jsonify({'deleted': found_ids})


@bp.route('/api/download/<int:file_id>', methods=['GET'])
def download_file(file_id: int):
    """下载本地文件或跳转外链。"""
    item = File.query.get_or_404(file_id)

    if item.is_link:
        return redirect(item.url, code=302)

    # COS 上传完成，重定向到 COS 外网 URL
    if item.cos_status == 'done' and current_app.config.get('COS_ENABLED'):
        cos_url = get_cos_url(current_app.config, item.url)
        return redirect(cos_url, code=302)

    file_path = os.path.join(current_app.config['UPLOAD_FOLDER'], item.url)
    if not os.path.exists(file_path):
        return jsonify({'error': '文件不存在或已被清理'}), 404

    return send_file(file_path, as_attachment=True, download_name=item.name)


@bp.route('/api/stats', methods=['GET'])
def get_stats():
    """获取文件池使用统计。"""
    used_bytes = db.session.query(func.sum(File.size)).filter_by(is_link=False).scalar() or 0
    file_count = db.session.query(func.count(File.id)).scalar() or 0

    return jsonify(
        {
            'used_bytes': int(used_bytes),
            'total_bytes': int(current_app.config['MAX_POOL_SIZE']),
            'file_count': int(file_count),
        }
    )
