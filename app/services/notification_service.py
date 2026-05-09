from app.models import Notification
from app import db
from datetime import datetime, timezone


def add_notification(user_id, ntype, title, content, related_id=0):
    notification = Notification(
        user_id=user_id,
        type=ntype,
        title=title,
        content=content,
        related_id=related_id,
        created_at=datetime.now(timezone.utc)
    )
    db.session.add(notification)
    db.session.commit()
    return notification


def get_notifications(user_id, page=1, per_page=20):
    notifications = Notification.query.filter_by(user_id=user_id).order_by(
        Notification.created_at.desc()
    ).paginate(page=page, per_page=per_page, error_out=False)

    unread_count = Notification.query.filter_by(user_id=user_id, is_read=False).count()

    return {
        'items': [_notification_dict(n) for n in notifications],
        'total': notifications.total,
        'page': page,
        'per_page': per_page,
        'unread_count': unread_count
    }


def mark_read(user_id, notification_id):
    notification = Notification.query.filter_by(id=notification_id, user_id=user_id).first()
    if notification:
        notification.is_read = True
        db.session.commit()
        return True
    return False


def mark_all_read(user_id):
    Notification.query.filter_by(user_id=user_id, is_read=False).update({'is_read': True})
    db.session.commit()
    return True


def _notification_dict(n):
    return {
        'id': n.id,
        'type': n.type,
        'title': n.title,
        'content': n.content,
        'is_read': n.is_read,
        'related_id': n.related_id,
        'created_at': n.created_at.strftime('%Y-%m-%d %H:%M:%S')
    }
