from app.models import User, Book, BorrowRecord, CreditLog, Notification, ImageReview
from app import db
from datetime import datetime, timezone


def submit_return(user, record_id, image_urls):
    if not image_urls or len(image_urls) == 0:
        return None, '还书必须上传照片', 400

    record = BorrowRecord.query.filter_by(id=record_id, user_id=user.id).first()
    if not record:
        return None, '借阅记录不存在', 404

    if record.status != '借阅中':
        return None, '该记录状态异常，无法提交归还', 400

    record.status = '已提交归还'
    record.before_return_image_urls = image_urls
    record.return_date = datetime.now(timezone.utc)
    record.updated_at = datetime.now(timezone.utc)

    for url in image_urls:
        review = ImageReview(
            user_id=user.id,
            image_type='还书快照',
            image_url=url,
            status='待审核'
        )
        db.session.add(review)

    db.session.commit()

    return {
        'record_id': record.id,
        'book_id': record.book_id,
        'status': record.status,
        'image_count': len(image_urls)
    }, None, None


def get_user_borrow_records(user_id, page=1, per_page=20):
    records = BorrowRecord.query.filter_by(user_id=user_id).order_by(
        BorrowRecord.borrow_date.desc()
    ).paginate(page=page, per_page=per_page, error_out=False)

    return {
        'items': [_record_dict(r) for r in records],
        'total': records.total,
        'page': page,
        'per_page': per_page
    }


def _record_dict(record):
    book = Book.query.get(record.book_id)
    return {
        'id': record.id,
        'book_id': record.book_id,
        'book_title': book.title if book else '未知图书',
        'borrow_date': record.borrow_date.strftime('%Y-%m-%d %H:%M:%S'),
        'due_date': record.due_date.strftime('%Y-%m-%d %H:%M:%S'),
        'return_date': record.return_date.strftime('%Y-%m-%d %H:%M:%S') if record.return_date else None,
        'status': record.status,
        'damage_level': record.damage_level,
        'fine_score': record.fine_score
    }
