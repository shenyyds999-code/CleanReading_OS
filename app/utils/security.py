import bleach


ALLOWED_TAGS = ['b', 'i', 'u', 'em', 'strong', 'p', 'br']


def sanitize_html(text):
    return bleach.clean(text, tags=ALLOWED_TAGS, strip=True)


SENSITIVE_WORDS = set()


def contains_sensitive(text):
    if not text:
        return False
    for word in SENSITIVE_WORDS:
        if word in text:
            return True
    return False
