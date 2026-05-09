from flask import jsonify


def success(data=None, message='success'):
    return jsonify({'code': 200, 'message': message, 'data': data or {}})


def error(code, message, http_status=None):
    body = {'code': code, 'message': message, 'data': {}}
    if http_status:
        return jsonify(body), http_status
    status_map = {400: 400, 401: 401, 403: 403, 404: 404, 500: 500}
    return jsonify(body), status_map.get(code, 400)


def paginated(items, total, page, per_page):
    return jsonify({
        'code': 200,
        'message': 'success',
        'data': {
            'items': items,
            'total': total,
            'page': page,
            'per_page': per_page
        }
    })
