import os
import uuid
from flask import Blueprint, request, current_app
from app import db
from app.models import Book, BorrowRecord, ImageReview, Notification
from app.services import return_service
from app.utils.response import success, error, paginated
from app.utils.jwt_helper import login_required, admin_required
from app.utils.kiosk import kiosk_blocked
from app.utils.cache import cache_delete, cache_delete_prefix, CacheKey
from datetime import datetime, timezone

return_bp = Blueprint('return', __name__)

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}


def _allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def _save_upload(file):
    upload_folder = current_app.config.get('UPLOAD_FOLDER', 'uploads')
    os.makedirs(upload_folder, exist_ok=True)
    ext = file.filename.rsplit('.', 1)[1].lower()
    safe_name = f'{uuid.uuid4().hex}.{ext}'
    filepath = os.path.join(upload_folder, safe_name)
    file.save(filepath)
    return f'/uploads/{safe_name}'


@return_bp.route('/submit', methods=['POST'])
@login_required
@kiosk_blocked
def submit_return(current_user):
    record_id = request.form.get('record_id')
    if not record_id:
        return error(400, '缺少record_id参数')

    try:
        record_id = int(record_id)
    except (TypeError, ValueError):
        return error(400, 'record_id格式错误')

    files = request.files.getlist('images')
    if not files or len(files) == 0:
        return error(400, '还书必须上传照片')

    image_urls = []
    for f in files[:3]:
        if not f or not f.filename:
            continue
        if not _allowed_file(f.filename):
            return error(400, '仅支持 png/jpg/jpeg/gif/webp 格式图片')
        try:
            url = _save_upload(f)
            image_urls.append(url)
        except Exception:
            return error(500, '图片保存失败')

    if not image_urls:
        return error(400, '未接收到有效图片')

    result, err, code = return_service.submit_return(current_user, record_id, image_urls)
    if err:
        return error(code or 400, err)

    cache_delete(CacheKey.USER(current_user.id))
    return success(result, '还书申请已提交，等待管理员确认')


@return_bp.route('/confirm', methods=['POST'])
@admin_required
def confirm_return(current_user):
    data = request.get_json(silent=True)
    if not data:
        return error(400, '请提供有效的JSON数据')

    record_id = data.get('record_id')
    damage_level = data.get('damage_level', '完好')

    if damage_level not in ('完好', '轻微污损', '严重破损'):
        return error(400, 'damage_level 必须为 完好/轻微污损/严重破损')

    record = BorrowRecord.query.filter_by(id=record_id).first()
    if not record:
        return error(404, '借阅记录不存在')

    if record.status != '已提交归还':
        return error(400, '该记录尚未提交归还')

    record.status = '已归还'
    record.damage_level = damage_level
    record.return_date = datetime.now(timezone.utc)
    record.updated_at = datetime.now(timezone.utc)

    book = db.session.get(Book, record.book_id)
    if book:
        book.available_copies += 1
        if book.available_copies > 0:
            book.status = '可借'

    if damage_level == '轻微污损':
        from app.models import CreditLog
        user = record.user
        user.credit_score = max(0, user.credit_score - 1)
        log = CreditLog(user_id=user.id, change_amount=-1, reason='还书污损', detail=f'轻微污损，扣除1分')
        db.session.add(log)
        cache_delete(CacheKey.USER(user.id))
    elif damage_level == '严重破损':
        from app.models import CreditLog
        user = record.user
        user.credit_score = max(0, user.credit_score - 2)
        log = CreditLog(user_id=user.id, change_amount=-2, reason='还书污损', detail=f'严重破损，扣除2分')
        db.session.add(log)
        cache_delete(CacheKey.USER(user.id))

    notify_title = '还书已确认'
    if damage_level == '完好':
        notify_content = f'你归还的《{book.title if book else "未知图书"}》已确认归还，图书状态完好。'
    elif damage_level == '轻微污损':
        notify_content = f'你归还的《{book.title if book else "未知图书"}》已确认归还。检测到轻微污损，信誉分-1。'
    else:
        notify_content = f'你归还的《{book.title if book else "未知图书"}》已确认归还。检测到严重破损，信誉分-2。'

    notification = Notification(
        user_id=record.user_id,
        type='还书通知',
        title=notify_title,
        content=notify_content,
        related_id=record.id
    )
    db.session.add(notification)

    db.session.commit()
    cache_delete_prefix(CacheKey.make('book'))
    return success({'record_id': record.id, 'status': record.status, 'damage_level': damage_level}, '还书确认完成')


@return_bp.route('/pending', methods=['GET'])
@admin_required
def pending_returns(current_user):
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)

    records = BorrowRecord.query.filter_by(status='已提交归还').order_by(
        BorrowRecord.borrow_date.desc()
    ).paginate(page=page, per_page=per_page, error_out=False)

    items = []
    for r in records:
        book = db.session.get(Book, r.book_id)
        items.append({
            'record_id': r.id,
            'user_id': r.user_id,
            'username': r.user.username,
            'book_id': r.book_id,
            'book_title': book.title if book else '未知',
            'borrow_date': r.borrow_date.strftime('%Y-%m-%d %H:%M:%S'),
            'due_date': r.due_date.strftime('%Y-%m-%d %H:%M:%S'),
            'return_date': r.return_date.strftime('%Y-%m-%d %H:%M:%S') if r.return_date else None,
            'image_urls': r.before_return_image_urls,
            'status': r.status
        })

    return paginated(items, records.total, page, per_page)


@return_bp.route('/my', methods=['GET'])
@login_required
def my_records(current_user):
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    result = return_service.get_user_borrow_records(current_user.id, page, per_page)
    return paginated(**result)
