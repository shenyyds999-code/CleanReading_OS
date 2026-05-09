from app.models import UserSetting, ImageReview
from app import db
from datetime import datetime, timezone


def get_settings(user):
    settings = UserSetting.query.filter_by(user_id=user.id).first()
    if not settings:
        settings = UserSetting(user_id=user.id)
        db.session.add(settings)
        db.session.commit()
    return {
        'background_image_url': settings.background_image_url or '',
        'theme_color': settings.theme_color or '#0d6efd',
        'learning_trigger_mode': settings.learning_trigger_mode or '主动'
    }


def update_settings(user, data):
    settings = UserSetting.query.filter_by(user_id=user.id).first()
    if not settings:
        settings = UserSetting(user_id=user.id)
        db.session.add(settings)

    if 'theme_color' in data:
        color = data['theme_color']
        if color.startswith('#') and len(color) == 7:
            settings.theme_color = color

    if 'background_image_url' in data:
        url = data['background_image_url']
        settings.background_image_url = url
        if url:
            review = ImageReview(
                user_id=user.id,
                image_type='背景',
                image_url=url,
                status='待审核'
            )
            db.session.add(review)

    if 'learning_trigger_mode' in data:
        mode = data['learning_trigger_mode']
        if mode in ('主动', '自动'):
            settings.learning_trigger_mode = mode

    settings.updated_at = datetime.now(timezone.utc)
    db.session.commit()

    return {
        'background_image_url': settings.background_image_url or '',
        'theme_color': settings.theme_color,
        'learning_trigger_mode': settings.learning_trigger_mode
    }
