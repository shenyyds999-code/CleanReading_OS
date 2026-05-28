from app import db
from datetime import datetime, timezone


class User(db.Model):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    username = db.Column(db.String(80), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(256), nullable=False)
    role = db.Column(db.SmallInteger, nullable=False, default=1)
    credit_score = db.Column(db.SmallInteger, nullable=False, default=5)
    avatar_url = db.Column(db.String(512), default='')
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc),
                           onupdate=lambda: datetime.now(timezone.utc))

    credit_logs = db.relationship('CreditLog', backref='user', lazy='dynamic')
    borrow_records = db.relationship('BorrowRecord', backref='user', lazy='dynamic')
    comments = db.relationship('Comment', backref='user', lazy='dynamic')
    quiz_attempts = db.relationship('QuizAttempt', backref='user', lazy='dynamic')
    user_titles = db.relationship('UserTitle', backref='user', lazy='dynamic')
    donations = db.relationship('Donation', backref='user', lazy='dynamic',
                              foreign_keys='Donation.user_id')
    image_reviews = db.relationship('ImageReview', backref='user', lazy='dynamic',
                                    foreign_keys='ImageReview.user_id')
    settings = db.relationship('UserSetting', backref='user', uselist=False)
    notifications = db.relationship('Notification', backref='user', lazy='dynamic')

    def __repr__(self):
        return f'<User {self.username}>'


class CreditLog(db.Model):
    __tablename__ = 'credit_logs'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    change_amount = db.Column(db.SmallInteger, nullable=False)
    reason = db.Column(db.String(100), nullable=False)
    detail = db.Column(db.String(500), default='')
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    def __repr__(self):
        return f'<CreditLog user={self.user_id} amount={self.change_amount}>'


class Book(db.Model):
    __tablename__ = 'books'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    title = db.Column(db.String(200), nullable=False, index=True)
    author = db.Column(db.String(200), nullable=False)
    isbn = db.Column(db.String(20), unique=True, nullable=False, index=True)
    category = db.Column(db.String(100), default='')
    publisher = db.Column(db.String(200), default='')
    total_copies = db.Column(db.Integer, nullable=False, default=1)
    available_copies = db.Column(db.Integer, nullable=False, default=1)
    location = db.Column(db.String(100), default='')
    cover_image_url = db.Column(db.String(512), default='')
    description = db.Column(db.Text, default='')
    status = db.Column(db.String(20), default='可借')
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc),
                           onupdate=lambda: datetime.now(timezone.utc))

    borrow_records = db.relationship('BorrowRecord', backref='book', lazy='dynamic')
    comments = db.relationship('Comment', backref='book', lazy='dynamic')
    quiz_questions = db.relationship('QuizQuestion', backref='book', lazy='dynamic')
    quiz_attempts = db.relationship('QuizAttempt', backref='book', lazy='dynamic')
    ratings = db.relationship('BookRating', backref='book', lazy='dynamic', cascade='all, delete-orphan')

    def __repr__(self):
        return f'<Book {self.title}>'


class BookRating(db.Model):
    __tablename__ = 'book_ratings'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    book_id = db.Column(db.Integer, db.ForeignKey('books.id'), nullable=False, index=True)
    rating = db.Column(db.SmallInteger, nullable=False)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    __table_args__ = (db.UniqueConstraint('user_id', 'book_id'),)

    def __repr__(self):
        return f'<BookRating user={self.user_id} book={self.book_id} rating={self.rating}>'


class BorrowRecord(db.Model):
    __tablename__ = 'borrow_records'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    book_id = db.Column(db.Integer, db.ForeignKey('books.id'), nullable=False, index=True)
    borrow_date = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    due_date = db.Column(db.DateTime, nullable=False)
    return_date = db.Column(db.DateTime, nullable=True)
    status = db.Column(db.String(20), nullable=False, default='借阅中')
    admin_check_status = db.Column(db.String(20), default='')
    before_return_image_urls = db.Column(db.JSON, default=list)
    damage_level = db.Column(db.String(10), nullable=True)
    fine_score = db.Column(db.SmallInteger, default=0)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc),
                           onupdate=lambda: datetime.now(timezone.utc))

    def __repr__(self):
        return f'<BorrowRecord user={self.user_id} book={self.book_id}>'


class Comment(db.Model):
    __tablename__ = 'comments'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    book_id = db.Column(db.Integer, db.ForeignKey('books.id'), nullable=False, index=True)
    content = db.Column(db.Text, nullable=False)
    image_urls = db.Column(db.JSON, default=list)
    parent_id = db.Column(db.Integer, db.ForeignKey('comments.id'), nullable=True, index=True)
    like_count = db.Column(db.Integer, default=0)
    is_reported = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    replies = db.relationship('Comment', backref=db.backref('parent', remote_side=[id]), lazy='dynamic')
    likes = db.relationship('CommentLike', backref='comment', lazy='dynamic', cascade='all, delete-orphan')

    def __repr__(self):
        return f'<Comment user={self.user_id} book={self.book_id}>'


class CommentLike(db.Model):
    __tablename__ = 'comment_likes'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    comment_id = db.Column(db.Integer, db.ForeignKey('comments.id'), nullable=False, index=True)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    __table_args__ = (db.UniqueConstraint('user_id', 'comment_id'),)

    def __repr__(self):
        return f'<CommentLike user={self.user_id} comment={self.comment_id}>'


class QuizQuestion(db.Model):
    __tablename__ = 'quiz_questions'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    book_id = db.Column(db.Integer, db.ForeignKey('books.id'), nullable=False, index=True)
    type = db.Column(db.SmallInteger, nullable=False)
    question_text = db.Column(db.Text, nullable=False)
    options = db.Column(db.JSON, nullable=True)
    correct_answer_text = db.Column(db.Text, nullable=False)
    score = db.Column(db.Integer, default=10)
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc),
                           onupdate=lambda: datetime.now(timezone.utc))

    def __repr__(self):
        return f'<QuizQuestion book={self.book_id} type={self.type}>'


class QuizAttempt(db.Model):
    __tablename__ = 'quiz_attempts'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    book_id = db.Column(db.Integer, db.ForeignKey('books.id'), nullable=False, index=True)
    score_rate = db.Column(db.Float, nullable=False)
    passed = db.Column(db.SmallInteger, nullable=False, default=0)
    attempt_detail = db.Column(db.JSON, default=dict)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    def __repr__(self):
        return f'<QuizAttempt user={self.user_id} book={self.book_id}>'


class Title(db.Model):
    __tablename__ = 'titles'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    title_name = db.Column(db.String(100), nullable=False, unique=True)
    description = db.Column(db.String(500), default='')
    obtain_condition_desc = db.Column(db.String(500), default='')
    icon_url = db.Column(db.String(512), default='')
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    user_titles = db.relationship('UserTitle', backref='title', lazy='dynamic')

    def __repr__(self):
        return f'<Title {self.title_name}>'


class UserTitle(db.Model):
    __tablename__ = 'user_titles'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    title_id = db.Column(db.Integer, db.ForeignKey('titles.id'), nullable=False, index=True)
    obtained_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    def __repr__(self):
        return f'<UserTitle user={self.user_id} title={self.title_id}>'


class Donation(db.Model):
    __tablename__ = 'donations'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    book_title = db.Column(db.String(200), nullable=False)
    damage_desc = db.Column(db.Text, default='')
    image_urls = db.Column(db.JSON, default=list)
    status = db.Column(db.String(20), nullable=False, default='待审核')
    admin_remark = db.Column(db.Text, default='')
    created_by_admin = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc),
                           onupdate=lambda: datetime.now(timezone.utc))

    def __repr__(self):
        return f'<Donation user={self.user_id} status={self.status}>'


class ImageReview(db.Model):
    __tablename__ = 'image_reviews'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    image_type = db.Column(db.String(20), nullable=False)
    image_url = db.Column(db.String(512), nullable=False)
    status = db.Column(db.String(20), nullable=False, default='待审核')
    reviewer_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc),
                           onupdate=lambda: datetime.now(timezone.utc))

    def __repr__(self):
        return f'<ImageReview user={self.user_id} type={self.image_type} status={self.status}>'


class UserSetting(db.Model):
    __tablename__ = 'user_settings'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), unique=True, nullable=False, index=True)
    background_image_url = db.Column(db.String(512), default='')
    theme_color = db.Column(db.String(20), default='#0d6efd')
    learning_trigger_mode = db.Column(db.String(20), default='主动')
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc),
                           onupdate=lambda: datetime.now(timezone.utc))

    def __repr__(self):
        return f'<UserSetting user={self.user_id}>'


class Notification(db.Model):
    __tablename__ = 'notifications'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    type = db.Column(db.String(50), nullable=False)
    title = db.Column(db.String(200), nullable=False)
    content = db.Column(db.Text, default='')
    is_read = db.Column(db.Boolean, default=False, index=True)
    related_id = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    def __repr__(self):
        return f'<Notification user={self.user_id} type={self.type} read={self.is_read}>'


class SystemConfig(db.Model):
    __tablename__ = 'system_config'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    config_key = db.Column(db.String(100), unique=True, nullable=False, index=True)
    config_value = db.Column(db.Text, default='')
    updated_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc),
                           onupdate=lambda: datetime.now(timezone.utc))

    def __repr__(self):
        return f'<SystemConfig {self.config_key}={self.config_value}>'
