from app.models import User, Book, BorrowRecord, CreditLog, Notification
from app import db
from datetime import datetime, timezone, timedelta


def _get_borrow_limit(credit_score):
    if credit_score >= 5:
        return {'max_books': 4, 'days': 31}
    elif credit_score >= 3:
        return {'max_books': 2, 'days': 15}
    else:
        return {'max_books': 0, 'days': 0}


def check_can_borrow(user, book):
    limit = _get_borrow_limit(user.credit_score)
    if limit['max_books'] == 0:
        return None, '信誉分不足，无法借书', 1001

    if book.available_copies <= 0:
        return None, '该图书暂无可借副本', 1003

    if book.status != '可借':
        return None, '该图书当前不可借', 1003

    active_count = BorrowRecord.query.filter_by(
        user_id=user.id, status='借阅中'
    ).count()

    if active_count >= limit['max_books']:
        return None, f'借阅数量已达上限（{limit["max_books"]}本）', 1002

    return limit, None, None


def borrow_book(user, book):
    limit, err, code = check_can_borrow(user, book)
    if err:
        return None, err, code

    due_date = datetime.now(timezone.utc) + timedelta(days=limit['days'])

    record = BorrowRecord(
        user_id=user.id,
        book_id=book.id,
        borrow_date=datetime.now(timezone.utc),
        due_date=due_date,
        status='借阅中'
    )
    book.available_copies -= 1
    if book.available_copies <= 0:
        book.status = '已借完'

    db.session.add(record)
    db.session.commit()

    return {
        'record_id': record.id,
        'book_id': book.id,
        'book_title': book.title,
        'borrow_date': record.borrow_date.strftime('%Y-%m-%d %H:%M:%S'),
        'due_date': record.due_date.strftime('%Y-%m-%d %H:%M:%S'),
        'borrow_days': limit['days'],
        'remaining_quota': limit['max_books'] - 1 - BorrowRecord.query.filter_by(
            user_id=user.id, status='借阅中'
        ).count()
    }, None, None
