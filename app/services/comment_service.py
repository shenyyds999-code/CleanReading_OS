from app.models import Comment, CommentLike, ImageReview
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
    return _comment_dict(comment, user.id), None, None


def get_comments(book_id, page=1, per_page=20, current_user_id=None):
    comments = Comment.query.filter_by(book_id=book_id, parent_id=None).order_by(
        Comment.created_at.desc()
    ).paginate(page=page, per_page=per_page, error_out=False)

    items = [_comment_dict(c, current_user_id) for c in comments]
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

    existing = CommentLike.query.filter_by(user_id=user.id, comment_id=comment_id).first()
    if existing:
        db.session.delete(existing)
        comment.like_count = max(0, comment.like_count - 1)
        db.session.commit()
        return {'id': comment.id, 'like_count': comment.like_count, 'is_liked': False}, None, None

    like = CommentLike(user_id=user.id, comment_id=comment_id)
    db.session.add(like)
    comment.like_count += 1
    db.session.commit()
    return {'id': comment.id, 'like_count': comment.like_count, 'is_liked': True}, None, None


def report_comment(user, comment_id):
    comment = Comment.query.get(comment_id)
    if not comment:
        return None, '评论不存在', 404
    comment.is_reported = True
    db.session.commit()
    return {'id': comment.id, 'is_reported': True}, None, None


def delete_comment(user, comment_id):
    comment = Comment.query.get(comment_id)
    if not comment:
        return None, '评论不存在', 404
    if comment.user_id != user.id and user.role not in (2, 3):
        return None, '无权删除他人评论', 403
    db.session.delete(comment)
    db.session.commit()
    return {'deleted': comment_id}, None, None


def _comment_dict(comment, current_user_id=None):
    is_liked = False
    if current_user_id:
        is_liked = CommentLike.query.filter_by(
            user_id=current_user_id, comment_id=comment.id
        ).first() is not None
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
        'is_liked': is_liked,
        'created_at': comment.created_at.strftime('%Y-%m-%d %H:%M:%S')
    }
