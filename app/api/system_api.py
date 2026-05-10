from flask import Blueprint, request
from app.services import system_service
from app.utils.response import success, error
from app.utils.jwt_helper import admin_required

system_bp = Blueprint('system', __name__)


@system_bp.route('/config', methods=['GET'])
def get_config():
    site_name = system_service.get_config('site_name')
    return success({'site_name': site_name})


@system_bp.route('/config', methods=['PUT'])
@admin_required
def update_config(current_user):
    data = request.get_json(silent=True)
    if not data:
        return error(400, '请提供有效的JSON数据')

    site_name = data.get('site_name', '').strip()
    if not site_name:
        return error(400, '站点名称不能为空')

    system_service.set_config('site_name', site_name)
    return success({'site_name': site_name}, '站点名称已更新')
