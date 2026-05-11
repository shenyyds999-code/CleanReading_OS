from app.models import Book
from app import db
from sqlalchemy import or_
import requests


def openlibrary_cover_url(isbn, size='M'):
    if not isbn:
        return ''
    return f'https://covers.openlibrary.org/b/isbn/{isbn}-{size}.jpg'


def isbn_lookup(isbn):
    isbn = (isbn or '').strip()
    if not isbn:
        return None, 'ISBN不能为空'

    try:
        resp = requests.get(
            f'https://openlibrary.org/isbn/{isbn}.json',
            timeout=(3, 5),
            headers={'User-Agent': 'ClearReading/1.0'}
        )
        if resp.status_code == 404:
            return None, '未找到该ISBN对应的图书信息'
        resp.raise_for_status()
        data = resp.json()
    except requests.Timeout:
        return None, '查询超时，请重试'
    except requests.RequestException:
        return None, '查询OpenLibrary失败，请检查网络'

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


def get_book(book_id):
    book = Book.query.get(book_id)
    if not book:
        return None
    return _book_dict(book)


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
        book = Book.query.get(p.id)
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


def _book_dict(book):
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
        'openlibrary_cover': ol_cover,
        'description': book.description,
        'status': book.status,
        'can_borrow': book.available_copies > 0 and book.status == '可借'
    }
