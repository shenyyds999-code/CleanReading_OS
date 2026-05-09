from app.models import Book
from app import db
from sqlalchemy import or_


def openlibrary_cover_url(isbn, size='M'):
    if not isbn:
        return ''
    return f'https://covers.openlibrary.org/b/isbn/{isbn}-{size}.jpg'


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


def get_popular_books(limit=8):
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
