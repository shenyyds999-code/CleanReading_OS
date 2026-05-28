from app.models import Book
from app import db
from sqlalchemy import or_
import requests


import os
import base64
import io
from PIL import Image


def openlibrary_cover_url(isbn, size='M'):
    if not isbn:
        return ''
    return f'https://covers.openlibrary.org/b/isbn/{isbn}-{size}.jpg'


def isbn_lookup(isbn):
    isbn = (isbn or '').strip()
    if not isbn:
        return None, 'ISBN不能为空', None

    try:
        resp = requests.get(
            f'https://openlibrary.org/isbn/{isbn}.json',
            timeout=(3, 5),
            headers={'User-Agent': 'ClearReading/1.0'}
        )
        if resp.status_code == 404:
            return None, '未找到该ISBN对应的图书信息', None
        resp.raise_for_status()
        data = resp.json()
    except requests.Timeout:
        return None, '查询超时，请重试', None
    except requests.RequestException:
        return None, '查询OpenLibrary失败，请检查网络', None

    result = {
        'isbn': isbn,
        'title': data.get('title', ''),
        'author': '',
        'publisher': '',
        'cover_url': openlibrary_cover_url(isbn, 'M'),
    }

    authors = data.get('authors', [])
    if authors:
        result['author'] = authors[0].get('name', '')

    publishers = data.get('publishers', [])
    if publishers:
        result['publisher'] = publishers[0]

    return result, None, None


def search_cover_by_isbn(isbn):
    """搜索封面图，返回图片URL列表"""
    isbn = (isbn or '').strip()
    if not isbn:
        return [], 'ISBN不能为空'

    cover_urls = []

    ol_url = openlibrary_cover_url(isbn, 'L')
    if ol_url:
        cover_urls.append(ol_url)

    if not cover_urls:
        return [], '未找到封面'

    return cover_urls, None


def download_cover(url):
    """下载封面图，返回base64编码的图片"""
    try:
        resp = requests.get(url, timeout=10, headers={
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        })
        resp.raise_for_status()

        img = Image.open(io.BytesIO(resp.content))
        img = img.convert('RGB')
        img.thumbnail((400, 600))

        buf = io.BytesIO()
        img.save(buf, format='JPEG', quality=85)
        img_b64 = base64.b64encode(buf.getvalue()).decode('utf-8')

        return img_b64, None
    except Exception as e:
        return None, str(e)


def search_books(query='', search_type='fuzzy', page=1, per_page=20):
    q = Book.query

    if query:
        if search_type == 'exact':
            q = q.filter(or_(
                Book.title == query,
                Book.isbn == query,
                Book.author == query
            ))
        else:
            pattern = f'%{query}%'
            q = q.filter(or_(
                Book.title.like(pattern),
                Book.author.like(pattern),
                Book.isbn.like(pattern),
                Book.category.like(pattern),
                Book.publisher.like(pattern)
            ))

    total = q.count()
    items = q.order_by(Book.created_at.desc()).paginate(page=page, per_page=per_page, error_out=False)

    return {
        'items': [_book_dict(b) for b in items],
        'total': total,
        'page': page,
        'per_page': per_page
    }


def get_book(book_id, user_id=None):
    book = db.session.get(Book, book_id)
    if not book:
        return None
    return _book_dict(book, user_id)


def get_popular_books(limit=8, user_id=None):
    from app.models import BorrowRecord
    from sqlalchemy import func
    popular = (
        db.session.query(
            Book.id,
            Book.title,
            Book.author,
            Book.isbn,
            func.count(BorrowRecord.id).label('borrow_count')
        )
        .outerjoin(BorrowRecord, BorrowRecord.book_id == Book.id)
        .group_by(Book.id)
        .order_by(func.count(BorrowRecord.id).desc())
        .limit(limit)
        .all()
    )
    result = []
    for p in popular:
        book = db.session.get(Book, p.id)
        d = _book_dict(book)
        d['borrow_count'] = p.borrow_count
        d['user_borrow_count'] = 0
        if user_id:
            d['user_borrow_count'] = BorrowRecord.query.filter_by(
                user_id=user_id, book_id=p.id, status='借阅中'
            ).count()
        result.append(d)
    result.sort(key=lambda x: x['borrow_count'], reverse=True)
    return result


def _book_dict(book, user_id=None):
    ol_cover = openlibrary_cover_url(book.isbn, 'M')
    avg_rating, user_rating = get_book_rating(book.id, user_id)
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
        'openlibrary_cover': ol_cover,
        'description': book.description,
        'status': book.status,
        'can_borrow': book.available_copies > 0 and book.status == '可借',
        'avg_rating': avg_rating,
        'user_rating': user_rating
    }


def get_book_rating(book_id, user_id=None):
    from app.models import BookRating
    from sqlalchemy import func
    result = db.session.query(func.avg(BookRating.rating)).filter_by(book_id=book_id).scalar()
    avg_rating = round(float(result), 1) if result else 0
    user_rating = None
    if user_id:
        user_rating_record = BookRating.query.filter_by(book_id=book_id, user_id=user_id).first()
        if user_rating_record:
            user_rating = user_rating_record.rating
    return avg_rating, user_rating


def rate_book(user_id, book_id, rating):
    from app.models import BookRating
    if rating < 1 or rating > 5:
        return None, '评分必须在1-5之间'
    book = db.session.get(Book, book_id)
    if not book:
        return None, '图书不存在'
    existing = BookRating.query.filter_by(user_id=user_id, book_id=book_id).first()
    if existing:
        existing.rating = rating
    else:
        new_rating = BookRating(user_id=user_id, book_id=book_id, rating=rating)
        db.session.add(new_rating)
    db.session.commit()
    avg_rating, _ = get_book_rating(book_id)
    return {'avg_rating': avg_rating, 'user_rating': rating}, None


def get_random_books(exclude_ids=None, limit=4):
    from sqlalchemy import func
    query = Book.query
    if exclude_ids:
        query = query.filter(~Book.id.in_(exclude_ids))
    books = query.order_by(func.random()).limit(limit).all()
    return [_book_dict(b) for b in books]
