from flask import Blueprint, request
from app.services import book_service
from app.utils.response import success, error, paginated
from app.utils.jwt_helper import login_required, _verify_token
from app.utils.kiosk import kiosk_blocked
from app.utils.cache import cache_get, cache_set, cache_delete, CacheKey
from app import db
from app.models import Book
import base64
import os

books_bp = Blueprint('books', __name__)


@books_bp.route('/popular', methods=['GET'])
def popular_books():
    limit = request.args.get('limit', 8, type=int)
    user_id = None
    user, _ = _verify_token()
    if user:
        user_id = user.id
    result = book_service.get_popular_books(limit, user_id=user_id)
    return success({'items': result})


@books_bp.route('', methods=['GET'])
@kiosk_blocked
def search_books():
    q = request.args.get('q', '')
    search_type = request.args.get('type', 'fuzzy')
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)

    cache_key = CacheKey.BOOK_LIST(q, page)
    cached = cache_get(cache_key)
    if cached:
        return paginated(**cached)

    result = book_service.search_books(q, search_type, page, per_page)
    cache_set(cache_key, result, current_app_ttl('CACHE_BOOK_LIST_TTL'))
    return paginated(**result)


@books_bp.route('/isbn-lookup', methods=['GET'])
@login_required
def isbn_lookup(current_user):
    isbn = request.args.get('isbn', '').strip()
    if not isbn:
        return error(400, '请提供ISBN参数')
    result, err, code = book_service.isbn_lookup(isbn)
    if err:
        return error(code or 400, err)
    return success(result)


@books_bp.route('/cover-search', methods=['GET'])
@login_required
def cover_search(current_user):
    isbn = request.args.get('isbn', '').strip()
    if not isbn:
        return error(400, '请提供ISBN参数')
    urls, err = book_service.search_cover_by_isbn(isbn)
    if err:
        return error(400, err)
    return success({'urls': urls})


@books_bp.route('/cover-download', methods=['POST'])
@login_required
def cover_download(current_user):
    data = request.get_json()
    url = data.get('url', '').strip()
    book_id = data.get('book_id')
    if not url:
        return error(400, '请提供封面URL')
    img_b64, err = book_service.download_cover(url)
    if err:
        return error(500, f'下载失败: {err}')
    if book_id:
        book = db.session.get(Book, book_id)
        if book:
            filename = f'cover_{book_id}.jpg'
            upload_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'static', 'uploads', 'covers', filename)
            os.makedirs(os.path.dirname(upload_path), exist_ok=True)
            with open(upload_path, 'wb') as f:
                f.write(base64.b64decode(img_b64))
            book.cover_image_url = f'/static/uploads/covers/{filename}'
            db.session.commit()
            return success({'image_url': book.cover_image_url})
    return success({'image_data': f'data:image/jpeg;base64,{img_b64}'})


@books_bp.route('/<int:book_id>', methods=['GET'])
@kiosk_blocked
def get_book(book_id):
    user, _ = _verify_token()
    user_id = user.id if user else None

    cache_key = CacheKey.BOOK(book_id)
    cached = cache_get(cache_key)
    if cached:
        if user_id:
            _, user_rating = book_service.get_book_rating(book_id, user_id)
            cached['user_rating'] = user_rating
        return success(cached)

    result = book_service.get_book(book_id, user_id)
    if not result:
        return error(404, '图书不存在')

    cache_set(cache_key, result, current_app_ttl('CACHE_BOOK_LIST_TTL'))
    return success(result)


@books_bp.route('/<int:book_id>/rating', methods=['POST'])
@login_required
def rate_book(current_user):
    data = request.get_json()
    rating = data.get('rating')
    if not rating or not isinstance(rating, int) or rating < 1 or rating > 5:
        return error(400, '评分必须是1-5之间的整数')
    result, err = book_service.rate_book(current_user.id, book_id, rating)
    if err:
        return error(400, err)
    return success(result)


@books_bp.route('/<int:book_id>/recommendations', methods=['GET'])
@kiosk_blocked
def book_recommendations(book_id):
    result = book_service.get_random_books(exclude_ids=[book_id], limit=4)
    return success({'items': result})


def current_app_ttl(name):
    from flask import current_app
    return current_app.config.get(name, 300)
