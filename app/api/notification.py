from flask import Blueprint, request
from app.services import notification_service
from app.utils.response import success, error, paginated
from app.utils.jwt_helper import login_required

notification_bp = Blueprint('notification', __name__)


@notification_bp.route('', methods=['GET'])
@login_required
def get_notifications(current_user):
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)

    result = notification_service.get_notifications(current_user.id, page, per_page)
    return success(result)


@notification_bp.route('/unread-count', methods=['GET'])
@login_required
def unread_count(current_user):
    from app.models import Notification
    count = Notification.query.filter_by(user_id=current_user.id, is_read=False).count()
    return success({'count': count})


@notification_bp.route('/<int:notification_id>/read', methods=['POST'])
@login_required
def mark_read(current_user, notification_id):
    notification_service.mark_read(current_user.id, notification_id)
    return success({}, '已标记为已读')


@notification_bp.route('/read-all', methods=['POST'])
@login_required
def mark_all_read(current_user):
    notification_service.mark_all_read(current_user.id)
    return success({}, '全部标记为已读')
