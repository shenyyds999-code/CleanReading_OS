from flask import Blueprint, request
from app.services import auth_service
from app.utils.response import success, error
from app.utils.jwt_helper import generate_token, login_required, admin_required, revoke_current_token
from app.utils.rate_limiter import rate_limit
from app.utils.cache import cache_get, cache_set, CacheKey
from app.models import User

auth_bp = Blueprint('auth', __name__)


@auth_bp.route('/register', methods=['POST'])
@rate_limit(limit_str='10/minute', key_func=lambda: request.remote_addr or '127.0.0.1')
def register():
    data = request.get_json(silent=True)
    if not data:
        return error(400, '请提供有效的JSON数据')

    username = data.get('username', '')
    password = data.get('password', '')
    role = data.get('role', 1)

    user, err = auth_service.register_user(username, password, role)
    if err:
        return error(400, err)

    token = generate_token(user)
    cache_set(CacheKey.USER(user.id), _user_dict(user), 600)
    return success({
        'token': token,
        'user': _user_dict(user)
    }, '注册成功')


@auth_bp.route('/login', methods=['POST'])
@rate_limit(limit_str='10/minute', key_func=lambda: request.remote_addr or '127.0.0.1')
def login():
    data = request.get_json(silent=True)
    if not data:
        return error(400, '请提供有效的JSON数据')

    username = data.get('username', '')
    password = data.get('password', '')

    user, err = auth_service.login_user(username, password)
    if err:
        return error(401, err)

    token = generate_token(user)
    cache_set(CacheKey.USER(user.id), _user_dict(user), 600)
    return success({
        'token': token,
        'user': _user_dict(user)
    }, '登录成功')


@auth_bp.route('/logout', methods=['POST'])
@login_required
def logout(current_user):
    revoke_current_token()
    cache_delete_key = CacheKey.USER(current_user.id)
    from app.utils.cache import cache_delete
    cache_delete(cache_delete_key)
    return success({}, '已退出登录')


@auth_bp.route('/me', methods=['GET'])
@login_required
def get_me(current_user):
    cache_key = CacheKey.USER(current_user.id)
    cached = cache_get(cache_key)
    if cached:
        return success(cached)

    user_data = _user_dict(current_user)
    cache_set(cache_key, user_data, 600)
    return success(user_data)


def _user_dict(user):
    return {
        'id': user.id,
        'username': user.username,
        'role': user.role,
        'credit_score': user.credit_score,
        'avatar_url': user.avatar_url or ''
    }


@auth_bp.route('/change-username', methods=['POST'])
@login_required
def change_username(current_user):
    data = request.get_json(silent=True)
    if not data:
        return error(400, '请提供有效的JSON数据')

    new_username = data.get('new_username', '')
    user, err = auth_service.change_username(current_user, new_username)
    if err:
        return error(400, err)

    from app.utils.cache import cache_delete
    cache_delete(CacheKey.USER(current_user.id))
    user_data = _user_dict(user)
    cache_set(CacheKey.USER(user.id), user_data, 600)
    return success(user_data, '用户名修改成功')


@auth_bp.route('/change-password', methods=['POST'])
@login_required
def change_password(current_user):
    data = request.get_json(silent=True)
    if not data:
        return error(400, '请提供有效的JSON数据')

    old_password = data.get('old_password', '')
    new_password = data.get('new_password', '')

    user, err = auth_service.change_password(current_user, old_password, new_password)
    if err:
        return error(400, err)

    from app.utils.cache import cache_delete
    cache_delete(CacheKey.USER(current_user.id))
    return success({}, '密码修改成功，请重新登录')
