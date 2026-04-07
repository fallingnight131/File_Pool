import os
import threading
import uuid
from datetime import datetime

from flask import Blueprint, current_app, jsonify, request
from sqlalchemy import func
from werkzeug.utils import secure_filename

from cos_client import upload_to_cos
from models import File, db


bp = Blueprint('upload', __name__)
_upload_lock = threading.Lock()

# COS 上传进度追踪（内存中）
_cos_tasks = {}  # task_id -> {total, uploaded, status}
_cos_tasks_lock = threading.Lock()


def _run_cos_upload(app, task_id, file_records):
    """后台线程：将文件从服务器分片上传到 COS。"""
    with app.app_context():
        total_size = sum(r['size'] for r in file_records)
        cumulative = 0

        try:
            for rec in file_records:
                base = cumulative

                def _on_progress(uploaded, _total, _base=base):
                    with _cos_tasks_lock:
                        task = _cos_tasks.get(task_id)
                        if task:
                            task['uploaded'] = _base + uploaded

                upload_to_cos(
                    app.config,
                    rec['local_path'],
                    rec['cos_key'],
                    rec['size'],
                    progress_callback=_on_progress,
                )
                cumulative += rec['size']

                file_obj = File.query.get(rec['id'])
                if file_obj:
                    file_obj.cos_status = 'done'
                    db.session.commit()

            with _cos_tasks_lock:
                task = _cos_tasks.get(task_id)
                if task:
                    task['uploaded'] = total_size
                    task['status'] = 'done'

        except Exception as exc:
            with _cos_tasks_lock:
                task = _cos_tasks.get(task_id)
                if task:
                    task['status'] = 'failed'
                    task['error'] = str(exc)

            for rec in file_records:
                file_obj = File.query.get(rec['id'])
                if file_obj and file_obj.cos_status != 'done':
                    file_obj.cos_status = 'failed'
            db.session.commit()


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
    cos_records = []
    cos_enabled = current_app.config.get('COS_ENABLED', False)

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
                    cos_status='pending' if cos_enabled else None,
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

                if cos_enabled:
                    cos_records.append(
                        {
                            'id': file_record.id,
                            'local_path': save_path,
                            'cos_key': stored_name,
                            'size': file_record.size,
                        }
                    )

            db.session.commit()
        except Exception as exc:
            db.session.rollback()
            return jsonify({'error': f'上传失败: {str(exc)}'}), 500

    result = {'files': created_files}

    # 启动后台线程将文件上传到 COS
    if cos_enabled and cos_records:
        task_id = uuid.uuid4().hex
        total_cos_size = sum(r['size'] for r in cos_records)
        with _cos_tasks_lock:
            _cos_tasks[task_id] = {
                'total': total_cos_size,
                'uploaded': 0,
                'status': 'uploading',
            }
        result['task_id'] = task_id

        app = current_app._get_current_object()
        t = threading.Thread(target=_run_cos_upload, args=(app, task_id, cos_records), daemon=True)
        t.start()

    return jsonify(result)


@bp.route('/api/upload/progress/<task_id>', methods=['GET'])
def upload_progress(task_id):
    """查询 COS 上传进度。"""
    with _cos_tasks_lock:
        task = _cos_tasks.get(task_id)
        if not task:
            return jsonify({'error': '任务不存在'}), 404

        data = {
            'total': task['total'],
            'uploaded': task['uploaded'],
            'status': task['status'],
        }

        # 终态任务第二次轮询后清理
        if task['status'] in ('done', 'failed'):
            if task.get('_polled'):
                del _cos_tasks[task_id]
            else:
                task['_polled'] = True

    return jsonify(data)
