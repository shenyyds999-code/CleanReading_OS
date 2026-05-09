from app.models import User
from app import db
from werkzeug.security import generate_password_hash, check_password_hash
from app.utils.security import sanitize_html


def register_user(username, password, role=1):
    username = sanitize_html(username.strip())
    if not username or len(username) < 2 or len(username) > 80:
        return None, '用户名长度需在2-80个字符之间'

    if not password or len(password) < 6:
        return None, '密码长度至少6位'

    existing = User.query.filter_by(username=username).first()
    if existing:
        return None, '用户名已被注册'

    if role not in (1, 2, 3):
        role = 1

    user = User(
        username=username,
        password_hash=generate_password_hash(password),
        role=role,
        credit_score=5
    )
    db.session.add(user)
    db.session.commit()
    return user, None


def login_user(username, password):
    username = sanitize_html(username.strip())
    if not username or not password:
        return None, '用户名和密码不能为空'

    user = User.query.filter_by(username=username).first()
    if not user:
        return None, '用户名或密码错误'

    if not check_password_hash(user.password_hash, password):
        return None, '用户名或密码错误'

    return user, None
