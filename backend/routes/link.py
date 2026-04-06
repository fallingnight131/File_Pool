import mimetypes
from urllib.parse import parse_qs, unquote, urlparse

import requests
from flask import Blueprint, jsonify, request

from models import File, db


bp = Blueprint('link', __name__)

FILE_TYPE_EXTENSION_MAP = {
    'image': 'png',
    'video': 'mp4',
    'audio': 'mp3',
    'pdf': 'pdf',
    'archive': 'zip',
    'document': 'docx',
    'spreadsheet': 'xlsx',
    'presentation': 'pptx',
    'code': 'txt',
    'binary': 'bin',
}


def _derive_name_from_url(url: str) -> str:
    """从 URL 推断文件名。"""
    parsed = urlparse(url)
    path_name = unquote((parsed.path or '').rstrip('/').split('/')[-1])
    if path_name:
        return path_name

    query = parse_qs(parsed.query or '', keep_blank_values=False)
    for key in ('filename', 'file', 'name', 'download', 'attname'):
        values = query.get(key) or []
        if values and values[0]:
            return unquote(values[0])
    return 'untitled-link'


def _extract_name_from_content_disposition(value: str) -> str:
    if not value or 'filename=' not in value:
        return ''
    name = value.split('filename=')[-1].split(';')[0].strip().strip('"')
    return unquote(name)


def _split_name_extension(name: str) -> tuple[str, str]:
    if not name:
        return '', ''
    if '.' not in name:
        return name, ''
    stem, ext = name.rsplit('.', 1)
    if not stem:
        return name, ''
    ext = ''.join(ch for ch in ext.lower() if ch.isalnum())
    return stem, ext


def _normalize_file_type(file_type: str) -> str:
    file_type = (file_type or '').strip().lower()
    return FILE_TYPE_EXTENSION_MAP.get(file_type, '')


def _mime_from_extension(extension: str) -> str | None:
    if not extension:
        return None
    guessed, _ = mimetypes.guess_type(f'dummy.{extension}')
    return guessed


@bp.route('/api/link', methods=['POST'])
def upload_link():
    """上传外链到文件池。"""
    payload = request.get_json(silent=True) or {}
    url = (payload.get('url') or '').strip()
    custom_name = (payload.get('name') or '').strip()
    selected_extension = _normalize_file_type(payload.get('file_type') or '')

    if not url:
        return jsonify({'error': 'URL 不能为空'}), 400

    filename = custom_name
    url_name = _derive_name_from_url(url)
    mime_type = None

    try:
        response = requests.head(url, timeout=5, allow_redirects=True)
        mime_header = response.headers.get('Content-Type') or ''
        mime_type = mime_header.split(';')[0].strip() or None
        if not filename:
            content_disposition = response.headers.get('Content-Disposition', '')
            from_header = _extract_name_from_content_disposition(content_disposition)
            filename = from_header or url_name
    except requests.RequestException:
        if not filename:
            filename = url_name

    if not filename:
        filename = url_name

    stem, current_ext = _split_name_extension(filename)
    _, url_ext = _split_name_extension(url_name)
    guessed_ext = ''
    if mime_type:
        guessed_ext = (mimetypes.guess_extension(mime_type) or '').lstrip('.').lower()

    target_ext = current_ext or url_ext or selected_extension or guessed_ext
    if not current_ext and target_ext:
        filename = f'{stem or filename}.{target_ext}'
        current_ext = target_ext

    if not mime_type:
        mime_type = _mime_from_extension(current_ext or selected_extension)

    file_record = File(
        name=filename,
        size=0,
        mime_type=mime_type,
        is_link=True,
        url=url,
        status='alive',
        expire_at=None,
    )

    try:
        db.session.add(file_record)
        db.session.commit()
    except Exception as exc:
        db.session.rollback()
        return jsonify({'error': f'外链入池失败: {str(exc)}'}), 500

    return jsonify(
        {
            'file': {
                'id': file_record.id,
                'name': file_record.name,
                'size': file_record.size,
                'url': file_record.url,
                'is_link': file_record.is_link,
                'created_at': file_record.created_at.isoformat(),
            }
        }
    )
