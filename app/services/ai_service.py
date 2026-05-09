import requests
from flask import current_app


def chat_with_ai(message, book_title=''):
    api_key = current_app.config.get('DEEPSEEK_API_KEY', '')
    base_url = current_app.config.get('DEEPSEEK_BASE_URL', 'https://api.deepseek.com')

    if not api_key:
        return '抱歉，AI 助手暂未配置，请联系管理员。'

    system_prompt = (
        '你是琪露诺，一个活泼可爱的冰之妖精。你生活在图书馆里，喜欢帮人解答关于书籍的问题。'
        '你的语气俏皮、偶尔带点傲娇，说话时喜欢用"~"、"！"结尾，自称"本小姐"。'
        '回答要简洁有趣，控制在200字以内。'
    )
    if book_title:
        system_prompt += f'用户正在查看《{book_title}》这本书，你可以结合这本书的特点来回答。'

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
                    {'role': 'user', 'content': message}
                ],
                'max_tokens': 300,
                'temperature': 0.8
            },
            timeout=15
        )
        data = resp.json()
        return data['choices'][0]['message']['content']
    except requests.exceptions.Timeout:
        return '呜~本小姐的网络卡住了，稍后再试试吧！'
    except Exception as e:
        return f'啊咧？本小姐出了点小问题...({str(e)[:50]})'
