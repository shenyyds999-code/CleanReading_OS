import os
from dotenv import load_dotenv

load_dotenv()


class Config:
    SECRET_KEY = os.getenv('SECRET_KEY', 'dev-secret-key')
    JWT_SECRET_KEY = os.getenv('JWT_SECRET_KEY', 'dev-jwt-secret')
    JWT_EXPIRATION_HOURS = int(os.getenv('JWT_EXPIRATION_HOURS', '24'))

    SQLALCHEMY_DATABASE_URI = os.getenv('DATABASE_URL', 'mysql+pymysql://root:password@127.0.0.1:3306/library_system')
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    REDIS_URL = os.getenv('REDIS_URL', 'redis://127.0.0.1:6379/0')
    REDIS_ENABLED = os.getenv('REDIS_ENABLED', 'true').lower() == 'true'
    REDIS_CONNECT_TIMEOUT = int(os.getenv('REDIS_CONNECT_TIMEOUT', '3'))
    REDIS_SOCKET_TIMEOUT = int(os.getenv('REDIS_SOCKET_TIMEOUT', '2'))

    CACHE_DEFAULT_TTL = int(os.getenv('CACHE_DEFAULT_TTL', '300'))
    CACHE_USER_TTL = int(os.getenv('CACHE_USER_TTL', '600'))
    CACHE_BOOK_LIST_TTL = int(os.getenv('CACHE_BOOK_LIST_TTL', '120'))

    RATE_LIMIT_ENABLED = os.getenv('RATE_LIMIT_ENABLED', 'true').lower() == 'true'
    RATE_LIMIT_GLOBAL = os.getenv('RATE_LIMIT_GLOBAL', '60/minute')
    RATE_LIMIT_AUTH = os.getenv('RATE_LIMIT_AUTH', '10/minute')

    DEEPSEEK_API_KEY = os.getenv('DEEPSEEK_API_KEY', '')
    DEEPSEEK_BASE_URL = os.getenv('DEEPSEEK_BASE_URL', 'https://api.deepseek.com')

    MAX_CONTENT_LENGTH = 10 * 1024 * 1024
    UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'uploads')
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}

    SCHEDULER_API_ENABLED = True
