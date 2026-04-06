import os
from datetime import datetime

from apscheduler.schedulers.background import BackgroundScheduler

from models import File, db


scheduler = BackgroundScheduler()


def delete_expired_files(app):
    """删除过期本地文件与对应数据库记录。"""
    with app.app_context():
        expired = File.query.filter(
            File.is_link.is_(False),
            File.expire_at.isnot(None),
            File.expire_at < datetime.utcnow(),
        ).all()

        for file_item in expired:
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], file_item.url)
            if os.path.exists(file_path):
                try:
                    os.remove(file_path)
                except OSError:
                    # 磁盘删除失败不影响数据库清理流程
                    pass
            db.session.delete(file_item)

        db.session.commit()


def init_scheduler(app):
    """初始化并启动定时清理任务。"""
    scheduler.add_job(
        lambda: delete_expired_files(app),
        trigger='interval',
        hours=1,
        id='delete_expired_files',
        replace_existing=True,
    )

    if not scheduler.running:
        scheduler.start()
