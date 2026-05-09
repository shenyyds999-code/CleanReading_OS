from flask import Blueprint, request
from app.services import ai_service
from app.utils.response import success, error
from app.utils.jwt_helper import login_required
from app.utils.kiosk import kiosk_blocked

ai_bp = Blueprint('ai', __name__)


@ai_bp.route('/chat', methods=['POST'])
@login_required
@kiosk_blocked
def chat(current_user):
    data = request.get_json(silent=True)
    if not data:
        return error(400, '请提供有效的JSON数据')

    message = data.get('message', '').strip()
    book_title = data.get('book_title', '').strip()

    if not message:
        return error(400, '消息不能为空')

    reply = ai_service.chat_with_ai(message, book_title)
    return success({'reply': reply})
