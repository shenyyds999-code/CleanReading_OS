from flask import Blueprint, request
from app import db
from app.models import Book
from app.services import borrow_service
from app.utils.response import success, error
from app.utils.jwt_helper import login_required
from app.utils.kiosk import kiosk_blocked
from app.utils.cache import cache_delete, CacheKey

borrow_bp = Blueprint('borrow', __name__)


@borrow_bp.route('/status', methods=['GET'])
@login_required
def borrow_status(current_user):
    book_id = request.args.get('book_id', type=int)
    if not book_id:
        return error(400, '缺少book_id参数')
    borrowed = borrow_service.is_book_borrowed_by_user(current_user.id, book_id)
    return success({'book_id': book_id, 'borrowed': borrowed})


@borrow_bp.route('/request', methods=['POST'])
@login_required
@kiosk_blocked
def request_borrow(current_user):
    data = request.get_json(silent=True)
    if not data:
        return error(400, '请提供有效的JSON数据')

    book_id = data.get('book_id')
    if not book_id:
        return error(400, '缺少book_id参数')

    book = Book.query.get(book_id)
    if not book:
        return error(404, '图书不存在')

    result, err, code = borrow_service.borrow_book(current_user, book)
    if err:
        return error(code or 400, err)

    cache_delete(CacheKey.BOOK(book_id))
    cache_delete(CacheKey.USER(current_user.id))
    return success(result, '借书成功')
