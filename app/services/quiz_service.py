from app.models import QuizQuestion, QuizAttempt, Title, UserTitle, Book
from app import db
from datetime import datetime, timezone
import random


def get_questions(book_id, limit=5):
    questions = QuizQuestion.query.filter_by(book_id=book_id).all()
    if len(questions) > limit:
        questions = random.sample(questions, limit)

    return [_question_dict(q) for q in questions]


def submit_attempt(user, book_id, answers):
    questions = QuizQuestion.query.filter_by(book_id=book_id).all()
    if not questions:
        return None, '该图书暂未添加题目', 400

    question_map = {q.id: q for q in questions}
    total_score = 0
    earned_score = 0
    detail = []

    for ans in answers:
        qid = ans.get('question_id')
        user_answer = ans.get('answer', '').strip()
        question = question_map.get(qid)
        if not question:
            continue
        correct = question.correct_answer_text.strip()
        is_correct = _check_answer(user_answer, correct, question.type)
        score = question.score if is_correct else 0
        total_score += question.score
        earned_score += score
        detail.append({
            'question_id': qid,
            'question_text': question.question_text,
            'user_answer': user_answer,
            'correct_answer': correct,
            'is_correct': is_correct,
            'score': score
        })

    if total_score == 0:
        return None, '未能匹配任何题目', 400

    score_rate = round(earned_score / total_score * 100, 1)
    passed = 1 if score_rate >= 80 else 0

    attempt = QuizAttempt(
        user_id=user.id,
        book_id=book_id,
        score_rate=score_rate,
        passed=passed,
        attempt_detail=detail,
        created_at=datetime.now(timezone.utc)
    )
    db.session.add(attempt)
    db.session.flush()

    new_titles = []
    if passed:
        new_titles = _award_titles(user, book_id)

    db.session.commit()

    return {
        'attempt_id': attempt.id,
        'score_rate': score_rate,
        'passed': passed,
        'total_questions': len(detail),
        'correct_count': sum(1 for d in detail if d['is_correct']),
        'detail': detail,
        'new_titles': new_titles
    }, None, None


def create_question(book_id, qtype, question_text, options, correct_answer_text, score=10, created_by=None):
    question = QuizQuestion(
        book_id=book_id,
        type=qtype,
        question_text=question_text,
        options=options,
        correct_answer_text=correct_answer_text,
        score=score,
        created_by=created_by
    )
    db.session.add(question)
    db.session.commit()
    return _question_dict(question)


def _check_answer(user_answer, correct, qtype):
    if qtype == 1:
        return user_answer.upper() == correct.upper()
    elif qtype == 2:
        return user_answer.strip() == correct.strip()
    else:
        return len(user_answer) >= 3 and (correct.lower() in user_answer.lower() or user_answer.lower() in correct.lower())


def _question_dict(q):
    return {
        'id': q.id,
        'book_id': q.book_id,
        'type': q.type,
        'question_text': q.question_text,
        'options': q.options,
        'score': q.score
    }


def _award_titles(user, book_id):
    book = db.session.get(Book, book_id)
    new_titles = []

    from app.models import BorrowRecord
    borrow_count = BorrowRecord.query.filter_by(user_id=user.id).count()
    from app.models import QuizAttempt
    passed_quizzes = QuizAttempt.query.filter_by(user_id=user.id, passed=1).count()

    title_checks = [
        ('初识书香', borrow_count >= 1),
        ('阅读达人', borrow_count >= 10),
    ]

    if book:
        if book.title == '三体':
            title_checks.append(('三体学者', True))
        elif book.title == '活着':
            title_checks.append(('文学鉴赏家', True))

    for title_name, condition in title_checks:
        if not condition:
            continue
        title = Title.query.filter_by(title_name=title_name).first()
        if not title:
            continue
        existing = UserTitle.query.filter_by(user_id=user.id, title_id=title.id).first()
        if existing:
            continue
        ut = UserTitle(user_id=user.id, title_id=title.id, obtained_at=datetime.now(timezone.utc))
        db.session.add(ut)
        new_titles.append({'id': title.id, 'title_name': title.title_name, 'description': title.description})

    return new_titles


def get_user_titles(user_id):
    user_titles = UserTitle.query.filter_by(user_id=user_id).all()
    return [{
        'id': ut.title_id,
        'title_name': ut.title.title_name,
        'description': ut.title.description,
        'icon_url': ut.title.icon_url or '',
        'obtained_at': ut.obtained_at.strftime('%Y-%m-%d %H:%M:%S')
    } for ut in user_titles]
