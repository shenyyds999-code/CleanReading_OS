from app.models import Book
from app import db
from sqlalchemy import or_
import requests
import re
import time
import json
from bs4 import BeautifulSoup


import os
import base64
import io
from PIL import Image


def openlibrary_cover_url(isbn, size='M'):
    if not isbn:
        return ''
    return f'https://covers.openlibrary.org/b/isbn/{isbn}-{size}.jpg'


def _douban_isbn_search(isbn):
    """通过豆瓣搜索页获取图书信息"""
    session = requests.Session()
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
    }

    search_url = f'https://book.douban.com/subject_search?search_text={isbn}&cat=1001'
    resp = session.get(search_url, headers=headers, timeout=10)
    resp.raise_for_status()

    match = re.search(r'window\.__DATA__\s*=\s*({.*?});', resp.text, re.DOTALL)
    if not match:
        return None

    data = json.loads(match.group(1))
    items = data.get('items', [])
    if not items:
        return None

    first_item = items[0]
    book_url = first_item.get('url', '')
    if not book_url:
        return None

    time.sleep(1)

    book_resp = session.get(book_url, headers=headers, timeout=10)
    book_resp.raise_for_status()
    book_soup = BeautifulSoup(book_resp.text, 'lxml')

    info_div = book_soup.find('div', id='info')
    if not info_div:
        return None

    title_elem = book_soup.select_one('#wrapper > h1 > span')
    title = title_elem.get_text(strip=True) if title_elem else ''

    def _get_info(label):
        pl_span = info_div.find('span', class_='pl', string=lambda t: t and label in t)
        if not pl_span:
            return ''
        next_elem = pl_span.next_sibling
        while next_elem:
            if hasattr(next_elem, 'name') and next_elem.name == 'br':
                next_elem = next_elem.next_sibling
                continue
            if hasattr(next_elem, 'name') and next_elem.name == 'a':
                return next_elem.get_text(strip=True)
            if hasattr(next_elem, 'get_text'):
                text = next_elem.get_text(strip=True)
                if text:
                    return text
            next_elem = next_elem.next_sibling
        return ''

    def _get_author():
        author_spans = info_div.find_all('span', class_='pl', string=lambda t: t and '作者' in t)
        if not author_spans:
            return ''
        authors = []
        for pl_span in author_spans:
            parent = pl_span.parent
            if parent and parent.name == 'span':
                links = parent.find_all('a')
                for link in links:
                    name = link.get_text(strip=True)
                    if name and name not in authors:
                        authors.append(name)
        return ' / '.join(authors)

    author = _get_author()
    publisher = _get_info('出版社')
    pub_date = _get_info('出版年')
    pages = _get_info('页数')
    price = _get_info('定价')
    isbn_val = _get_info('ISBN')

    cover_url = first_item.get('cover_url', '')
    if cover_url:
        cover_url = cover_url.replace('/view/subject/s/', '/view/subject/l/').replace('/view/subject/m/', '/view/subject/l/')
        cover_url = re.sub(r'https?://img\d+\.doubanio\.com', 'https://img1.doubanio.com', cover_url)
    if not cover_url:
        img_elem = book_soup.select_one('#mainpic > a > img')
        if img_elem and img_elem.get('src'):
            cover_url = img_elem['src'].replace('/view/subject/s/', '/view/subject/l/').replace('/view/subject/m/', '/view/subject/l/')
            cover_url = re.sub(r'https?://img\d+\.doubanio\.com', 'https://img1.doubanio.com', cover_url)

    description = ''
    intro_div = book_soup.find('div', class_='intro')
    if intro_div:
        description = intro_div.get_text(strip=True)

    score_elem = book_soup.select_one('#interest_sectl > div > div.rating_self > strong')
    score = score_elem.get_text(strip=True) if score_elem else ''

    return {
        'isbn': isbn_val or isbn,
        'title': title,
        'author': author,
        'publisher': publisher,
        'cover_url': cover_url,
        'description': description,
        'published': pub_date,
        'pages': pages,
        'price': price,
        'douban_score': score,
    }


def isbn_lookup(isbn):
    isbn = (isbn or '').strip()
    if not isbn:
        return None, 'ISBN不能为空', None

    try:
        result = _douban_isbn_search(isbn)
        if result and result.get('title'):
            if not result.get('cover_url'):
                result['cover_url'] = openlibrary_cover_url(isbn, 'M')
            return result, None, None
    except requests.Timeout:
        pass
    except Exception:
        pass

    try:
        resp = requests.get(
            f'https://openlibrary.org/isbn/{isbn}.json',
            timeout=(3, 5),
            headers={'User-Agent': 'ClearReading/1.0'}
        )
        if resp.status_code == 404:
            return None, '未找到该ISBN对应的图书信息', None
        resp.raise_for_status()
        data = resp.json()
    except requests.Timeout:
        return None, '查询超时，请重试', None
    except requests.RequestException:
        return None, '查询OpenLibrary失败，请检查网络', None

    result = {
        'isbn': isbn,
        'title': data.get('title', ''),
        'author': '',
        'publisher': '',
        'cover_url': openlibrary_cover_url(isbn, 'M'),
    }

    authors = data.get('authors', [])
    if authors:
        result['author'] = authors[0].get('name', '')

    publishers = data.get('publishers', [])
    if publishers:
        result['publisher'] = publishers[0]

    return result, None, None


def search_cover_by_isbn(isbn):
    """搜索封面图，返回图片URL列表"""
    isbn = (isbn or '').strip()
    if not isbn:
        return [], 'ISBN不能为空'

    cover_urls = []

    try:
        result = _douban_isbn_search(isbn)
        if result and result.get('cover_url'):
            cover_urls.append(result['cover_url'])
    except Exception:
        pass

    ol_url = openlibrary_cover_url(isbn, 'L')
    if ol_url:
        cover_urls.append(ol_url)

    if not cover_urls:
        return [], '未找到封面'

    return cover_urls, None


def download_cover(url):
    """下载封面图，返回base64编码的图片"""
    try:
        resp = requests.get(url, timeout=10, headers={
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        })
        resp.raise_for_status()

        img = Image.open(io.BytesIO(resp.content))
        img = img.convert('RGB')
        img.thumbnail((400, 600))

        buf = io.BytesIO()
        img.save(buf, format='JPEG', quality=85)
        img_b64 = base64.b64encode(buf.getvalue()).decode('utf-8')

        return img_b64, None
    except Exception as e:
        return None, str(e)


def search_books(query='', search_type='fuzzy', page=1, per_page=20):
    q = Book.query

    if query:
        if search_type == 'exact':
            q = q.filter(or_(
                Book.title == query,
                Book.isbn == query,
                Book.author == query
            ))
        else:
            pattern = f'%{query}%'
            q = q.filter(or_(
                Book.title.like(pattern),
                Book.author.like(pattern),
                Book.isbn.like(pattern),
                Book.category.like(pattern),
                Book.publisher.like(pattern)
            ))

    total = q.count()
    items = q.order_by(Book.created_at.desc()).paginate(page=page, per_page=per_page, error_out=False)

    return {
        'items': [_book_dict(b) for b in items],
        'total': total,
        'page': page,
        'per_page': per_page
    }


def get_book(book_id):
    book = db.session.get(Book, book_id)
    if not book:
        return None
    return _book_dict(book)


def get_popular_books(limit=8, user_id=None):
    from app.models import BorrowRecord
    from sqlalchemy import func
    popular = (
        db.session.query(
            Book.id,
            Book.title,
            Book.author,
            Book.isbn,
            func.count(BorrowRecord.id).label('borrow_count')
        )
        .outerjoin(BorrowRecord, BorrowRecord.book_id == Book.id)
        .group_by(Book.id)
        .order_by(func.count(BorrowRecord.id).desc())
        .limit(limit)
        .all()
    )
    result = []
    for p in popular:
        book = db.session.get(Book, p.id)
        d = _book_dict(book)
        d['borrow_count'] = p.borrow_count
        d['user_borrow_count'] = 0
        if user_id:
            d['user_borrow_count'] = BorrowRecord.query.filter_by(
                user_id=user_id, book_id=p.id, status='借阅中'
            ).count()
        result.append(d)
    result.sort(key=lambda x: x['borrow_count'], reverse=True)
    return result


def _book_dict(book):
    ol_cover = openlibrary_cover_url(book.isbn, 'M')
    return {
        'id': book.id,
        'title': book.title,
        'author': book.author,
        'isbn': book.isbn,
        'category': book.category,
        'publisher': book.publisher,
        'total_copies': book.total_copies,
        'available_copies': book.available_copies,
        'location': book.location,
        'cover_image_url': book.cover_image_url or ol_cover,
        'openlibrary_cover': ol_cover,
        'description': book.description,
        'status': book.status,
        'can_borrow': book.available_copies > 0 and book.status == '可借'
    }
