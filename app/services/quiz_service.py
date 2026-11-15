from app.models import QuizQuestion, QuizAttempt, Title, UserTitle, Book
from app import db
from datetime import datetime, timezone
import random
import requests
from flask import current_app


def get_questions(book_id, limit=5):
    questions = QuizQuestion.query.filter_by(book_id=book_id).all()
    if len(questions) > limit:
        questions = random.sample(questions, limit)

    return [_public_question_dict(q) for q in questions]


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
        is_correct = _check_answer(user_answer, correct, question.type, question.options)
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


def _check_answer(user_answer, correct, qtype, options=None):
    user_answer = (user_answer or '').strip()
    correct = (correct or '').strip()
    if qtype == 1:
        # 兼容两种答案配置：选项文本，或选项字母（A/B/C/D）
        if correct.upper() in ('A', 'B', 'C', 'D') and options:
            idx = ord(correct.upper()) - ord('A')
            if 0 <= idx < len(options):
                return user_answer == str(options[idx]).strip()
        return user_answer.upper() == correct.upper()
    elif qtype == 2:
        return user_answer == correct
    else:
        return len(user_answer) >= 3 and (correct.lower() in user_answer.lower() or user_answer.lower() in correct.lower())


def _public_question_dict(q):
    return {
        'id': q.id,
        'book_id': q.book_id,
        'type': q.type,
        'question_text': q.question_text,
        'options': q.options,
        'score': q.score
    }


def _question_dict(q):
    book_title = None
    if q.book_id:
        book = db.session.get(Book, q.book_id)
        if book:
            book_title = book.title
    return {
        'id': q.id,
        'book_id': q.book_id,
        'book_title': book_title,
        'type': q.type,
        'question_text': q.question_text,
        'options': q.options,
        'correct_answer_text': q.correct_answer_text,
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


def generate_questions_with_ai(book_id, count=5):
    book = db.session.get(Book, book_id)
    if not book:
        return None, '图书不存在'

    api_key = current_app.config.get('DEEPSEEK_API_KEY', '')
    base_url = current_app.config.get('DEEPSEEK_BASE_URL', 'https://api.deepseek.com')

    if not api_key:
        return None, 'AI 暂未配置，请联系管理员'

    system_prompt = (
        '你是一个专业的图书馆题目生成专家。根据提供的图书信息，生成适合测试读者理解程度的选择题。'
        '请生成JSON格式的题目数组，每个题目包含：'
        '1. question_text: 问题文本'
        '2. options: 选项数组（4个选项）'
        '3. correct_answer_text: 正确答案（选项中的文本）'
        '题目应该测试读者对书籍内容、作者、主题的理解。'
    )

    book_info = f"书名：{book.title}，作者：{book.author}，ISBN：{book.isbn}"
    if book.description:
        book_info += f"，简介：{book.description[:200]}"

    try:
        resp = requests.post(
            f'{base_url}/v1/chat/completions',
            headers={
                'Authorization': f'Bearer {api_key}',
                'Content-Type': 'application/json'
            },
            json={
                'model': 'deepseek-chat',
                'messages': [
                    {'role': 'system', 'content': system_prompt},
                    {'role': 'user', 'content': f'请为以下图书生成{count}道选择题：{book_info}'}
                ],
                'max_tokens': 1500,
                'temperature': 0.7
            },
            timeout=30
        )
        data = resp.json()
        content = data['choices'][0]['message']['content']

        import json
        import re
        match = re.search(r'\[.*\]', content, re.DOTALL)
        if match:
            questions_data = json.loads(match.group(0))
        else:
            return None, 'AI 返回格式错误'

        created = []
        for q in questions_data[:count]:
            question = QuizQuestion(
                book_id=book_id,
                type=1,
                question_text=q.get('question_text', ''),
                options=q.get('options', []),
                correct_answer_text=q.get('correct_answer_text', ''),
                score=10,
                created_by=None
            )
            db.session.add(question)
            created.append(question)

        db.session.commit()
        return [_question_dict(q) for q in created], None

    except requests.exceptions.Timeout:
        return None, 'AI 请求超时，请重试'
    except Exception as e:
        return None, f'AI 生成失败：{str(e)[:50]}'


def list_questions(page=1, page_size=20, book_id=None):
    query = QuizQuestion.query
    if book_id:
        query = query.filter_by(book_id=book_id)
    total = query.count()
    questions = query.order_by(QuizQuestion.id.desc()).offset((page - 1) * page_size).limit(page_size).all()
    return [_question_dict(q) for q in questions], total


def delete_question(question_id):
    question = db.session.get(QuizQuestion, question_id)
    if not question:
        return False, '题目不存在'
    db.session.delete(question)
    db.session.commit()
    return True, None
