import validators
from urllib.parse import urlparse, urlunparse
import re

def validate_url(url: str) -> tuple[bool, str]:
    """
    Valida un URL e restituisce (is_valid, clean_url)
    """
    if not url:
        return False, ""
    
    # Rimuovi spazi
    url = url.strip()
    
    # Aggiungi schema se mancante
    if not url.startswith(('http://', 'https://')):
        url = 'https://' + url
    
    # Valida l'URL
    if not validators.url(url):
        return False, url
    
    # Pulisci l'URL (rimuovi parametri e frammenti dalla base)
    parsed = urlparse(url)
    clean_url = urlunparse((
        parsed.scheme,
        parsed.netloc,
        parsed.path.rstrip('/') or '/',
        '',  # params
        '',  # query
        ''   # fragment
    ))
    
    return True, clean_url

def extract_domain(url: str) -> str:
    """
    Estrae il dominio da un URL
    """
    try:
        parsed = urlparse(url)
        domain = parsed.netloc
        # Rimuovi www. se presente
        if domain.startswith('www.'):
            domain = domain[4:]
        return domain
    except:
        return ""

def clean_text(text: str) -> str:
    """
    Pulisce il testo rimuovendo caratteri speciali e spazi extra
    """
    if not text:
        return ""
    
    # Rimuovi caratteri di controllo
    text = re.sub(r'[\x00-\x1f\x7f-\x9f]', '', text)
    
    # Rimuovi spazi multipli
    text = re.sub(r'\s+', ' ', text)
    
    return text.strip()

def format_file_size(size_bytes: int) -> str:
    """
    Formatta la dimensione del file in formato leggibile
    """
    if size_bytes == 0:
        return "0 B"
    
    size_names = ["B", "KB", "MB", "GB"]
    i = 0
    
    while size_bytes >= 1024 and i < len(size_names) - 1:
        size_bytes /= 1024.0
        i += 1
    
    return f"{size_bytes:.1f} {size_names[i]}"

def truncate_text(text: str, max_length: int = 100, suffix: str = "...") -> str:
    """
    Tronca il testo alla lunghezza massima specificata
    """
    if not text or len(text) <= max_length:
        return text
    
    return text[:max_length - len(suffix)] + suffix

def get_page_type(url: str) -> str:
    """
    Determina il tipo di pagina basato sull'URL
    """
    path = urlparse(url).path.lower()
    
    if path in ['/', '/index.html', '/home', '/homepage']:
        return "Homepage"
    elif '/blog' in path or '/article' in path or '/post' in path:
        return "Blog/Articolo"
    elif '/product' in path or '/shop' in path:
        return "Prodotto/E-commerce"
    elif '/contact' in path:
        return "Contatti"
    elif '/about' in path:
        return "Chi Siamo"
    elif '/service' in path:
        return "Servizi"
    else:
        return "Pagina Generica"

def calculate_reading_time(text: str, words_per_minute: int = 200) -> int:
    """
    Calcola il tempo di lettura stimato per un testo
    """
    if not text:
        return 0
    
    word_count = len(text.split())
    reading_time = max(1, round(word_count / words_per_minute))
    
    return reading_time

def extract_keywords(text: str, min_length: int = 4, max_keywords: int = 10) -> list:
    """
    Estrae le parole chiave più frequenti da un testo
    """
    if not text:
        return []
    
    # Converti in minuscolo e rimuovi punteggiatura
    text = re.sub(r'[^\w\s]', ' ', text.lower())
    
    # Estrai parole
    words = text.split()
    
    # Filtra parole troppo corte e stop words comuni
    stop_words = {
        'che', 'con', 'per', 'una', 'del', 'nel', 'alla', 'dal', 'sul', 'come',
        'sono', 'hanno', 'questo', 'quella', 'essere', 'fare', 'dire', 'dove',
        'quando', 'come', 'chi', 'cosa', 'perché', 'molto', 'più', 'anche',
        'and', 'the', 'for', 'are', 'but', 'not', 'you', 'all', 'can', 'had',
        'her', 'was', 'one', 'our', 'out', 'day', 'get', 'has', 'him', 'his',
        'how', 'man', 'new', 'now', 'old', 'see', 'two', 'way', 'who', 'boy',
        'did', 'its', 'let', 'put', 'say', 'she', 'too', 'use'
    }
    
    filtered_words = [
        word for word in words 
        if len(word) >= min_length and word not in stop_words
    ]
    
    # Conta frequenze
    from collections import Counter
    word_counts = Counter(filtered_words)
    
    # Restituisci le parole più frequenti
    keywords = [word for word, count in word_counts.most_common(max_keywords)]
    
    return keywords

def is_mobile_friendly_indicator(text: str) -> bool:
    """
    Verifica indicatori di mobile-friendliness nel contenuto
    """
    if not text:
        return False
    
    mobile_indicators = [
        'viewport', 'responsive', 'mobile', 'tablet', 'device-width',
        'media query', 'bootstrap', 'flex', 'grid'
    ]
    
    text_lower = text.lower()
    
    for indicator in mobile_indicators:
        if indicator in text_lower:
            return True
    
    return False

def analyze_url_structure(url: str) -> dict:
    """
    Analizza la struttura dell'URL per fattori SEO
    """
    parsed = urlparse(url)
    
    analysis = {
        'has_https': parsed.scheme == 'https',
        'has_www': parsed.netloc.startswith('www.'),
        'path_length': len(parsed.path),
        'has_parameters': bool(parsed.query),
        'has_fragment': bool(parsed.fragment),
        'depth_level': len([p for p in parsed.path.split('/') if p]),
        'contains_keywords': bool(re.search(r'[a-zA-Z]', parsed.path)),
        'has_underscores': '_' in parsed.path,
        'has_uppercase': any(c.isupper() for c in parsed.path)
    }
    
    return analysis

def get_seo_score_for_url(url: str) -> int:
    """
    Calcola un punteggio SEO per la struttura dell'URL
    """
    analysis = analyze_url_structure(url)
    score = 100
    
    # Penalità per vari fattori
    if not analysis['has_https']:
        score -= 20
    
    if analysis['path_length'] > 100:
        score -= 10
    
    if analysis['depth_level'] > 4:
        score -= 10
    
    if analysis['has_underscores']:
        score -= 5
    
    if analysis['has_uppercase']:
        score -= 5
    
    if analysis['has_parameters']:
        score -= 5
    
    return max(0, score)
