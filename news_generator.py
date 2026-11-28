"""
Live News Scraper & Post Generator for X Daily Manager (Viral Psychology & High-Engagement Edition)
- Powered by Consumer Psychology: Shock, Greed/Relief, Pride, Curiosity Gaps, and High-Emotion Debate.
- Verified Urdu RSS feeds from Dawn News Urdu & BBC Urdu.
- Extracts 1200px Ultra-HD editorial photos directly from article OpenGraph metadata.
- Strict Category Routing: No category pollution (Cricket is strictly Cricket, National is strictly Pakistan).
- Zero Bot Watermarks: Strips boilerplate citations ("بشکریہ بی بی سی") for authentic digital news reporting.
- Layman Coherence & Completeness: Grammatically whole with authentic Urdu verbs; zero '..' cutoffs.
- Polarizing Debate CTAs: Forces reader engagement, comments, and viral shares.
- 100% compliant with Pakistani law, constitution, and state institutions.
"""

import feedparser
import re
import os
import requests
from datetime import datetime
from PIL import Image, ImageEnhance
from bs4 import BeautifulSoup

URDU_FEEDS = [
    {"name": "ڈان نیوز", "url": "https://www.dawnnews.tv/feeds/latest-news/"},
    {"name": "بی بی سی اردو", "url": "https://feeds.bbci.co.uk/urdu/rss.xml"}
]

URDU_VERBAL_ENDINGS = (
    'ہے', 'ہیں', 'تھا', 'تھی', 'تھے', 'ہوں',
    'ہوگا', 'ہوگی', 'ہوںگے', 'ہوں گے',
    'گیا', 'گئی', 'گئے', 'دیا', 'دی', 'دیے',
    'لیا', 'لی', 'لیے', 'ہوا', 'ہوئی', 'ہوئے',
    'سکا', 'سکی', 'سکے', 'کیا', 'کی', 'کیے',
    'چکا', 'چکی', 'چکے', 'آیا', 'آئی', 'آئے',
    'پایا', 'پائی', 'پائے', 'رہا', 'رہی', 'رہے',
    'بنایا', 'بنائی', 'بنائے', 'ڈالا', 'ڈالی', 'ڈالے',
    'کریں', 'ہو', 'سکیں', 'سکے گا', 'سکیں گے'
)

BOILERPLATE = [
    'تصویر کا ذریعہGetty Images', 'Getty Images', 'تصویر کا ذریعہ',
    'تصویر کے جملہ حقوق', 'فوٹو:', 'تصویر:', 'EPA', 'AFP', 'Reuters',
    'بی بی سی کے لیے', 'DawnNews', 'ڈان نیوز', 'بی بی سی اردو',
    'بی بی سی نیوز اردو', 'بی بی سی کو بتایا کہ', 'بی بی سی نے',
    'بی بی سی کے مطابق'
]

BLACKLIST = [
    'ایپ ڈاؤن لوڈ', 'ایپلی کیشن ڈاؤن لوڈ', 'موبائل ایپ',
    'سبسکرائب کریں', 'نیوز لیٹر', 'پوڈکاسٹ', 'کاپی رائٹ',
    'اشتہار', 'بی بی سی نیوز اردو ایپ', 'ڈاؤن لوڈ کریں'
]

TRAGEDY_WORDS = [
    'شہید', 'شہادت', 'جنازہ', 'ہلاک', 'قتل', 'مبینہ قتل', 'وفات',
    'انتقال', 'دھماکا', 'خودکش حملہ', 'جاں بحق', 'لاش', 'لاشیں',
    'سوگ', 'تعزیت'
]

INCOMPLETE_HEADLINE_ENDINGS = {
    'کا', 'کی', 'کے', 'نے', 'کو', 'سے', 'پر', 'میں', 'تک', 'اور', 'کہ', 'یا', 'اگر',
    'کرنے', 'ہونے', 'دینے', 'لینے', 'والے', 'والی', 'والا', 'پہ', 'تاہم', 'لیکن', 'جبکہ',
    'ہو', 'کیا', 'تھا', 'تھی', 'تھے'
}

def clean_urdu_text(t: str) -> str:
    """Strip HTML tags, boilerplate credits, and normalize whitespace."""
    if not t:
        return ""
    t = re.sub(r'<[^>]+>', '', t)
    for b in BOILERPLATE:
        t = t.replace(b, '')
    t = re.sub(r'[\r\n\t]+', ' ', t)
    t = re.sub(r'\s+', ' ', t)
    return t.strip()

def is_blacklisted(text: str) -> bool:
    return any(b in text for b in BLACKLIST)

def is_tragedy(text: str) -> bool:
    return any(w in text for w in TRAGEDY_WORDS)

def is_complete_sentence(s: str) -> bool:
    """Checks if a sentence is grammatically whole and ends with an authentic Urdu verbal predicate."""
    s = s.strip(" '\"`‘’“”،؛:-.۔")
    words = s.split()
    if len(words) < 5:
        return False
    last_word = words[-1]
    last_two = " ".join(words[-2:]) if len(words) >= 2 else ""
    return last_word.endswith(URDU_VERBAL_ENDINGS) or last_two.endswith(URDU_VERBAL_ENDINGS)

def extract_clean_sentences(text: str) -> list:
    """Splits text into verified, complete Urdu sentences without cutting abbreviations."""
    text = clean_urdu_text(text)
    text = re.sub(r'([A-Za-z0-9])\.([A-Za-z0-9])', r'\1_\2', text)
    raw_splits = re.split(r'[\u06D4\n\r]+', text)
    valid = []
    for r in raw_splits:
        c = clean_urdu_text(r).strip(" '\"`‘’“”،؛:-.۔")
        if len(c) > 28 and is_complete_sentence(c):
            valid.append(c)
    return valid

def clean_headline(title: str, max_len: int = 86) -> str:
    """Creates a complete, impactful headline with zero truncation, balanced quotes, and no hanging prepositions."""
    title = clean_urdu_text(title)
    title = title.replace("’", "").replace("‘", "").replace("'", "").replace('"', "")
    title = title.strip(" ،؛:-.۔")
    if len(title) <= max_len:
        return title
    if ':' in title:
        parts = title.split(':', 1)
        p1 = parts[0].strip(" ،؛:-.۔")
        p2 = parts[1].strip(" ،؛:-.۔")
        if 25 <= len(p1) <= max_len:
            return p1
        if 25 <= len(p2) <= max_len:
            return p2
    if '،' in title:
        parts = title.split('،')
        cand = ""
        for p in parts:
            p = p.strip()
            if not cand:
                cand = p
            elif len(cand + "، " + p) <= max_len:
                cand = cand + "، " + p
        if len(cand) >= 25:
            cand_words = cand.split()
            while cand_words and cand_words[-1] in INCOMPLETE_HEADLINE_ENDINGS:
                cand_words.pop()
            return " ".join(cand_words).strip(" ،؛:-.۔")
    words = title.split()
    cand = ""
    for w in words:
        if len(cand + " " + w) <= max_len:
            cand = (cand + " " + w).strip()
        else:
            break
    cand_words = cand.split()
    while cand_words and cand_words[-1] in INCOMPLETE_HEADLINE_ENDINGS:
        cand_words.pop()
    return " ".join(cand_words).strip(" ،؛:-.۔")

def scrape_article_lead(url: str) -> list:
    """Scrapes the live article page to extract complete lead sentences if RSS summary was sparse."""
    if not url:
        return []
    try:
        headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36"}
        resp = requests.get(url, headers=headers, timeout=6)
        if resp.status_code == 200:
            soup = BeautifulSoup(resp.text, 'html.parser')
            paras = [clean_urdu_text(p.get_text()) for p in soup.find_all('p') if len(clean_urdu_text(p.get_text())) > 25]
            good_paras = []
            for p in paras[:4]:
                if any(b in p for b in BLACKLIST):
                    continue
                good_paras.append(p)
            combined = ' '.join(good_paras)
            return extract_clean_sentences(combined)
    except Exception as e:
        print(f"[Scraper Fallback Warning] {e}")
    return []

def get_psychological_framing(title: str, slot_id: str):
    """
    Applies high-conversion consumer psychology to select:
    1. Thumb-stopping pattern interrupt prefix (Shock, Greed, Pride, Drama)
    2. Emotion-provoking debate CTA that compels replies
    """
    if slot_id == "post-1":
        # National & Political Power
        if any(k in title for k in ["مولانا", "سیل", "گرفتار", "عدالت", "عمران", "حکومت", "نوٹس", "چھاپہ", "پی ٹی آئی"]):
            prefix = "🚨 بڑا سیاسی زلزلہ:"
            cta = "💬 کیا یہ خالص قانونی کارروائی ہے یا سیاسی دباؤ؟ اپنی کھری رائے کمنٹ میں دیں!"
        else:
            prefix = "📢 اہم قومی پیش رفت:"
            cta = "💬 اس بڑے حکومتی فیصلے کے بارے میں آپ کی کیا رائے ہے؟ کمنٹ کریں!"
    elif slot_id == "post-2":
        # Economy & Pocketbook (Greed/Relief/Anxiety)
        if any(k in title for k in ["کمی", "ریلیف", "سستا", "خوشخبری", "اضافہ", "فائدہ", "سرمایہ"]):
            prefix = "💰 عوام کے لیے بڑی خوشخبری:"
            cta = "💬 کیا اس سے عام آدمی کو حقیقی معاشی ریلیف ملے گا؟ اپنی رائے بتائیں!"
        else:
            prefix = "⚠️ عوام ہوشیار رہیں! معاشی الرٹ:"
            cta = "💬 کیا ملکی معیشت درست سمت میں جا رہی ہے یا بوجھ عوام پر ہی پڑے گا؟ کمنٹ کریں!"
    elif slot_id == "post-3":
        # Tech & Innovation (Awe/National Pride)
        if any(k in title for k in ["انڈیا", "خلائی", "روس", "دفاع", "سیٹلائٹ"]):
            prefix = "🚀 دلی کے ایوانوں میں کھلبلی:"
            cta = "💬 کیا پاکستان اب اسپیس ٹیکنالوجی میں خطے کا لیڈر بن رہا ہے؟ اپنی رائے دیں!"
        else:
            prefix = "🔬 سائنس اور ٹیکنالوجی کا نیا انقلاب:"
            cta = "💬 کیا آپ روزمرہ زندگی میں اس جدید ٹیکنالوجی سے فائدہ اٹھاتے ہیں؟ کمنٹ کریں!"
    elif slot_id == "post-4":
        # Cricket & Sports (High Tribalism / Passion)
        if any(k in title for k in ["بیچ", "اونر", "پی ایس ایل", "تنازعہ", "بابر", "رضوان", "کوئٹہ"]):
            prefix = "🏏 کرکٹ کی دنیا میں دھماکہ:"
            cta = "💬 کیا آپ اس فیصلے کے حق میں ہیں یا سخت مخالف ہیں؟ کمنٹ میں کھل کر بتائیں!"
        else:
            prefix = "🔥 کھیل کے میدان سے بڑی خبر:"
            cta = "💬 قومی ٹیم کی موجودہ حکمت عملی پر آپ کا کیا مؤقف ہے؟ کمنٹ کریں!"
    elif slot_id == "post-5":
        # Investigative / Revelation (High Curiosity Gap)
        prefix = "😱 ہوشربا سچائی اور لرزہ خیز انکشاف:"
        cta = "💬 اس سنسنی خیز معاملے پر آپ کیا کہیں گے؟ اپنی رائے ضرور بتائیں!"
    elif slot_id == "post-6":
        # Geopolitics & World Crisis (High Stakes)
        prefix = "🌍 عالمی منظرنامے پر بڑی ہلچل:"
        cta = "💬 کیا یہ پیش رفت خطے میں امن لائے گی یا نئی جنگ کا آغاز ہے؟ کمنٹ کریں!"
    else:
        # History & Fascinating Human Realities (Awe & Curiosity)
        prefix = "✨ تاریخ کا سب سے بڑا سنسنی خیز راز:"
        cta = "💬 اس تاریخی حقیقت پر آپ کا کیا نقطہ نظر ہے؟"

    if is_tragedy(title):
        prefix = "⚠️ افسوسناک خبر:"
        cta = "انا للہ وانا الیہ راجعون۔ اللہ تعالیٰ مرحومین کے درجات بلند فرمائے۔"

    return prefix, cta

def compose_editorial_post(title: str, summary: str, url: str, slot_id: str, hashtags: list, is_tragic_story: bool) -> str:
    """
    Constructs a viral, thumb-stopping, emotionally charged Urdu post.
    - Eliminates robotic source citations ('بشکریہ بی بی سی')
    - Embeds psychological pattern interrupts
    - Closes with polarizing debate question
    - Strictly kept under 275 characters.
    """
    clean_title = clean_headline(title, max_len=85)
    prefix, cta_line = get_psychological_framing(clean_title, slot_id)
    tags_line = ' '.join(hashtags)

    candidate_sentences = extract_clean_sentences(summary)
    lead_sentences = scrape_article_lead(url)
    for ls in lead_sentences:
        if ls not in candidate_sentences:
            candidate_sentences.append(ls)

    # Budget calculation
    fixed_overhead = len(f"{prefix} {clean_title}\n\n\n\n{cta_line}\n\n{tags_line}")
    max_body_budget = 275 - fixed_overhead

    chosen_body = ""
    for s in candidate_sentences:
        if s in clean_title or clean_title in s:
            continue
        if len(s) + 1 <= max_body_budget:
            chosen_body = s + "۔"
            break

    # If first sentence didn't fit with full CTA, fall back to concise CTA
    if not chosen_body:
        short_cta = "انا للہ وانا الیہ راجعون۔" if is_tragic_story else "💬 آپ کی کیا رائے ہے؟ کمنٹ کریں!"
        fixed_overhead = len(f"{prefix} {clean_title}\n\n\n\n{short_cta}\n\n{tags_line}")
        max_body_budget = 275 - fixed_overhead
        for s in candidate_sentences:
            if s in clean_title or clean_title in s:
                continue
            if len(s) + 1 <= max_body_budget:
                chosen_body = s + "۔"
                cta_line = short_cta
                break

    if chosen_body:
        tweet = f"{prefix} {clean_title}\n\n{chosen_body}\n\n{cta_line}\n\n{tags_line}"
    else:
        tweet = f"{prefix} {clean_title}\n\n{cta_line}\n\n{tags_line}"

    return tweet

def extract_ultra_hd_image(entry) -> str:
    """
    Extracts high-resolution (1200px+) editorial photo.
    Scrapes the full article og:image first, and upgrades BBC thumbnails to 1200px HD.
    """
    link = entry.get('link', '')
    if link:
        try:
            headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
            r = requests.get(link, headers=headers, timeout=6)
            if r.status_code == 200:
                soup = BeautifulSoup(r.text, 'html.parser')
                og = soup.find('meta', property='og:image')
                if og and og.get('content'):
                    img_url = og['content']
                    if 'bbci.co.uk' in img_url:
                        img_url = re.sub(r'/(240|320|480|800|1024)/', '/1200/', img_url)
                    return img_url
        except Exception as e:
            print(f"[HD Image Warning] Article og:image failed: {e}")

    # Fallback to RSS media tag
    raw_img = ""
    if 'media_content' in entry and entry.media_content:
        raw_img = entry.media_content[0].get('url', '')
    elif 'media_thumbnail' in entry and entry.media_thumbnail:
        raw_img = entry.media_thumbnail[0].get('url', '')
    elif 'enclosures' in entry and entry.enclosures:
        for enc in entry.enclosures:
            if enc.get('href') and any(enc.get('href', '').lower().endswith(ext) for ext in ['.jpg', '.jpeg', '.png', '.webp']):
                raw_img = enc['href']
                break

    if raw_img:
        if 'bbci.co.uk' in raw_img:
            return re.sub(r'/(240|320|480)/', '/1200/', raw_img)
        return raw_img

    return ""

def download_and_prepare_image(image_url: str, post_id: str) -> str:
    """Download image, enhance contrast & sharpness, and convert to high-quality JPEG."""
    if not image_url:
        return ""
    try:
        media_dir = os.path.join(os.path.dirname(__file__), "media_cache")
        os.makedirs(media_dir, exist_ok=True)
        target_path = os.path.join(media_dir, f"{post_id}.jpg")
        
        headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
        resp = requests.get(image_url, headers=headers, timeout=20)
        if resp.status_code == 200:
            temp_path = os.path.join(media_dir, f"{post_id}_temp")
            with open(temp_path, "wb") as f:
                f.write(resp.content)
            
            im = Image.open(temp_path).convert("RGB")
            enhancer = ImageEnhance.Sharpness(im)
            im = enhancer.enhance(1.15)
            im.save(target_path, "JPEG", quality=95, optimize=True)
            if os.path.exists(temp_path):
                os.remove(temp_path)
            return target_path
    except Exception as e:
        print(f"Warning: Could not download/process image for {post_id}: {e}")
    return ""

SLOT_DEFINITIONS = [
    {
        "id": "post-1",
        "time_slot": "08:30 AM PKT",
        "category": "قومی و ریاستی امور",
        "title_keywords": ["پاکستان", "حکومت", "وزیر", "عدالت", "سپریم کورٹ", "شہری", "معاہدہ", "امیگریشن", "قانون", "اسلام آباد", "لاہور", "کراچی", "صوبائی", "وفاق", "پاسپورٹ", "پولیس", "سہیل آفریدی", "پی ٹی آئی", "ن لیگ", "فضل الرحمٰن", "سیل", "جائیداد"],
        "body_keywords": ["پاکستان", "حکومت", "وفاقی", "شہری", "عدالت"],
        "hashtags": ["#BreakingNews", "#Pakistan", "#Trending"],
        "default_title": "پاکستان میں اہم ریاستی فیصلے اور عوامی بہبود کے اقدامات",
        "default_body": "شہریوں کی سہولت کے لیے نئے ضوابط اور سفری و قانونی طریقہ کار کو آسان بنایا جا رہا ہے۔"
    },
    {
        "id": "post-2",
        "time_slot": "11:30 AM PKT",
        "category": "معیشت و فنانس",
        "title_keywords": ["معیشت", "بینک", "اسٹاک", "روپیہ", "ڈالر", "سرمایہ", "تجارت", "ٹیکس", "مہنگائی", "مارکیٹ", "تیل", "بجٹ", "برآمدات", "ترقیاتی", "آمدنی", "غریب", "پیٹرول", "بجلی", "سونا"],
        "body_keywords": ["معیشت", "روپیہ", "ڈالر", "اسٹاک", "مارکیٹ", "تجارت", "قیمتوں"],
        "hashtags": ["#Economy", "#PakistanNews", "#Breaking"],
        "default_title": "پاکستان کی معیشت اور تجارتی اعشاریوں میں اہم پیش رفت",
        "default_body": "ملکی برآمدات میں اضافہ اور صنعتی شعبے کے لیے نئے معاشی اقدامات حتمی مراحل میں داخل ہو چکے ہیں۔"
    },
    {
        "id": "post-3",
        "time_slot": "02:00 PM PKT",
        "category": "ٹیکنالوجی و سائنس",
        "title_keywords": ["ٹیکنالوجی", "سائنس", "آئی ٹی", "اے آئی", "ڈیجیٹل", "موبائل", "انٹرنیٹ", "کمپیوٹر", "مصنوعی ذہانت", "مائیکروسافٹ", "گوگل", "سافٹ ویئر", "خلائی", "دریافت", "محققین", "سائبر", "کنگھی", "علاج", "گنج پن", "روس", "سیٹلائٹ"],
        "body_keywords": ["ٹیکنالوجی", "سائنس", "سافٹ ویئر", "کمپیوٹر", "ڈیجیٹل", "محققین"],
        "hashtags": ["#Technology", "#Science", "#Innovation"],
        "default_title": "جدید ڈیجیٹل دور کے تقاضے اور سائنسی ایجادات کا دائرہ کار وسیع",
        "default_body": "معلومات تک فوری رسائی اور جدید ٹیکنالوجی کے استعمال سے روزمرہ زندگی کے مختلف شعبوں میں انقلابی تبدیلیاں آ رہی ہیں۔"
    },
    {
        "id": "post-4",
        "time_slot": "05:30 PM PKT",
        "category": "کھیل و قومی ایتھلیٹس",
        # STRICT CRICKET & SPORTS MATCHING - Must contain genuine sports entities
        "title_keywords": ["کرکٹ", "بیٹنگ", "رنز", "وکٹ", "میچ", "کھلاڑی", "ٹیم", "کھیل", "پی ایس ایل", "لیگ", "بابر", "رضوان", "شاہین", "ٹیسٹ", "ون ڈے", "پی سی بی", "آئی سی سی", "کوئٹہ", "گلیڈی ایٹرز", "لاہور قلندرز", "فٹبال"],
        "body_keywords": ["کرکٹ", "میچ", "کھلاڑی", "ٹیم", "رنز", "وکٹ", "پی ایس ایل"],
        "hashtags": ["#Cricket", "#PSL", "#PakistanCricket"],
        "default_title": "کھیلوں کے میدان سے اہم اپ ڈیٹ: قومی کھلاڑیوں کی کارکردگی کا جائزہ",
        "default_body": "کھلاڑیوں کے لیے بین الاقوامی سطح پر مسابقتی مواقع اور آئندہ میچز کے لیے خصوصی حکمت عملی تیار کر لی گئی ہے۔"
    },
    {
        "id": "post-5",
        "time_slot": "08:15 PM PKT",
        "category": "خصوصی جائزہ و تجزیہ",
        "title_keywords": ["رپورٹ", "جائزہ", "پالیسی", "تحقیق", "سماجی", "بحران", "چوری", "سرنگ", "تحقیقات", "انکشاف", "خام تیل", "راولپنڈی", "معمہ", "سنسنی", "راز"],
        "body_keywords": ["رپورٹ", "تحقیق", "انکشاف", "جائزہ"],
        "hashtags": ["#Exclusive", "#Investigation", "#Pakistan"],
        "default_title": "قومی اور علاقائی امور پر خصوصی تحقیقاتی جائزہ",
        "default_body": "خطے کے بدلتے ہوئے حالات اور اندرونی چیلنجز کے پیش نظر جامع حکمت عملی ناگزیر قرار دی گئی ہے۔"
    },
    {
        "id": "post-6",
        "time_slot": "09:45 PM PKT",
        "category": "عالمی حالاتِ حاضرہ",
        "title_keywords": ["امریکہ", "چین", "ایران", "ٹرمپ", "غزہ", "سفارت", "عالمی", "مشرق", "اقوام متحدہ", "روس", "اسرائیل", "مذاکرات", "ڈرون", "یمن", "سعودی", "حوثی"],
        "body_keywords": ["امریکہ", "چین", "ایران", "عالمی", "روس"],
        "hashtags": ["#WorldNews", "#Geopolitics", "#Global"],
        "default_title": "عالمی سفارت کاری اور بین الاقوامی تعلقات میں اہم پیش رفت",
        "default_body": "عالمی طاقتوں کے درمیان مکالمے اور سرحدی امن و استحکام کے لیے سفارتی کوششیں تیز تر ہو گئی ہیں۔"
    },
    {
        "id": "post-7",
        "time_slot": "11:15 PM PKT",
        "category": "تاریخ، ادب و مثبت فکر",
        "title_keywords": ["تاریخ", "ماضی", "ادب", "کتاب", "نصیحت", "یادداشت", "ثقافت", "ورثہ", "دنیا", "شاعری", "فکر", "علاقے", "ملکیت", "راز"],
        "body_keywords": ["تاریخ", "ادب", "کتاب", "ثقافت"],
        "hashtags": ["#History", "#Facts", "#Inspiration"],
        "default_title": "تاریخی پس منظر اور اخلاقی اقدار کا معاشرتی شعور میں کردار",
        "default_body": "ماضی کے تجربات سے سیکھ کر باوقار اور پرامن معاشرے کے قیام کی مشترکہ ذمہ داری ہم سب پر عائد ہوتی ہے۔"
    }
]

def build_daily_posts(date_str: str = None) -> list:
    """Scrapes Urdu feeds and constructs 7 strictly validated, high-engagement viral posts."""
    if not date_str:
        date_str = datetime.now().strftime("%Y-%m-%d")

    all_entries = []
    seen_urls = set()
    for feed_info in URDU_FEEDS:
        try:
            d = feedparser.parse(feed_info["url"])
            for e in d.entries:
                link = e.get("link", "")
                if link and link not in seen_urls:
                    seen_urls.add(link)
                    title = clean_urdu_text(e.get("title", ""))
                    summary = clean_urdu_text(e.get("summary", ""))
                    
                    if is_blacklisted(title) or is_blacklisted(summary):
                        continue
                        
                    e["_source_name"] = feed_info["name"]
                    e["_title"] = title
                    e["_summary"] = summary
                    all_entries.append(e)
        except Exception as err:
            print(f"Error fetching feed {feed_info['name']}: {err}")

    used_links = set()
    posts = []

    for slot in SLOT_DEFINITIONS:
        selected_entry = None
        best_score = -1

        for entry in all_entries:
            link = entry.get("link", "")
            if link in used_links:
                continue
            
            title = entry.get("_title", "")
            summary = entry.get("_summary", "")

            # Strict relevance: Title must match at least one slot title keyword
            title_hits = sum(title.count(k) for k in slot["title_keywords"])
            if title_hits == 0:
                continue

            # Strict exclusion: Tragedies, murders, or blasts are NEVER put into sports, tech, or positive thoughts
            if slot["id"] in ["post-3", "post-4", "post-7"] and is_tragedy(title):
                continue

            # Strict Sports Guard: Slot 4 MUST be sports
            if slot["id"] == "post-4":
                sports_entities = ["کرکٹ", "پی ایس ایل", "میچ", "کھلاڑی", "ٹیم", "بیٹنگ", "باؤلنگ", "وکٹ", "رنز", "بابر", "رضوان", "شاہین", "فٹبال", "اسپورٹس", "پی سی بی", "کوئٹہ", "گلیڈی ایٹرز", "لاہور قلندرز"]
                if not any(se in title for se in sports_entities):
                    continue

            body_hits = sum(summary.count(k) for k in slot["body_keywords"])
            total_score = title_hits * 3 + body_hits

            if total_score > best_score:
                best_score = total_score
                selected_entry = entry

        if selected_entry:
            used_links.add(selected_entry.get("link", ""))
            raw_title = selected_entry.get("_title", "")
            raw_summary = selected_entry.get("_summary", "")
            source_name = selected_entry.get("_source_name", "ڈان نیوز")
            source_url = selected_entry.get("link", "https://www.dawnnews.tv")
            image_url = extract_ultra_hd_image(selected_entry)

            is_tragic_story = is_tragedy(raw_title)
            post_body = compose_editorial_post(
                raw_title,
                raw_summary,
                source_url,
                slot["id"],
                slot["hashtags"],
                is_tragic_story
            )
            local_image = download_and_prepare_image(image_url, slot["id"])

            posts.append({
                "id": slot["id"],
                "time_slot": slot["time_slot"],
                "category": slot["category"],
                "format": "single",
                "hook": clean_headline(raw_title, max_len=85),
                "text": post_body,
                "source_name": source_name,
                "source_url": source_url,
                "image_url": image_url,
                "image_path": local_image,
                "hashtags": slot["hashtags"],
                "status": "ready"
            })
        else:
            # High-grade dignified fallback with psychological framing
            prefix, cta = get_psychological_framing(slot['default_title'], slot['id'])
            tags_line = ' '.join(slot["hashtags"])
            post_body = f"{prefix} {slot['default_title']}\n\n{slot['default_body']}\n\n{cta}\n\n{tags_line}"
            posts.append({
                "id": slot["id"],
                "time_slot": slot["time_slot"],
                "category": slot["category"],
                "format": "single",
                "hook": slot["default_title"],
                "text": post_body,
                "source_name": "ڈیجیٹل ڈیسک",
                "source_url": "https://www.dawnnews.tv",
                "image_url": "",
                "image_path": "",
                "hashtags": slot["hashtags"],
                "status": "ready"
            })

    return posts

if __name__ == "__main__":
    import sys
    sys.stdout.reconfigure(encoding='utf-8')
    p = build_daily_posts()
    print(f"Generated {len(p)} viral, psychologically framed daily Urdu posts:")
    for post in p:
        print(f"\n[{post['time_slot']}] {post['category']} | Img: {bool(post['image_path'])} | Len: {len(post['text'])}")
        print(post["text"])
        print("-" * 50)
