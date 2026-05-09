from app.models import Comment, ImageReview
from app import db
from app.utils.security import sanitize_html, contains_sensitive
from datetime import datetime, timezone


def create_comment(user, book_id, content, image_urls=None):
    content = sanitize_html(content.strip())
    if not content:
        return None, '评论内容不能为空', 400
    if len(content) > 2000:
        return None, '评论内容不能超过2000字', 400
    if contains_sensitive(content):
        return None, '评论包含敏感词，请修改后重新提交', 1005

    image_urls = image_urls or []

    comment = Comment(
        user_id=user.id,
        book_id=book_id,
        content=content,
        image_urls=image_urls,
        created_at=datetime.now(timezone.utc)
    )
    db.session.add(comment)

    for url in image_urls:
        review = ImageReview(
            user_id=user.id,
            image_type='评论',
            image_url=url,
            status='待审核'
        )
        db.session.add(review)

    db.session.commit()
    return _comment_dict(comment), None, None


def get_comments(book_id, page=1, per_page=20):
    comments = Comment.query.filter_by(book_id=book_id, parent_id=None).order_by(
        Comment.created_at.desc()
    ).paginate(page=page, per_page=per_page, error_out=False)

    items = [_comment_dict(c) for c in comments]
    return {
        'items': items,
        'total': comments.total,
        'page': page,
        'per_page': per_page
    }


def like_comment(user, comment_id):
    comment = Comment.query.get(comment_id)
    if not comment:
        return None, '评论不存在', 404
    comment.like_count += 1
    db.session.commit()
    return _comment_dict(comment), None, None


def report_comment(user, comment_id):
    comment = Comment.query.get(comment_id)
    if not comment:
        return None, '评论不存在', 404
    comment.is_reported = True
    db.session.commit()
    return {'id': comment.id, 'is_reported': True}, None, None


def _comment_dict(comment):
    return {
        'id': comment.id,
        'user_id': comment.user_id,
        'username': comment.user.username,
        'avatar_url': comment.user.avatar_url or '',
        'book_id': comment.book_id,
        'content': comment.content,
        'image_urls': comment.image_urls or [],
        'like_count': comment.like_count,
        'is_reported': comment.is_reported,
        'created_at': comment.created_at.strftime('%Y-%m-%d %H:%M:%S')
    }
