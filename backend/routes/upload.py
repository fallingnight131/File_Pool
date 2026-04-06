import os
import threading
import uuid
from datetime import datetime

from flask import Blueprint, current_app, jsonify, request
from sqlalchemy import func
from werkzeug.utils import secure_filename

from models import File, db


bp = Blueprint('upload', __name__)
_upload_lock = threading.Lock()


@bp.route('/api/upload', methods=['POST'])
def upload_files():
    """上传本地文件到文件池。"""
    files = request.files.getlist('files[]')
    if not files:
        return jsonify({'error': '未检测到上传文件'}), 400

    # 先计算总上传体积，再在锁内完成容量校验与写入，保证并发安全。
    total_new_size = 0
    for file_obj in files:
        file_obj.stream.seek(0, os.SEEK_END)
        total_new_size += file_obj.stream.tell()
        file_obj.stream.seek(0)

    created_files = []

    with _upload_lock:
        used_bytes = db.session.query(func.sum(File.size)).filter_by(is_link=False).scalar() or 0
        if used_bytes + total_new_size > current_app.config['MAX_POOL_SIZE']:
            return jsonify({'error': '容量已满，文件池剩余空间不足'}), 413

        now = datetime.utcnow()
        expire_at = now + current_app.config['FILE_TTL']

        try:
            for file_obj in files:
                original_name = secure_filename(file_obj.filename or '')
                if not original_name:
                    original_name = f'unnamed_{uuid.uuid4().hex[:8]}'

                stored_name = f"{uuid.uuid4().hex}_{original_name}"
                save_path = os.path.join(current_app.config['UPLOAD_FOLDER'], stored_name)
                file_obj.save(save_path)

                file_record = File(
                    name=original_name,
                    size=os.path.getsize(save_path),
                    mime_type=file_obj.mimetype,
                    is_link=False,
                    url=stored_name,
                    status='alive',
                    expire_at=expire_at,
                    created_at=now,
                )
                db.session.add(file_record)
                db.session.flush()

                created_files.append(
                    {
                        'id': file_record.id,
                        'name': file_record.name,
                        'size': file_record.size,
                        'expire_at': file_record.expire_at.isoformat() if file_record.expire_at else None,
                        'created_at': file_record.created_at.isoformat(),
                    }
                )

            db.session.commit()
        except Exception as exc:
            db.session.rollback()
            return jsonify({'error': f'上传失败: {str(exc)}'}), 500

    return jsonify({'files': created_files})
