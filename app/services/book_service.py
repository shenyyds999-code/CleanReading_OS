from app.models import Book
from app import db
from sqlalchemy import or_


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


def _book_dict(book):
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
        'cover_image_url': book.cover_image_url,
        'description': book.description,
        'status': book.status,
        'can_borrow': book.available_copies > 0 and book.status == '可借'
    }
