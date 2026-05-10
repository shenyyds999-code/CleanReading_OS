from flask import Blueprint, request
from app.services import admin_service
from app.utils.response import success, error, paginated
from app.utils.jwt_helper import admin_required, super_admin_required
from app.utils.cache import cache_delete, CacheKey

admin_bp = Blueprint('admin', __name__)


@admin_bp.route('/stats', methods=['GET'])
@admin_required
def dashboard_stats(current_user):
    result = admin_service.get_dashboard_stats()
    result['role'] = current_user.role
    return success(result)


@admin_bp.route('/books', methods=['GET'])
@admin_required
def list_books(current_user):
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    search = request.args.get('q', '')
    result = admin_service.list_books(page, per_page, search)
    return paginated(**result)


@admin_bp.route('/books', methods=['POST'])
@admin_required
def create_book(current_user):
    data = request.get_json(silent=True)
    if not data:
        return error(400, '请提供有效的JSON数据')
    if not data.get('title') or not data.get('author'):
        return error(400, '书名和作者为必填项')
    result, err, code = admin_service.create_book(data)
    if err:
        return error(code or 400, err)
    return success(result, '图书添加成功')


@admin_bp.route('/books/<int:book_id>', methods=['PUT'])
@admin_required
def update_book(current_user, book_id):
    data = request.get_json(silent=True)
    if not data:
        return error(400, '请提供有效的JSON数据')
    result, err, code = admin_service.update_book(book_id, data)
    if err:
        return error(code or 400, err)
    cache_delete(CacheKey.BOOK(book_id))
    return success(result, '图书更新成功')


@admin_bp.route('/books/<int:book_id>', methods=['DELETE'])
@admin_required
def delete_book(current_user, book_id):
    result, err, code = admin_service.delete_book(book_id)
    if err:
        return error(code or 400, err)
    cache_delete(CacheKey.BOOK(book_id))
    return success(result, '图书已删除')


@admin_bp.route('/users', methods=['GET'])
@super_admin_required
def list_users(current_user):
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    search = request.args.get('q', '')
    result = admin_service.list_users(page, per_page, search)
    return paginated(**result)


@admin_bp.route('/users/credit', methods=['POST'])
@super_admin_required
def adjust_credit(current_user):
    data = request.get_json(silent=True)
    if not data:
        return error(400, '请提供有效的JSON数据')

    user_id = data.get('user_id')
    amount = data.get('amount')
    reason = data.get('reason', '')
    detail = data.get('detail', '')

    if not user_id or amount is None:
        return error(400, '缺少user_id或amount参数')
    if not isinstance(amount, int):
        return error(400, 'amount必须为整数')

    result, err, code = admin_service.adjust_credit(user_id, amount, reason, detail)
    if err:
        return error(code or 400, err)
    cache_delete(CacheKey.USER(user_id))
    return success(result, '信誉分调整成功')


@admin_bp.route('/returns', methods=['GET'])
@admin_required
def list_returns(current_user):
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    status = request.args.get('status', '')
    result = admin_service.list_returns(page, per_page, status or None)
    return paginated(**result)


@admin_bp.route('/donations', methods=['GET'])
@admin_required
def list_donations(current_user):
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    status = request.args.get('status', '')
    result = admin_service.list_donations(page, per_page, status or None)
    return paginated(**result)


@admin_bp.route('/donations/review', methods=['POST'])
@admin_required
def review_donation(current_user):
    data = request.get_json(silent=True)
    if not data:
        return error(400, '请提供有效的JSON数据')

    donation_id = data.get('donation_id')
    action = data.get('action')
    remark = data.get('remark', '')

    if not donation_id or not action:
        return error(400, '缺少donation_id或action参数')

    result, err, code = admin_service.review_donation(donation_id, action, remark)
    if err:
        return error(code or 400, err)
    return success(result, '审核完成')


@admin_bp.route('/images', methods=['GET'])
@admin_required
def list_images(current_user):
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    status = request.args.get('status', '')
    result = admin_service.list_image_reviews(page, per_page, status or None)
    return paginated(**result)


@admin_bp.route('/images/review', methods=['POST'])
@admin_required
def review_image(current_user):
    data = request.get_json(silent=True)
    if not data:
        return error(400, '请提供有效的JSON数据')

    image_id = data.get('image_id')
    action = data.get('action')

    if not image_id or not action:
        return error(400, '缺少image_id或action参数')

    result, err, code = admin_service.review_image(image_id, action, current_user.id)
    if err:
        return error(code or 400, err)
    return success(result, '审核完成')


@admin_bp.route('/comments', methods=['GET'])
@admin_required
def list_comments(current_user):
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    reported_only = request.args.get('reported', '0') == '1'
    result = admin_service.list_comments(page, per_page, reported_only)
    return paginated(**result)


@admin_bp.route('/comments/<int:comment_id>', methods=['DELETE'])
@admin_required
def delete_comment(current_user, comment_id):
    result, err, code = admin_service.delete_comment(comment_id)
    if err:
        return error(code or 400, err)
    return success(result, '评论已删除')
