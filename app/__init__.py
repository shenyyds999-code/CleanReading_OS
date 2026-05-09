import os
import time
from flask import Flask, send_from_directory, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_cors import CORS
from config import Config

db = SQLAlchemy()
migrate = Migrate()


def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    db.init_app(app)
    migrate.init_app(app, db)
    CORS(app)

    from app import models  # noqa: F401

    from app.api.auth import auth_bp
    app.register_blueprint(auth_bp, url_prefix='/api/auth')

    from app.api.books import books_bp
    app.register_blueprint(books_bp, url_prefix='/api/books')

    from app.api.borrow import borrow_bp
    app.register_blueprint(borrow_bp, url_prefix='/api/borrow')

    from app.api.return_api import return_bp
    app.register_blueprint(return_bp, url_prefix='/api/return')

    from app.api.comment import comment_bp
    app.register_blueprint(comment_bp, url_prefix='/api/comments')

    from app.api.learn import learn_bp
    app.register_blueprint(learn_bp, url_prefix='/api/learn')

    from app.api.ai import ai_bp
    app.register_blueprint(ai_bp, url_prefix='/api/ai')

    from app.api.settings_api import settings_bp
    app.register_blueprint(settings_bp, url_prefix='/api/user/settings')

    from app.api.notification import notification_bp
    app.register_blueprint(notification_bp, url_prefix='/api/notifications')

    from apscheduler.schedulers.background import BackgroundScheduler
    scheduler = BackgroundScheduler(daemon=True)
    scheduler.add_job(
        func=_overdue_job,
        trigger='interval',
        hours=1,
        id='overdue_check',
        replace_existing=True
    )
    scheduler.start()

    @app.route('/api/health')
    def health_check():
        cache_status = 'unknown'
        cache_type = 'none'
        try:
            from app.utils.cache import get_cache, SimpleCache
            cache = get_cache()
            if cache is None:
                cache_status = 'disabled'
                cache_type = 'none'
            elif isinstance(cache, SimpleCache):
                cache_status = 'degraded'
                cache_type = 'in-memory'
            else:
                try:
                    cache.ping()
                    cache_status = 'connected'
                    cache_type = 'redis'
                except Exception:
                    cache_status = 'disconnected'
                    cache_type = 'redis'
        except Exception:
            cache_status = 'error'
            cache_type = 'none'

        return jsonify({
            'code': 200,
            'message': 'ok',
            'data': {
                'status': 'running',
                'timestamp': int(time.time()),
                'cache': {
                    'status': cache_status,
                    'type': cache_type
                },
                'redis_enabled': app.config.get('REDIS_ENABLED', False)
            }
        })

    client_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'client')
    kiosk_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'kiosk')

    @app.route('/')
    @app.route('/client/<path:filename>')
    def serve_client(filename=''):
        if not filename:
            return send_from_directory(client_dir, 'index.html')
        return send_from_directory(client_dir, filename)

    @app.route('/client/')
    def serve_client_index():
        return send_from_directory(client_dir, 'index.html')

    @app.route('/kiosk/<path:filename>')
    def serve_kiosk(filename='index.html'):
        return send_from_directory(kiosk_dir, filename)

    @app.route('/kiosk/')
    def serve_kiosk_index():
        return send_from_directory(kiosk_dir, 'index.html')

    @app.route('/uploads/<path:filename>')
    def serve_uploads(filename):
        upload_folder = app.config.get('UPLOAD_FOLDER', 'uploads')
        return send_from_directory(upload_folder, filename)

    @app.cli.command('seed')
    def seed_data():
        from app.models import User, Book, Title, CreditLog, Notification
        from werkzeug.security import generate_password_hash

        if User.query.first():
            print('数据库已有数据，跳过种子数据插入')
            return

        admin = User(username='admin', password_hash=generate_password_hash('admin123'), role=3, credit_score=5)
        librarian = User(username='librarian', password_hash=generate_password_hash('lib123'), role=2, credit_score=5)
        normal = User(username='reader', password_hash=generate_password_hash('reader123'), role=1, credit_score=5)
        db.session.add_all([admin, librarian, normal])
        db.session.flush()

        books = [
            Book(title='三体', author='刘慈欣', isbn='9787536692930', category='科幻', publisher='重庆出版社',
                 total_copies=5, available_copies=5, location='A-01-01', description='中国科幻文学的里程碑之作'),
            Book(title='活着', author='余华', isbn='9787530215319', category='文学', publisher='北京十月文艺出版社',
                 total_copies=3, available_copies=3, location='A-02-01', description='讲述人如何去承受巨大的苦难'),
            Book(title='百年孤独', author='加西亚·马尔克斯', isbn='9787544253994', category='文学', publisher='南海出版公司',
                 total_copies=4, available_copies=4, location='A-02-02', description='魔幻现实主义文学的代表作'),
            Book(title='深入理解计算机系统', author='Randal E. Bryant', isbn='9787111544937', category='计算机',
                 publisher='机械工业出版社', total_copies=2, available_copies=2, location='B-01-01',
                 description='计算机科学经典教材'),
        ]
        db.session.add_all(books)
        db.session.flush()

        titles = [
            Title(title_name='初识书香', description='首次借阅一本书', obtain_condition_desc='完成首次借阅'),
            Title(title_name='阅读达人', description='累计借阅10本书', obtain_condition_desc='累计借阅10本书'),
            Title(title_name='三体学者', description='通过《三体》答题测验', obtain_condition_desc='《三体》答题正确率≥80%'),
            Title(title_name='文学鉴赏家', description='通过《活着》答题测验', obtain_condition_desc='《活着》答题正确率≥80%'),
        ]
        db.session.add_all(titles)
        db.session.flush()

        from app.models import QuizQuestion
        questions = [
            QuizQuestion(book_id=1, type=1, question_text='《三体》的作者是谁？',
                         options=['刘慈欣', '余华', '莫言', '马伯庸'], correct_answer_text='A', score=10, created_by=1),
            QuizQuestion(book_id=1, type=2, question_text='三体人的母星叫什么名字？（填入名称）',
                         options=None, correct_answer_text='三体星', score=10, created_by=1),
            QuizQuestion(book_id=1, type=3, question_text='请简述《三体》中"黑暗森林法则"的核心思想',
                         options=None, correct_answer_text='宇宙就是一座黑暗森林，每个文明都是带枪的猎人', score=20, created_by=1),
            QuizQuestion(book_id=2, type=1, question_text='《活着》的主角叫什么？',
                         options=['福贵', '许三观', '孙少平', '刘跃进'], correct_answer_text='A', score=10, created_by=1),
            QuizQuestion(book_id=2, type=2, question_text='《活着》的作者是谁？',
                         options=None, correct_answer_text='余华', score=10, created_by=1),
            QuizQuestion(book_id=3, type=1, question_text='《百年孤独》中布恩迪亚家族生活在哪个虚构小镇？',
                         options=['马孔多', '桑塔菲', '奥雷里亚诺', '拉美尼亚'], correct_answer_text='A', score=10, created_by=1),
        ]
        db.session.add_all(questions)

        db.session.commit()
        print('种子数据插入完成！')
        print('  管理员: admin / admin123 (role=3)')
        print('  图书管理员: librarian / lib123 (role=2)')
        print('  读者: reader / reader123 (role=1)')
        print(f'  已插入 {len(books)} 本图书, {len(titles)} 个称号')

    return app


def _overdue_job():
    from app import create_app
    app = create_app()
    with app.app_context():
        from app.services.scheduler_service import check_overdue_and_penalize
        count = check_overdue_and_penalize()
        if count:
            print(f'[Scheduler] 超期扣分完成，共处理 {count} 条记录')
