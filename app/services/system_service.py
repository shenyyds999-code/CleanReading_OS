from app.models import SystemConfig
from app import db
from datetime import datetime, timezone


DEFAULTS = {
    'site_name': 'CleanReading OS',
    'allow_register': 'true',
}


def get_config(key):
    config = SystemConfig.query.filter_by(config_key=key).first()
    if config:
        return config.config_value
    return DEFAULTS.get(key, '')


def get_all_config():
    result = dict(DEFAULTS)
    configs = SystemConfig.query.all()
    for c in configs:
        result[c.config_key] = c.config_value
    return result


def set_config(key, value):
    config = SystemConfig.query.filter_by(config_key=key).first()
    if config:
        config.config_value = value
        config.updated_at = datetime.now(timezone.utc)
    else:
        config = SystemConfig(config_key=key, config_value=value)
        db.session.add(config)
    db.session.commit()
    return config.config_value
