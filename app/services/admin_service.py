from app.models import User, Book, BorrowRecord, Comment, Donation, ImageReview, CreditLog, Notification
from app import db
from datetime import datetime, timezone
from sqlalchemy import func


def get_dashboard_stats():
    total_users = User.query.count()
    total_books = Book.query.count()
    total_borrowing = BorrowRecord.query.filter_by(status='借阅中').count()
    pending_returns = BorrowRecord.query.filter_by(status='已提交归还').count()
    pending_donations = Donation.query.filter_by(status='待审核').count()
    pending_images = ImageReview.query.filter_by(status='待审核').count()
    reported_comments = Comment.query.filter_by(is_reported=True).count()
    overdue_count = BorrowRecord.query.filter(
        BorrowRecord.status == '借阅中',
        BorrowRecord.due_date < datetime.now(timezone.utc)
    ).count()

    return {
        'total_users': total_users,
        'total_books': total_books,
        'total_borrowing': total_borrowing,
        'pending_returns': pending_returns,
        'pending_donations': pending_donations,
        'pending_images': pending_images,
        'reported_comments': reported_comments,
        'overdue_count': overdue_count
    }


def list_books(page=1, per_page=20, search=''):
    query = Book.query
    if search:
        query = query.filter(
            Book.title.contains(search) | Book.author.contains(search) | Book.isbn.contains(search)
        )
    pagination = query.order_by(Book.id.desc()).paginate(page=page, per_page=per_page, error_out=False)
    return {
        'items': [_book_dict(b) for b in pagination.items],
        'total': pagination.total,
        'page': page,
        'per_page': per_page
    }


def create_book(data):
    isbn = data.get('isbn', '').strip()
    if isbn:
        existing = Book.query.filter_by(isbn=isbn).first()
        if existing:
            return None, '该ISBN已存在', 400

    book = Book(
        title=data.get('title', '').strip(),
        author=data.get('author', '').strip(),
        isbn=isbn,
        category=data.get('category', ''),
        publisher=data.get('publisher', ''),
        total_copies=data.get('total_copies', 1),
        available_copies=data.get('available_copies', data.get('total_copies', 1)),
        location=data.get('location', ''),
        cover_image_url=data.get('cover_image_url', ''),
        description=data.get('description', ''),
        status='可借'
    )
    if book.available_copies <= 0:
        book.status = '已借完'

    db.session.add(book)
    db.session.commit()
    return _book_dict(book), None, None


def update_book(book_id, data):
    book = db.session.get(Book, book_id)
    if not book:
        return None, '图书不存在', 404

    if 'title' in data:
        book.title = data['title'].strip()
    if 'author' in data:
        book.author = data['author'].strip()
    if 'isbn' in data:
        new_isbn = data['isbn'].strip()
        if new_isbn and new_isbn != book.isbn:
            existing = Book.query.filter_by(isbn=new_isbn).first()
            if existing and existing.id != book.id:
                return None, '该ISBN已被其他图书使用', 400
        book.isbn = new_isbn
    if 'category' in data:
        book.category = data['category']
    if 'publisher' in data:
        book.publisher = data['publisher']
    if 'total_copies' in data:
        new_total = data['total_copies']
        diff = new_total - book.total_copies
        book.total_copies = new_total
        book.available_copies = max(0, book.available_copies + diff)
    if 'location' in data:
        book.location = data['location']
    if 'cover_image_url' in data:
        book.cover_image_url = data['cover_image_url']
    if 'description' in data:
        book.description = data['description']

    if book.available_copies <= 0:
        book.status = '已借完'
    elif book.status == '已借完' and book.available_copies > 0:
        book.status = '可借'

    book.updated_at = datetime.now(timezone.utc)
    db.session.commit()
    return _book_dict(book), None, None


def delete_book(book_id):
    book = db.session.get(Book, book_id)
    if not book:
        return None, '图书不存在', 404

    active_borrows = BorrowRecord.query.filter_by(book_id=book_id, status='借阅中').count()
    if active_borrows > 0:
        return None, f'该图书尚有 {active_borrows} 条在借记录，无法删除', 400

    BorrowRecord.query.filter_by(book_id=book_id).delete()
    Comment.query.filter_by(book_id=book_id).delete()
    db.session.delete(book)
    db.session.commit()
    return {'deleted': book_id}, None, None


def list_users(page=1, per_page=20, search=''):
    query = User.query
    if search:
        query = query.filter(User.username.contains(search))
    pagination = query.order_by(User.id.asc()).paginate(page=page, per_page=per_page, error_out=False)
    return {
        'items': [_user_dict(u) for u in pagination.items],
        'total': pagination.total,
        'page': page,
        'per_page': per_page
    }


def adjust_credit(user_id, amount, reason, detail=''):
    user = db.session.get(User, user_id)
    if not user:
        return None, '用户不存在', 404

    if not reason:
        return None, '必须填写变动原因', 400

    new_score = user.credit_score + amount
    if new_score < 0:
        new_score = 0
    if new_score > 100:
        new_score = 100

    user.credit_score = new_score
    user.updated_at = datetime.now(timezone.utc)

    log = CreditLog(
        user_id=user.id,
        change_amount=amount,
        reason=reason,
        detail=detail
    )
    db.session.add(log)

    notification = Notification(
        user_id=user.id,
        type='信誉分变动',
        title='信誉分已调整',
        content=f'管理员调整了你的信誉分：{amount:+d}分。原因：{reason}。当前信誉分：{new_score}',
        related_id=user.id
    )
    db.session.add(notification)

    db.session.commit()
    return {'user_id': user.id, 'new_score': new_score}, None, None


def list_returns(page=1, per_page=20, status=None):
    query = BorrowRecord.query
    if status:
        query = query.filter_by(status=status)
    else:
        query = query.filter(BorrowRecord.status.in_(['已提交归还', '已归还']))
    pagination = query.order_by(BorrowRecord.updated_at.desc()).paginate(page=page, per_page=per_page, error_out=False)

    items = []
    for r in pagination.items:
        book = db.session.get(Book, r.book_id)
        user = db.session.get(User, r.user_id)
        items.append({
            'record_id': r.id,
            'user_id': r.user_id,
            'username': user.username if user else '未知',
            'book_id': r.book_id,
            'book_title': book.title if book else '未知',
            'borrow_date': r.borrow_date.strftime('%Y-%m-%d %H:%M:%S'),
            'due_date': r.due_date.strftime('%Y-%m-%d %H:%M:%S'),
            'return_date': r.return_date.strftime('%Y-%m-%d %H:%M:%S') if r.return_date else None,
            'image_urls': r.before_return_image_urls or [],
            'damage_level': r.damage_level,
            'fine_score': r.fine_score,
            'status': r.status
        })

    return {'items': items, 'total': pagination.total, 'page': page, 'per_page': per_page}


def list_donations(page=1, per_page=20, status=None):
    query = Donation.query
    if status:
        query = query.filter_by(status=status)
    pagination = query.order_by(Donation.created_at.desc()).paginate(page=page, per_page=per_page, error_out=False)

    items = []
    for d in pagination.items:
        user = db.session.get(User, d.user_id)
        items.append({
            'id': d.id,
            'user_id': d.user_id,
            'username': user.username if user else '未知',
            'book_title': d.book_title,
            'damage_desc': d.damage_desc,
            'image_urls': d.image_urls or [],
            'status': d.status,
            'admin_remark': d.admin_remark or '',
            'created_at': d.created_at.strftime('%Y-%m-%d %H:%M:%S')
        })

    return {'items': items, 'total': pagination.total, 'page': page, 'per_page': per_page}


def review_donation(donation_id, action, remark=''):
    donation = db.session.get(Donation, donation_id)
    if not donation:
        return None, '捐书记录不存在', 404

    if action == 'approve':
        donation.status = '已审核'
        donation.admin_remark = remark or '审核通过'

        user = db.session.get(User, donation.user_id)
        if user:
            user.credit_score = min(100, user.credit_score + 1)
            log = CreditLog(
                user_id=user.id,
                change_amount=1,
                reason='捐书奖励',
                detail=f'捐书《{donation.book_title}》审核通过，+1分'
            )
            db.session.add(log)
            notification = Notification(
                user_id=user.id,
                type='审核通知',
                title='捐书审核通过',
                content=f'你捐赠的《{donation.book_title}》已通过审核，信誉分+1！',
                related_id=donation_id
            )
            db.session.add(notification)

    elif action == 'reject':
        donation.status = '已拒绝'
        donation.admin_remark = remark or '审核不通过'
        notification = Notification(
            user_id=donation.user_id,
            type='审核通知',
            title='捐书审核未通过',
            content=f'你捐赠的《{donation.book_title}》未通过审核。原因：{remark or "未说明"}',
            related_id=donation_id
        )
        db.session.add(notification)
    else:
        return None, '无效的操作', 400

    donation.updated_at = datetime.now(timezone.utc)
    db.session.commit()
    return {'id': donation.id, 'status': donation.status}, None, None


def list_image_reviews(page=1, per_page=20, status=None):
    query = ImageReview.query
    if status:
        query = query.filter_by(status=status)
    pagination = query.order_by(ImageReview.created_at.desc()).paginate(page=page, per_page=per_page, error_out=False)

    items = []
    for ir in pagination.items:
        user = db.session.get(User, ir.user_id)
        reviewer = db.session.get(User, ir.reviewer_id) if ir.reviewer_id else None
        items.append({
            'id': ir.id,
            'user_id': ir.user_id,
            'username': user.username if user else '未知',
            'image_type': ir.image_type,
            'image_url': ir.image_url,
            'status': ir.status,
            'reviewer': reviewer.username if reviewer else None,
            'created_at': ir.created_at.strftime('%Y-%m-%d %H:%M:%S')
        })

    return {'items': items, 'total': pagination.total, 'page': page, 'per_page': per_page}


def review_image(image_id, action, reviewer_id):
    img = db.session.get(ImageReview, image_id)
    if not img:
        return None, '图片审核记录不存在', 404

    if action == 'approve':
        img.status = '已通过'
    elif action == 'reject':
        img.status = '已拒绝'
    else:
        return None, '无效的操作', 400

    img.reviewer_id = reviewer_id
    img.updated_at = datetime.now(timezone.utc)
    db.session.commit()
    return {'id': img.id, 'status': img.status}, None, None


def list_comments(page=1, per_page=20, reported_only=False):
    query = Comment.query
    if reported_only:
        query = query.filter_by(is_reported=True)
    pagination = query.order_by(Comment.created_at.desc()).paginate(page=page, per_page=per_page, error_out=False)

    items = []
    for c in pagination.items:
        book = db.session.get(Book, c.book_id)
        items.append({
            'id': c.id,
            'user_id': c.user_id,
            'username': c.user.username,
            'book_id': c.book_id,
            'book_title': book.title if book else '未知',
            'content': c.content,
            'image_urls': c.image_urls or [],
            'like_count': c.like_count,
            'is_reported': c.is_reported,
            'created_at': c.created_at.strftime('%Y-%m-%d %H:%M:%S')
        })

    return {'items': items, 'total': pagination.total, 'page': page, 'per_page': per_page}


def delete_comment(comment_id):
    comment = db.session.get(Comment, comment_id)
    if not comment:
        return None, '评论不存在', 404

    book = db.session.get(Book, comment.book_id)
    was_reported = comment.is_reported
    user_id = comment.user_id

    if was_reported:
        notification = Notification(
            user_id=user_id,
            type='评论通知',
            title='评论已被移除',
            content=f'你在《{book.title if book else "未知图书"}》下的评论因被举报已被管理员移除。',
            related_id=comment_id
        )
        db.session.add(notification)

    db.session.delete(comment)
    db.session.commit()
    return {'deleted': comment_id}, None, None


def delete_user(user_id):
    user = db.session.get(User, user_id)
    if not user:
        return None, '用户不存在', 404
    if user.role == 3:
        return None, '不能删除超级管理员', 400

    BorrowRecord.query.filter_by(user_id=user_id).delete()
    Comment.query.filter_by(user_id=user_id).delete()
    CreditLog.query.filter_by(user_id=user_id).delete()
    Notification.query.filter_by(user_id=user_id).delete()

    db.session.delete(user)
    db.session.commit()
    return {'deleted': user_id}, None, None


def _book_dict(book):
    from app.services.book_service import openlibrary_cover_url
    ol_cover = openlibrary_cover_url(book.isbn, 'M')
    return {
        'id': book.id,
        'title': book.title,
        'author': book.author,
        'isbn': book.isbn,
        'category': book.category,
        'publisher': book.publisher,
        'total_copies': book.total_copies,
        'available_copies': book.available_copies,
        'location': book.location,
        'cover_image_url': book.cover_image_url or ol_cover,
        'description': book.description,
        'status': book.status,
        'created_at': book.created_at.strftime('%Y-%m-%d %H:%M:%S')
    }


def _user_dict(user):
    borrowing_count = BorrowRecord.query.filter_by(user_id=user.id, status='借阅中').count()
    return {
        'id': user.id,
        'username': user.username,
        'role': user.role,
        'credit_score': user.credit_score,
        'avatar_url': user.avatar_url or '',
        'borrowing_count': borrowing_count,
        'created_at': user.created_at.strftime('%Y-%m-%d %H:%M:%S')
    }
