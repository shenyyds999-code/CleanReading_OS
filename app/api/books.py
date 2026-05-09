from flask import Blueprint, request
from app.services import book_service
from app.utils.response import success, error, paginated
from app.utils.jwt_helper import login_required
from app.utils.kiosk import kiosk_blocked
from app.utils.cache import cache_get, cache_set, cache_delete, CacheKey

books_bp = Blueprint('books', __name__)


@books_bp.route('/popular', methods=['GET'])
def popular_books():
    limit = request.args.get('limit', 8, type=int)
    result = book_service.get_popular_books(limit)
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


@books_bp.route('/<int:book_id>', methods=['GET'])
@kiosk_blocked
def get_book(book_id):
    cache_key = CacheKey.BOOK(book_id)
    cached = cache_get(cache_key)
    if cached:
        return success(cached)

    result = book_service.get_book(book_id)
    if not result:
        return error(404, '图书不存在')

    cache_set(cache_key, result, current_app_ttl('CACHE_BOOK_LIST_TTL'))
    return success(result)


def current_app_ttl(name):
    from flask import current_app
    return current_app.config.get(name, 300)
