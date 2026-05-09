import os
import uuid
from flask import Blueprint, request, current_app
from app.services import settings_service
from app.utils.response import success, error
from app.utils.jwt_helper import login_required
from app.utils.kiosk import kiosk_blocked

settings_bp = Blueprint('settings', __name__)

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}


def _allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


@settings_bp.route('', methods=['GET'])
@login_required
@kiosk_blocked
def get_settings(current_user):
    result = settings_service.get_settings(current_user)
    return success(result)


@settings_bp.route('', methods=['POST'])
@login_required
@kiosk_blocked
def update_settings(current_user):
    data = {}
    if request.is_json:
        data = request.get_json(silent=True) or {}

    if 'theme_color' in request.form:
        data['theme_color'] = request.form['theme_color']

    if 'learning_trigger_mode' in request.form:
        data['learning_trigger_mode'] = request.form['learning_trigger_mode']

    if 'background_image' in request.files:
        f = request.files['background_image']
        if f and f.filename and _allowed_file(f.filename):
            upload_folder = current_app.config.get('UPLOAD_FOLDER', 'uploads')
            os.makedirs(upload_folder, exist_ok=True)
            ext = f.filename.rsplit('.', 1)[1].lower()
            safe_name = f'{uuid.uuid4().hex}.{ext}'
            filepath = os.path.join(upload_folder, safe_name)
            f.save(filepath)
            data['background_image_url'] = f'/uploads/{safe_name}'

    if not data:
        return error(400, '请提供要更新的设置项')

    result = settings_service.update_settings(current_user, data)
    return success(result, '设置已更新')
