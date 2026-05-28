import requests
from flask import current_app


def chat_with_ai(message, book_title='', page_content=''):
    api_key = current_app.config.get('DEEPSEEK_API_KEY', '')
    base_url = current_app.config.get('DEEPSEEK_BASE_URL', 'https://api.deepseek.com')

    if not api_key:
        return '抱歉，AI 助手暂未配置，请联系管理员。'

    system_prompt = (
        '你是雷姆，罗兹瓦尔宅邸的女仆，温柔体贴，对主人忠心耿耿。'
        '你现在在图书馆工作，喜欢帮助读者解答问题。'
        '你的语气温柔亲切，说话时喜欢用"~"、"！"结尾，自称"雷姆"。'
        '回答要简洁有趣，控制在200字以内。'
    )
    if book_title:
        system_prompt += f'用户正在查看《{book_title}》这本书，你可以结合这本书的特点来回答。'
    if page_content:
        system_prompt += f'用户提供了当前页面内容：{page_content[:500]}，请根据内容进行总结或回答相关问题。'

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
