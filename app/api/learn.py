from flask import Blueprint, request
from app.services import quiz_service
from app.utils.response import success, error
from app.utils.jwt_helper import login_required, admin_required
from app.utils.kiosk import kiosk_blocked

learn_bp = Blueprint('learn', __name__)


@learn_bp.route('/questions', methods=['GET'])
@login_required
@kiosk_blocked
def get_questions(current_user):
    if current_user.credit_score <= 0:
        return error(1001, '信誉分不足，无法使用学习中心')

    book_id = request.args.get('book_id', type=int)
    if not book_id:
        return error(400, '缺少book_id参数')

    limit = request.args.get('limit', 5, type=int)
    questions = quiz_service.get_questions(book_id, limit)
    return success({'questions': questions, 'count': len(questions)})


@learn_bp.route('/submit', methods=['POST'])
@login_required
@kiosk_blocked
def submit_attempt(current_user):
    if current_user.credit_score <= 0:
        return error(1001, '信誉分不足，无法使用学习中心')

    data = request.get_json(silent=True)
    if not data:
        return error(400, '请提供有效的JSON数据')

    book_id = data.get('book_id')
    answers = data.get('answers', [])

    if not book_id:
        return error(400, '缺少book_id参数')

    result, err, code = quiz_service.submit_attempt(current_user, book_id, answers)
    if err:
        return error(code or 400, err)
    return success(result, '答题完成')


@learn_bp.route('/titles', methods=['GET'])
@login_required
def get_titles(current_user):
    titles = quiz_service.get_user_titles(current_user.id)
    return success({'titles': titles})


@learn_bp.route('/admin/questions', methods=['POST'])
@admin_required
def create_question(current_user):
    data = request.get_json(silent=True)
    if not data:
        return error(400, '请提供有效的JSON数据')

    question = quiz_service.create_question(
        book_id=data.get('book_id'),
        qtype=data.get('type', 1),
        question_text=data.get('question_text', ''),
        options=data.get('options'),
        correct_answer_text=data.get('correct_answer_text', ''),
        score=data.get('score', 10),
        created_by=current_user.id
    )
    return success(question, '题目添加成功')


@learn_bp.route('/ai/generate', methods=['POST'])
@admin_required
def generate_questions_ai(current_user):
    data = request.get_json(silent=True)
    if not data:
        return error(400, '请提供有效的JSON数据')

    book_id = data.get('book_id')
    count = data.get('count', 5)

    if not book_id:
        return error(400, '缺少book_id参数')

    if count < 1 or count > 10:
        return error(400, '题目数量应在1-10之间')

    questions, err = quiz_service.generate_questions_with_ai(book_id, count)
    if err:
        return error(400, err)

    return success({'questions': questions, 'count': len(questions)}, f'成功生成{len(questions)}道题目')


@learn_bp.route('/admin/questions', methods=['GET'])
@admin_required
def admin_list_questions(current_user):
    page = request.args.get('page', 1, type=int)
    page_size = request.args.get('page_size', 20, type=int)
    book_id = request.args.get('book_id', type=int)

    questions, total = quiz_service.list_questions(page, page_size, book_id)
    return success({
        'items': questions,
        'total': total,
        'page': page,
        'page_size': page_size
    })


@learn_bp.route('/admin/questions/<int:question_id>', methods=['DELETE'])
@admin_required
def delete_question(current_user, question_id):
    success, msg = quiz_service.delete_question(question_id)
    if success:
        return success(None, '题目已删除')
    return error(400, msg)
