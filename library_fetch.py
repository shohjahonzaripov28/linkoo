# Linko Kutubxona: erkin (public domain) kitoblar matnini internetdan yuklab olish va tozalash.
# Manbalar: Project Gutenberg, Wikisource (uz/ru/...), yoki oddiy .txt/.html havola.
#
# Manba yozilishi (books.source ustuni):
#   gutenberg:1342                              -> Project Gutenberg kitobi (raqami)
#   wiki:ru.wikisource.org:Шинель (Гоголь)      -> bitta Wikisource sahifasi (versiyalar/boblar avtomatik topiladi)
#   wikiseries:wikisource.org:O'tkan kunlar     -> "Nom/01", "Nom/02", ... boblar ketma-ket
#   url:https://example.com/book.txt            -> oddiy matn yoki HTML sahifa

import json
import re
import time
import urllib.parse
import urllib.request
from html.parser import HTMLParser

UA = "LinkoLibrary/1.0 (Linko app library; https://linkoo.onrender.com)"
MAX_CHARS = 6_000_000


class FetchError(Exception):
    pass


def http_get(url, timeout=30):
    req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept-Encoding": "identity"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.read()


def decode_bytes(data):
    if data.startswith(b"\xef\xbb\xbf"):
        data = data[3:]
    for enc in ("utf-8", "cp1251", "koi8-r", "latin-1"):
        try:
            return data.decode(enc)
        except UnicodeDecodeError:
            continue
    return data.decode("utf-8", "replace")


# ---------------- Matnni tartiblash ----------------
_CJK = re.compile(r"[　-〿㐀-䶿一-鿿豈-﫿＀-￯]")


def is_cjk_text(text):
    sample = text[:4000]
    if not sample:
        return False
    return len(_CJK.findall(sample)) > len(sample) * 0.3


def reflow(text):
    """Gutenberg kabi qattiq qatorlarga bo'lingan matnni paragraflarga yig'adi.
    She'r/dialog (qisqa qatorlar) bo'lsa, qator bo'linishi saqlanadi."""
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    paras = re.split(r"\n\s*\n", text)
    out = []
    for p in paras:
        lines = [ln.rstrip() for ln in p.split("\n") if ln.strip()]
        if not lines:
            continue
        avg = sum(len(ln.strip()) for ln in lines) / len(lines)
        cjk = bool(_CJK.search(p))
        if len(lines) == 1:
            out.append(lines[0].strip())
        elif cjk:
            out.append("".join(ln.strip() for ln in lines))
        elif avg < 48:
            out.append("\n".join(ln.strip() for ln in lines))  # she'r yoki dialog
        else:
            joined = " ".join(ln.strip() for ln in lines)
            out.append(re.sub(r"(\w)- (\w)", r"\1\2", joined))
    return "\n\n".join(out)


def tidy(text):
    text = text.replace("\r\n", "\n").replace("\xa0", " ")
    text = re.sub(r"[ \t]+\n", "\n", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


# ---------------- Gutenberg ----------------
def fetch_gutenberg(book_id):
    book_id = int(book_id)
    urls = (
        f"https://www.gutenberg.org/cache/epub/{book_id}/pg{book_id}.txt",
        f"https://www.gutenberg.org/files/{book_id}/{book_id}-0.txt",
        f"https://www.gutenberg.org/files/{book_id}/{book_id}.txt",
    )
    raw, last = None, None
    for u in urls:
        try:
            raw = http_get(u)
            if raw:
                break
        except Exception as e:  # keyingi manzilni sinaymiz
            last = e
    if not raw:
        raise FetchError(f"gutenberg {book_id}: {last}")
    text = decode_bytes(raw)
    m = re.search(r"\*\*\*\s*START OF (THE|THIS) PROJECT GUTENBERG[^\n]*\n", text, re.I)
    if m:
        text = text[m.end():]
    m = re.search(r"\*\*\*\s*END OF (THE|THIS) PROJECT GUTENBERG", text, re.I)
    if m:
        text = text[:m.start()]
    text = re.sub(r"(?im)^\s*(produced by|this ebook was produced by|e-text prepared by)[^\n]*(\n[^\n]+)*\n", "", text, count=1)
    return tidy(reflow(text))


# ---------------- Wikisource ----------------
SKIP_CLASSES = {
    "ws-noexport", "noprint", "headertemplate", "mw-editsection", "reference", "references", "navbox",
    "ws-header", "metadata", "printfooter", "catlinks", "mw-references-wrap", "licensecontainer", "ambox",
    "toc", "mw-cite-backlink", "wst-header", "header_notes", "pagenum", "ws-pagenum", "mw-heading-anchor",
    "sisitem", "plainlinks", "prp-pages-output-note",
}
SKIP_IDS = {"headertemplate", "toc", "navigation", "footertemplate", "catlinks"}
SKIP_TAGS = {"script", "style", "table", "sup", "noscript", "figure", "img", "math"}
BLOCK_TAGS = {"p", "div", "h1", "h2", "h3", "h4", "h5", "h6", "li", "dd", "dt", "blockquote", "center", "section", "pre", "tr"}
VOID_TAGS = {"br", "img", "hr", "meta", "link", "input", "wbr", "source", "col", "area", "base", "embed", "param", "track"}


class _TextExtractor(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.parts = []
        self.skip_depth = 0
        self.stack = []
        self.links = []

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if tag == "a" and a.get("href", "").startswith("/wiki/") and not self.skip_depth:
            title = urllib.parse.unquote(a["href"][6:].split("#")[0]).replace("_", " ")
            if "class" not in a or "new" not in a.get("class", ""):
                self.links.append(title)
        if tag in VOID_TAGS:
            if tag == "br" and not self.skip_depth:
                self.parts.append("\n")
            return
        classes = set((a.get("class") or "").lower().split())
        skip = (
            tag in SKIP_TAGS
            or bool(classes & SKIP_CLASSES)
            or (a.get("id") or "").lower() in SKIP_IDS
            or (a.get("style") or "").replace(" ", "").find("display:none") >= 0
        )
        self.stack.append((tag, skip))
        if skip:
            self.skip_depth += 1
        elif tag in BLOCK_TAGS and not self.skip_depth:
            self.parts.append("\n\n")

    def handle_endtag(self, tag):
        if tag in VOID_TAGS:
            return
        # yopilmagan teglarni ham to'g'ri chiqarib tashlaymiz
        while self.stack:
            t, skip = self.stack.pop()
            if skip:
                self.skip_depth -= 1
            if t == tag:
                break
        if tag in BLOCK_TAGS and not self.skip_depth:
            self.parts.append("\n\n")

    def handle_data(self, data):
        if not self.skip_depth:
            self.parts.append(data)


def html_to_text(html_src):
    p = _TextExtractor()
    p.feed(html_src)
    p.close()
    raw = "".join(p.parts)
    lines = [re.sub(r"[ \t ]+", " ", ln).strip() for ln in raw.split("\n")]
    text = "\n".join(lines)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return tidy(text), p.links


def wiki_parse(host, title):
    params = urllib.parse.urlencode({
        "action": "parse", "page": title, "prop": "text", "format": "json",
        "formatversion": "2", "redirects": "1", "disableeditsection": "1", "disablelimitreport": "1",
    })
    data = json.loads(decode_bytes(http_get(f"https://{host}/w/api.php?{params}")))
    if "error" in data:
        raise FetchError(f"{host}:{title}: {data['error'].get('code')}")
    html_src = data["parse"]["text"]
    real_title = data["parse"].get("title", title)
    text, links = html_to_text(html_src)
    return real_title, text, links


def fetch_wiki(host, title, depth=0):
    real_title, text, links = wiki_parse(host, title)
    prefix = real_title + "/"
    subs = []
    for ln in links:
        if ln.startswith(prefix) and ln not in subs:
            subs.append(ln)
    if len(text) >= 4000 or not subs or depth >= 1:
        return text
    versions = [s for s in subs if re.search(r"/(ДО|ВТ|Версия|Редакция|Вариант)", s)]
    if versions or len(subs) <= 2:
        modern = [s for s in subs if "/ДО" not in s] or subs
        return fetch_wiki(host, modern[0], depth + 1)
    # boblar: hammasini ketma-ket yig'amiz
    chunks = []
    for s in subs[:150]:
        try:
            chunks.append(fetch_wiki(host, s, depth + 1))
        except Exception:
            continue
        time.sleep(0.3)
    return "\n\n".join(c for c in chunks if c)


def fetch_wiki_series(host, base, start=1, limit=200):
    chunks, misses, i = [], 0, start
    while i < start + limit:
        title = f"{base}/{i:02d}"
        try:
            _, text, _ = wiki_parse(host, title)
            chunks.append(text)
            misses = 0
        except FetchError:
            misses += 1
            if misses >= 2:
                break
        i += 1
        time.sleep(0.3)
    if not chunks:
        raise FetchError(f"{host}:{base}: boblar topilmadi")
    return "\n\n* * *\n\n".join(chunks)


def fetch_url(url):
    raw = http_get(url)
    text = decode_bytes(raw)
    if re.search(r"<html|<body|<p[ >]", text[:5000], re.I):
        text, _ = html_to_text(text)
        return text
    return tidy(reflow(text))


def fetch_source(spec):
    """Manba yozuvi bo'yicha kitob matnini qaytaradi (xato bo'lsa FetchError)."""
    spec = (spec or "").strip()
    kind, _, rest = spec.partition(":")
    try:
        if kind == "gutenberg":
            text = fetch_gutenberg(rest)
        elif kind == "wiki":
            host, _, title = rest.partition(":")
            text = fetch_wiki(host, title)
        elif kind == "wikiseries":
            host, _, title = rest.partition(":")
            text = fetch_wiki_series(host, title)
        elif kind in ("url", "http", "https"):
            text = fetch_url(rest if kind == "url" else spec)
        else:
            raise FetchError("noma'lum manba: " + spec[:60])
    except FetchError:
        raise
    except Exception as e:
        raise FetchError(f"{type(e).__name__}: {e}"[:300])
    if len(text) < 300:
        raise FetchError("matn juda qisqa (" + str(len(text)) + " belgi)")
    return text[:MAX_CHARS]


# ---------------- Sahifalarga bo'lish ----------------
def split_pages(text, cjk=None):
    """Matnni o'qish uchun sahifalarga bo'ladi (paragraf chegarasida). Qaytaradi: [(boshi, oxiri), ...]."""
    if cjk is None:
        cjk = is_cjk_text(text)
    size = 2600 if cjk else 5200
    pages, start, n = [], 0, len(text)
    while start < n:
        end = min(n, start + size)
        if end < n:
            cut = text.rfind("\n\n", start + size // 2, end + size // 3)
            if cut == -1:
                cut = text.rfind("\n", start + size // 2, end + size // 4)
            if cut == -1:
                cut = text.rfind(" ", start + size // 2, end)
            end = cut if cut > start else end
        pages.append((start, end))
        start = end
        while start < n and text[start] in "\n ":
            start += 1
    return pages or [(0, 0)]
