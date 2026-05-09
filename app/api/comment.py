from flask import Blueprint, request
from app.services import comment_service
from app.utils.response import success, error, paginated
from app.utils.jwt_helper import login_required, admin_required
from app.utils.kiosk import kiosk_blocked

comment_bp = Blueprint('comment', __name__)


@comment_bp.route('', methods=['POST'])
@login_required
@kiosk_blocked
def create_comment(current_user):
    data = request.get_json(silent=True)
    if not data:
        return error(400, '请提供有效的JSON数据')

    book_id = data.get('book_id')
    content = data.get('content', '')
    image_urls = data.get('image_urls', [])

    if not book_id:
        return error(400, '缺少book_id参数')

    result, err, code = comment_service.create_comment(current_user, book_id, content, image_urls)
    if err:
        return error(code or 400, err)
    return success(result, '评论发表成功')


@comment_bp.route('', methods=['GET'])
@kiosk_blocked
def get_comments():
    book_id = request.args.get('book_id', type=int)
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)

    if not book_id:
        return error(400, '缺少book_id参数')

    result = comment_service.get_comments(book_id, page, per_page)
    return paginated(**result)


@comment_bp.route('/<int:comment_id>/like', methods=['POST'])
@login_required
@kiosk_blocked
def like_comment(current_user, comment_id):
    result, err, code = comment_service.like_comment(current_user, comment_id)
    if err:
        return error(code or 400, err)
    return success(result, '点赞成功')


@comment_bp.route('/<int:comment_id>/report', methods=['POST'])
@login_required
@kiosk_blocked
def report_comment(current_user, comment_id):
    result, err, code = comment_service.report_comment(current_user, comment_id)
    if err:
        return error(code or 400, err)
    return success(result, '举报已提交')
