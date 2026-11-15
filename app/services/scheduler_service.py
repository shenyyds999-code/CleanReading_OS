from datetime import datetime, timezone, timedelta
from app import db
from app.models import BorrowRecord, User, CreditLog, Notification
from app.utils.cache import cache_delete, CacheKey


def check_overdue_and_penalize():
    now = datetime.now(timezone.utc)

    overdue_records = BorrowRecord.query.filter(
        BorrowRecord.status == '借阅中',
        BorrowRecord.due_date < now
    ).all()

    penalized_count = 0
    for record in overdue_records:
        days_overdue = (now - record.due_date).days
        weeks_overdue = days_overdue // 7

        expected_deductions = weeks_overdue

        # 只统计当前这本超期图书的扣分记录，避免多本超期图书互相抵消
        credit_logs = CreditLog.query.filter(
            CreditLog.user_id == record.user_id,
            CreditLog.reason == '超期扣分',
            CreditLog.detail.like(f'图书《{record.book.title}》超期%'),
            CreditLog.created_at >= record.due_date
        ).count()

        deductions_to_apply = expected_deductions - credit_logs
        if deductions_to_apply <= 0:
            continue

        user = db.session.get(User, record.user_id)
        if not user:
            continue

        actual_deduct = min(deductions_to_apply, user.credit_score)

        user.credit_score -= actual_deduct
        user.updated_at = now

        log = CreditLog(
            user_id=user.id,
            change_amount=-actual_deduct,
            reason='超期扣分',
            detail=f'图书《{record.book.title}》超期{days_overdue}天，自动扣除{actual_deduct}分'
        )
        db.session.add(log)

        notification = Notification(
            user_id=user.id,
            type='扣分通知',
            title='信誉分扣除提醒',
            content=f'您借阅的《{record.book.title}》已超期{days_overdue}天，系统自动扣除{actual_deduct}分。当前信誉分：{user.credit_score}',
            related_id=record.id
        )
        db.session.add(notification)

        cache_delete(CacheKey.USER(user.id))
        penalized_count += 1

    db.session.commit()
    return penalized_count
