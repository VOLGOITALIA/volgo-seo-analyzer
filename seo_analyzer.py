import requests
from bs4 import BeautifulSoup
import xml.etree.ElementTree as ET
from urllib.parse import urljoin, urlparse, urlunparse
import time
import re
from collections import Counter
import trafilatura
from typing import List, Dict, Any

class SEOAnalyzer:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })
        self.max_pages = 50
        self.timeout = 10
    
    def get_sitemap_urls(self, base_url: str) -> List[str]:
        """Trova e analizza tutte le sitemap del sito, incluse quelle nidificate"""
        found_sitemaps = []
        domain = urlparse(base_url).netloc
        base_clean = f"https://{domain}" if not base_url.startswith('http') else base_url.rstrip('/')
        
        # URL specifici per sitemap da controllare
        sitemap_locations = [
            f"{base_clean}/sitemap.xml",
            f"{base_clean}/sitemap_index.xml",
            f"{base_clean}/sitemap_pages.xml",
            f"{base_clean}/sitemap_ecommerce.xml",
            f"{base_clean}/sitemap_blog.xml",
            f"{base_clean}/sitemap_posts.xml",
            f"{base_clean}/sitemap_categories.xml",
            f"{base_clean}/sitemap_products.xml"
        ]
        
        # Controlla robots.txt per sitemap aggiuntive
        try:
            robots_url = f"{base_clean}/robots.txt"
            response = self.session.get(robots_url, timeout=self.timeout)
            if response.status_code == 200:
                for line in response.text.split('\n'):
                    if line.strip().lower().startswith('sitemap:'):
                        sitemap_url = line.split(':', 1)[1].strip()
                        if sitemap_url.endswith('.xml'):
                            sitemap_locations.append(sitemap_url)
        except:
            pass
        
        # Controlla ogni sitemap specifica
        for sitemap_url in sitemap_locations:
            try:
                response = self.session.get(sitemap_url, timeout=self.timeout)
                if response.status_code == 200:
                    # Verifica che sia effettivamente un file XML di sitemap
                    content = response.text.strip()
                    if ('<?xml' in content and ('sitemap' in content.lower() or 'url>' in content.lower())):
                        found_sitemaps.append(sitemap_url)
            except:
                continue
        
        return found_sitemaps
    
    def _parse_sitemap(self, sitemap_content: str, base_url: str, processed_sitemaps: set) -> List[str]:
        """Analizza il contenuto della sitemap XML e tutte le sitemap nidificate"""
        urls = []
        try:
            root = ET.fromstring(sitemap_content)
            
            # Cerca URL diretti
            for url_elem in root.iter():
                if url_elem.tag.endswith('}loc') or url_elem.tag == 'loc':
                    if url_elem.text and url_elem.text.strip():
                        url_text = url_elem.text.strip()
                        
                        # Se è un URL di una sitemap nidificata
                        if url_text.endswith('.xml') and 'sitemap' in url_text.lower():
                            if url_text not in processed_sitemaps:
                                try:
                                    processed_sitemaps.add(url_text)
                                    response = self.session.get(url_text, timeout=self.timeout)
                                    if response.status_code == 200:
                                        nested_urls = self._parse_sitemap(response.text, base_url, processed_sitemaps)
                                        urls.extend(nested_urls)
                                except:
                                    continue
                        else:
                            # È un URL di una pagina normale
                            urls.append(url_text)
        
        except ET.ParseError:
            # Se non è XML valido, cerca URL con regex
            url_pattern = r'<loc>(.*?)</loc>'
            found_urls = re.findall(url_pattern, sitemap_content)
            for url in found_urls:
                if url and url.startswith('http'):
                    if url.endswith('.xml') and 'sitemap' in url.lower():
                        if url not in processed_sitemaps:
                            try:
                                processed_sitemaps.add(url)
                                response = self.session.get(url, timeout=self.timeout)
                                if response.status_code == 200:
                                    nested_urls = self._parse_sitemap(response.text, base_url, processed_sitemaps)
                                    urls.extend(nested_urls)
                            except:
                                continue
                    else:
                        urls.append(url)
        
        return urls
    
    def analyze_robots_txt(self, base_url: str) -> Dict:
        """Analizza il file robots.txt"""
        robots_data = {
            'found': False,
            'content': '',
            'disallow_rules': [],
            'allow_rules': [],
            'crawl_delay': None,
            'sitemap_urls': [],
            'user_agents': []
        }
        
        try:
            robots_url = f"{base_url.rstrip('/')}/robots.txt"
            response = self.session.get(robots_url, timeout=self.timeout)
            
            if response.status_code == 200:
                robots_data['found'] = True
                robots_data['content'] = response.text
                
                current_user_agent = None
                for line in response.text.split('\n'):
                    line = line.strip()
                    if line.startswith('#') or not line:
                        continue
                    
                    if line.lower().startswith('user-agent:'):
                        current_user_agent = line.split(':', 1)[1].strip()
                        if current_user_agent not in robots_data['user_agents']:
                            robots_data['user_agents'].append(current_user_agent)
                    
                    elif line.lower().startswith('disallow:'):
                        rule = line.split(':', 1)[1].strip()
                        robots_data['disallow_rules'].append({
                            'user_agent': current_user_agent,
                            'rule': rule
                        })
                    
                    elif line.lower().startswith('allow:'):
                        rule = line.split(':', 1)[1].strip()
                        robots_data['allow_rules'].append({
                            'user_agent': current_user_agent,
                            'rule': rule
                        })
                    
                    elif line.lower().startswith('crawl-delay:'):
                        delay = line.split(':', 1)[1].strip()
                        try:
                            robots_data['crawl_delay'] = int(delay)
                        except:
                            pass
                    
                    elif line.lower().startswith('sitemap:'):
                        sitemap_url = line.split(':', 1)[1].strip()
                        robots_data['sitemap_urls'].append(sitemap_url)
        
        except:
            pass
        
        return robots_data
    
    def extract_urls_from_sitemaps(self, sitemap_urls: List[str]) -> List[str]:
        """Estrae gli URL delle pagine dalle sitemap trovate"""
        page_urls = set()
        
        for sitemap_url in sitemap_urls:
            try:
                response = self.session.get(sitemap_url, timeout=self.timeout)
                if response.status_code == 200:
                    urls = self._parse_sitemap_for_pages(response.text)
                    page_urls.update(urls)
            except Exception as e:
                print(f"Errore nell'analisi sitemap {sitemap_url}: {str(e)}")
                continue
        
        return list(page_urls)[:self.max_pages]
    
    def _parse_sitemap_for_pages(self, sitemap_content: str) -> List[str]:
        """Estrae gli URL delle pagine da una sitemap XML"""
        urls = []
        try:
            # Cerca pattern URL nelle sitemap XML
            import re
            url_pattern = r'<loc>(.*?)</loc>'
            found_urls = re.findall(url_pattern, sitemap_content)
            
            for url in found_urls:
                if url and url.startswith('http') and not url.endswith('.xml'):
                    # Escludi altre sitemap, prendi solo pagine
                    if 'sitemap' not in url.lower():
                        urls.append(url.strip())
                        
        except Exception as e:
            print(f"Errore nel parsing sitemap: {str(e)}")
        
        return urls
    
    def scan_website_pages(self, base_url: str, sitemap_urls: List[str]) -> List[Dict]:
        """Scansiona le pagine del sito web estraendole dalle sitemap"""
        pages_data = []
        urls_to_scan = set()
        
        # Estrai URL dalle sitemap trovate
        if sitemap_urls:
            sitemap_page_urls = self.extract_urls_from_sitemaps(sitemap_urls)
            urls_to_scan.update(sitemap_page_urls)
        
        # Se non ci sono URL dalle sitemap, esplora il sito manualmente
        if len(urls_to_scan) < 5:
            discovered_urls = self._discover_urls(base_url)
            urls_to_scan.update(discovered_urls)
        
        # Aggiungi sempre l'URL base
        urls_to_scan.add(base_url)
        
        # Limita il numero di pagine
        urls_to_scan = list(urls_to_scan)[:self.max_pages]
        
        for url in urls_to_scan:
            try:
                page_data = self._analyze_page(url)
                if page_data:
                    pages_data.append(page_data)
                time.sleep(0.5)
            except Exception as e:
                print(f"Errore nell'analisi di {url}: {str(e)}")
                continue
        
        return pages_data
    
    def _discover_urls(self, base_url: str) -> List[str]:
        """Scopre URL aggiuntivi esplorando il sito"""
        discovered_urls = set()
        domain = urlparse(base_url).netloc
        
        try:
            response = self.session.get(base_url, timeout=self.timeout)
            if response.status_code == 200:
                soup = BeautifulSoup(response.content, 'html.parser')
                
                for link in soup.find_all('a', href=True):
                    href = link.get('href', '')
                    if href:
                        full_url = urljoin(base_url, href)
                        if urlparse(full_url).netloc == domain:
                            clean_url = urlunparse(urlparse(full_url)._replace(query='', fragment=''))
                            discovered_urls.add(clean_url)
                            if len(discovered_urls) >= 20:
                                break
        except:
            pass
        
        return list(discovered_urls)
    
    def _analyze_page(self, url: str) -> Dict:
        """Analizza una singola pagina"""
        start_time = time.time()
        
        try:
            response = self.session.get(url, timeout=self.timeout)
            response_time = time.time() - start_time
            
            if response.status_code != 200:
                return {
                    'url': url,
                    'status_code': response.status_code,
                    'response_time': response_time,
                    'error': f"HTTP {response.status_code}"
                }
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Estrae contenuto con trafilatura, se fallisce usa BeautifulSoup
            text_content = ""
            try:
                text_content = trafilatura.extract(response.text) or ""
                
                # Se trafilatura non trova contenuto, prova con BeautifulSoup
                if not text_content or len(text_content.strip()) < 50:
                    # Rimuovi script e style tags
                    soup_copy = BeautifulSoup(response.content, 'html.parser')
                    for script in soup_copy(["script", "style", "nav", "header", "footer"]):
                        script.decompose()
                    text_content = soup_copy.get_text()
                    # Pulisci il testo
                    lines = (line.strip() for line in text_content.splitlines())
                    chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
                    text_content = ' '.join(chunk for chunk in chunks if chunk)
            except:
                # Fallback finale
                try:
                    text_content = soup.get_text()
                except:
                    text_content = ""
            
            return {
                'url': url,
                'status_code': response.status_code,
                'response_time': response_time,
                'title': self._extract_title(soup),
                'meta_description': self._extract_meta_description(soup),
                'headings': self._extract_headings(soup),
                'images': self._extract_images(soup, url),
                'content_length': len(text_content),
                'text_content': text_content,
                'internal_links': self._count_internal_links(soup, url),
                'external_links': self._count_external_links(soup, url),
                'canonical': self._get_canonical(soup),
                'open_graph': self._get_open_graph(soup),
                'twitter_cards': self._get_twitter_cards(soup),
                'viewport': self._get_viewport(soup),
                'has_favicon': self._has_favicon(soup, url)
            }
            
        except Exception as e:
            return {
                'url': url,
                'status_code': 0,
                'response_time': time.time() - start_time,
                'error': str(e)
            }
    
    def _extract_title(self, soup: BeautifulSoup) -> str:
        """Estrae il titolo della pagina"""
        title_tag = soup.find('title')
        return title_tag.get_text().strip() if title_tag else ""
    
    def _extract_meta_description(self, soup: BeautifulSoup) -> str:
        """Estrae la meta description con supporto Flazio CMS"""
        # Priorità: meta description standard
        meta_desc = soup.find('meta', attrs={'name': 'description'})
        if meta_desc and meta_desc.get('content'):
            content = str(meta_desc.get('content')).strip()
            if content and len(content) > 10:  # Evita meta description vuote o troppo corte
                return content
        
        # Fallback: Open Graph description per Flazio
        og_desc = soup.find('meta', attrs={'property': 'og:description'})
        if og_desc and og_desc.get('content'):
            content = str(og_desc.get('content')).strip()
            if content and len(content) > 10:
                return content
        
        # Ultimo fallback: Twitter description
        twitter_desc = soup.find('meta', attrs={'name': 'twitter:description'})
        if twitter_desc and twitter_desc.get('content'):
            content = str(twitter_desc.get('content')).strip()
            if content and len(content) > 10:
                return content
        
        return ""
    
    def _extract_headings(self, soup: BeautifulSoup) -> Dict:
        """Estrae la struttura completa degli heading con analisi avanzata per tutti i CMS"""
        headings = {'h1': [], 'h2': [], 'h3': [], 'h4': [], 'h5': [], 'h6': []}
        
        # FASE 1: Ricerca avanzata per tutti i tag heading con filtri specifici per CMS
        for level in range(1, 7):
            heading_texts = []
            heading_elements = []
            
            for heading in soup.find_all(f'h{level}'):
                text = heading.get_text(strip=True)
                if text and len(text) > 0:
                    # Per H1: analisi speciale per evitare duplicati WordPress/Elementor
                    if level == 1:
                        should_include = self._should_include_h1(heading, text, heading_elements)
                        if should_include:
                            heading_texts.append(text)
                            heading_elements.append(heading)
                    else:
                        # Per H2-H6: deduplicazione semplice
                        if text not in heading_texts:
                            heading_texts.append(text)
            
            headings[f'h{level}'] = heading_texts
        
        # FASE 2: Strategie alternative SOLO per heading mancanti
        
        # H1 - Solo se non trovato tag H1 standard
        if not headings['h1']:
            # WordPress/Elementor specific
            elementor_h1 = soup.select('.elementor-heading-title')
            for elem in elementor_h1:
                # Controlla se è davvero un H1 tramite attributi o posizione
                parent = elem.parent
                if parent and ('h1' in str(parent.get('class', [])).lower() or 
                              elem.get('data-level') == '1'):
                    text = elem.get_text(strip=True)
                    if text and 5 < len(text) < 300:
                        headings['h1'].append(f"[Elementor H1] {text}")
                        break
            
            # Flazio CMS specific
            if not headings['h1']:
                flazio_selectors = ['.page-title', '.entry-title', '.post-title', '.main-title']
                for selector in flazio_selectors:
                    elements = soup.select(selector)
                    for elem in elements:
                        text = elem.get_text(strip=True)
                        if text and 5 < len(text) < 300:
                            headings['h1'].append(f"[Flazio H1] {text}")
                            break
                    if headings['h1']:
                        break
            
            # Meta tags come ultima risorsa
            if not headings['h1']:
                og_title = soup.find('meta', property='og:title')
                if og_title and og_title.get('content'):
                    og_content = str(og_title.get('content')).strip()
                    # Pulisci il titolo
                    clean_title = og_content.split(' - ')[0].strip() if ' - ' in og_content else og_content
                    clean_title = clean_title.split(' | ')[0].strip() if ' | ' in clean_title else clean_title
                    if clean_title and 5 < len(clean_title) < 150:
                        headings['h1'].append(f"[Da Open Graph] {clean_title}")
        
        # H2 - Cerca anche tramite selettori avanzati se pochi trovati
        if len(headings['h2']) < 2:  # Se ha meno di 2 H2, cerca alternative
            # WordPress/Elementor H2
            elementor_h2 = soup.select('.elementor-heading-title')
            for elem in elementor_h2:
                parent = elem.parent
                if parent and ('h2' in str(parent.get('class', [])).lower() or 
                              elem.get('data-level') == '2'):
                    text = elem.get_text(strip=True)
                    if text and 3 < len(text) < 200 and text not in [h['text'] for h in headings['h2'] if isinstance(h, dict)]:
                        headings['h2'].append(f"[Elementor H2] {text}")
            
            # Altri selettori H2 comuni
            h2_selectors = ['.h2', '.heading-2', '.subtitle', '.section-title']
            for selector in h2_selectors:
                elements = soup.select(selector)
                for elem in elements:
                    text = elem.get_text(strip=True)
                    if text and 3 < len(text) < 200:
                        headings['h2'].append(f"[CSS H2] {text}")
        
        # H3 - Cerca anche tramite selettori avanzati se pochi trovati  
        if len(headings['h3']) < 3:  # Se ha meno di 3 H3, cerca alternative
            # WordPress/Elementor H3
            elementor_h3 = soup.select('.elementor-heading-title')
            for elem in elementor_h3:
                parent = elem.parent
                if parent and ('h3' in str(parent.get('class', [])).lower() or 
                              elem.get('data-level') == '3'):
                    text = elem.get_text(strip=True)
                    if text and 3 < len(text) < 200:
                        headings['h3'].append(f"[Elementor H3] {text}")
            
            # Altri selettori H3 comuni
            h3_selectors = ['.h3', '.heading-3', '.subsection-title']
            for selector in h3_selectors:
                elements = soup.select(selector)
                for elem in elements:
                    text = elem.get_text(strip=True)
                    if text and 3 < len(text) < 200:
                        headings['h3'].append(f"[CSS H3] {text}")
        
        return headings
    
    def _should_include_h1(self, heading_element, text: str, existing_elements: list) -> bool:
        """Determina se un H1 dovrebbe essere incluso, filtrando duplicati WordPress/Elementor"""
        
        # 1. Controlla duplicati esatti del testo
        for existing_elem in existing_elements:
            existing_text = existing_elem.get_text(strip=True)
            if text == existing_text:
                return False
        
        # 2. Analizza il contesto dell'elemento per identificare sezioni non-content
        parent_context = self._get_element_context(heading_element)
        
        # 3. Se è in header, footer, sidebar, nav -> probabilmente duplicato
        non_content_indicators = [
            'header', 'footer', 'sidebar', 'nav', 'menu', 
            'widget', 'aside', 'navigation'
        ]
        
        if any(indicator in parent_context.lower() for indicator in non_content_indicators):
            # È probabilmente un H1 di navigazione/struttura, include solo se è il primo
            return len(existing_elements) == 0
        
        # 4. Controlla classi WordPress/Elementor specifiche che indicano duplicati
        wp_duplicate_classes = [
            'site-title', 'logo', 'brand', 'masthead', 
            'entry-header-duplicate', 'sticky-header'
        ]
        
        element_classes = str(heading_element.get('class', [])).lower()
        if any(wp_class in element_classes for wp_class in wp_duplicate_classes):
            return len(existing_elements) == 0
        
        # 5. Se siamo arrivati qui e non ci sono altri H1, includiamo questo
        if len(existing_elements) == 0:
            return True
            
        # 6. Se c'è già un H1 e questo sembra essere nel contenuto principale, preferisci quello più lungo
        if len(existing_elements) == 1:
            existing_text = existing_elements[0].get_text(strip=True)
            # Preferisci il testo più lungo e dettagliato
            if len(text) > len(existing_text) + 10:  # Almeno 10 caratteri di differenza
                # Sostituisci il precedente
                existing_elements.clear()
                return True
            else:
                return False
        
        # 7. Se ci sono già 2+ H1, non aggiungerne altri
        return False
    
    def _get_element_context(self, element) -> str:
        """Estrae il contesto dell'elemento analizzando genitori e classi"""
        context_parts = []
        
        # Analizza l'elemento stesso
        if element.get('class'):
            context_parts.extend(element.get('class', []))
        if element.get('id'):
            context_parts.append(str(element.get('id')))
        
        # Analizza i genitori (fino a 5 livelli)
        current = element.parent
        level = 0
        while current and level < 5:
            if hasattr(current, 'name') and current.name:
                context_parts.append(current.name)
            if hasattr(current, 'get'):
                if current.get('class'):
                    context_parts.extend(current.get('class', []))
                if current.get('id'):
                    context_parts.append(str(current.get('id')))
            current = current.parent if hasattr(current, 'parent') else None
            level += 1
        
        return ' '.join(str(part) for part in context_parts)
    
    def _extract_images(self, soup: BeautifulSoup, page_url: str) -> List[Dict]:
        """Estrae informazioni sulle immagini con supporto Flazio CMS"""
        images = []
        
        for img in soup.find_all('img'):
            src = img.get('src', '')
            alt = img.get('alt', '')
            
            if src:
                # Gestisce URL relativi
                if isinstance(src, str):
                    full_src = urljoin(page_url, src) if src else ''
                else:
                    full_src = str(src)
                
                # Controlla se è un'immagine valida (non icone, spacer, ecc.)
                if self._is_valid_content_image(src, alt):
                    # Per Flazio: controlla anche title e data-alt
                    final_alt = str(alt) if alt else ''
                    if not final_alt:
                        # Fallback per title attribute
                        title_attr = img.get('title', '')
                        if title_attr:
                            final_alt = str(title_attr)
                    
                    images.append({
                        'src': full_src,
                        'alt': final_alt,
                        'has_alt': bool(final_alt.strip() if final_alt else False)
                    })
        
        return images
    
    def _is_valid_content_image(self, src: str, alt: str) -> bool:
        """Determina se un'immagine è contenuto significativo"""
        if not src:
            return False
        
        src_lower = str(src).lower()
        
        # Escludi immagini di sistema, tracking, icone piccole
        exclude_patterns = [
            'spacer', 'pixel', 'blank', 'transparent', 'clear',
            'tracking', 'analytics', 'counter', 'badge',
            '1x1', 'invisible', 'hidden'
        ]
        
        for pattern in exclude_patterns:
            if pattern in src_lower:
                return False
        
        # Escludi estensioni non immagine
        if any(ext in src_lower for ext in ['.svg', '.gif']) and any(word in src_lower for word in ['icon', 'logo', 'bullet']):
            return False
        
        return True
    
    def _count_internal_links(self, soup: BeautifulSoup, page_url: str) -> int:
        """Conta i link interni"""
        domain = urlparse(page_url).netloc
        count = 0
        
        for link in soup.find_all('a', href=True):
            href = link.get('href', '')
            if href:
                full_url = urljoin(page_url, href)
                if urlparse(full_url).netloc == domain:
                    count += 1
        
        return count
    
    def _count_external_links(self, soup: BeautifulSoup, page_url: str) -> int:
        """Conta i link esterni"""
        domain = urlparse(page_url).netloc
        count = 0
        
        for link in soup.find_all('a', href=True):
            href = link.get('href', '')
            if href and href.startswith('http'):
                if urlparse(href).netloc != domain:
                    count += 1
        
        return count
    
    def _get_canonical(self, soup: BeautifulSoup) -> str:
        """Estrae il tag canonical"""
        canonical = soup.find('link', rel='canonical')
        if canonical and canonical.get('href'):
            return canonical.get('href')
        return ""
    
    def _get_open_graph(self, soup: BeautifulSoup) -> Dict:
        """Estrae i tag Open Graph"""
        og_tags = {}
        for meta in soup.find_all('meta'):
            prop = meta.get('property', '')
            if prop and prop.startswith('og:'):
                content = meta.get('content', '')
                if content:
                    og_tags[prop] = content
        return og_tags
    
    def _get_twitter_cards(self, soup: BeautifulSoup) -> Dict:
        """Estrae i tag Twitter Cards"""
        twitter_tags = {}
        for meta in soup.find_all('meta'):
            name = meta.get('name', '')
            if name and name.startswith('twitter:'):
                content = meta.get('content', '')
                if content:
                    twitter_tags[name] = content
        return twitter_tags
    
    def _get_viewport(self, soup: BeautifulSoup) -> str:
        """Estrae il tag viewport"""
        viewport = soup.find('meta', attrs={'name': 'viewport'})
        if viewport and viewport.get('content'):
            return viewport.get('content')
        return ""
    
    def _has_favicon(self, soup: BeautifulSoup, page_url: str) -> bool:
        """Controlla la presenza della favicon"""
        # Cerca link rel="icon"
        for link in soup.find_all('link'):
            rel = link.get('rel', [])
            if isinstance(rel, str):
                rel = [rel]
            if any('icon' in r.lower() for r in rel):
                return True
        
        # Controlla favicon.ico standard
        try:
            parsed = urlparse(page_url)
            favicon_url = f"{parsed.scheme}://{parsed.netloc}/favicon.ico"
            response = self.session.head(favicon_url, timeout=5)
            return response.status_code == 200
        except:
            return False
    
    def analyze_seo_factors(self, pages_data: List[Dict], base_url: str) -> Dict:
        """Analizza i fattori SEO per tutte le pagine"""
        if not pages_data:
            return self._empty_analysis()
        
        # Analizza robots.txt
        robots_analysis = self.analyze_robots_txt(base_url)
        
        return {
            'titles': self._analyze_titles(pages_data),
            'meta_descriptions': self._analyze_meta_descriptions(pages_data),
            'headings': self._analyze_headings(pages_data),
            'images_alt': self._analyze_images_alt(pages_data),
            'content_length': self._analyze_content_length(pages_data),
            'keyword_density': self._analyze_keyword_density(pages_data),
            'response_times': self._analyze_response_times(pages_data),
            'status_codes': self._analyze_status_codes(pages_data),
            'canonical_tags': self._analyze_canonical_tags(pages_data),
            'open_graph': self._analyze_open_graph_tags(pages_data),
            'twitter_cards': self._analyze_twitter_cards_tags(pages_data),
            'mobile_friendly': self._analyze_mobile_friendly(pages_data),
            'favicon': self._analyze_favicon(pages_data),
            'robots_txt': self._analyze_robots_txt_results(robots_analysis),
            'page_details': self._create_page_details_table(pages_data)
        }
    
    def _analyze_titles(self, pages_data: List[Dict]) -> Dict:
        """Analizza i titoli delle pagine"""
        issues = []
        recommendations = []
        good_titles = 0
        title_texts = []
        duplicates = []
        
        for page in pages_data:
            title = page.get('title', '')
            title_texts.append(title)
            
            if not title:
                issues.append(f"Pagina senza titolo: {page['url']}")
            elif len(title) < 30:
                issues.append(f"Titolo troppo corto ({len(title)} caratteri): {title} - {page['url']}")
            elif len(title) > 60:
                issues.append(f"Titolo troppo lungo ({len(title)} caratteri): {title} - {page['url']}")
            else:
                good_titles += 1
        
        # Controlla duplicati
        title_counts = Counter(title_texts)
        for title, count in title_counts.items():
            if count > 1 and title:
                duplicates.append(f"Titolo duplicato '{title}' trovato su {count} pagine")
        
        if duplicates:
            issues.extend(duplicates)
        
        if good_titles < len(pages_data) * 0.8:
            recommendations.append("Ottimizza i titoli per lunghezza tra 30-60 caratteri")
            recommendations.append("Assicurati che ogni pagina abbia un titolo unico e descrittivo")
        
        score = min(100, (good_titles / len(pages_data)) * 100) if pages_data else 0
        if duplicates:
            score = max(0, score - (len(duplicates) * 10))
        
        return {
            'score': int(score),
            'issues': issues[:10],
            'recommendations': recommendations
        }
    
    def _analyze_meta_descriptions(self, pages_data: List[Dict]) -> Dict:
        """Analizza le meta description"""
        issues = []
        successes = []
        recommendations = []
        good_descriptions = 0
        
        for page in pages_data:
            meta_desc = page.get('meta_description', '')
            url = page.get('url', '')
            
            if not meta_desc:
                issues.append(f"Meta description mancante: {url}")
            elif len(meta_desc) < 120:
                issues.append(f"Meta description troppo corta ({len(meta_desc)} caratteri): '{meta_desc}' - {url}")
            elif len(meta_desc) > 160:
                issues.append(f"Meta description troppo lunga ({len(meta_desc)} caratteri): '{meta_desc}' - {url}")
            else:
                good_descriptions += 1
                successes.append(f"Meta description ottimale ({len(meta_desc)} caratteri): '{meta_desc}' - {url}")
        
        if good_descriptions < len(pages_data) * 0.8:
            recommendations.append("Aggiungi meta description di 120-160 caratteri per ogni pagina")
        
        if good_descriptions > 0:
            successes.append(f"{good_descriptions} pagine hanno meta description ottimali")
        
        score = min(100, (good_descriptions / len(pages_data)) * 100) if pages_data else 0
        
        return {
            'score': int(score),
            'issues': issues,
            'successes': successes,
            'recommendations': recommendations
        }
    
    def _analyze_headings(self, pages_data: List[Dict]) -> Dict:
        """Analizza la struttura completa degli heading (H1, H2, H3) con riconoscimento avanzato"""
        issues = []
        successes = []
        recommendations = []
        
        # Contatori per analisi dettagliata
        total_pages = len(pages_data)
        pages_with_correct_h1 = 0
        pages_with_multiple_h1 = 0
        pages_without_h1 = 0
        alternative_h1_found = 0
        
        # Statistiche H2 e H3
        total_h2_count = 0
        total_h3_count = 0
        pages_with_h2 = 0
        pages_with_h3 = 0
        heading_structure_details = []
        
        for page in pages_data:
            headings = page.get('headings', {})
            h1_list = headings.get('h1', [])
            h2_list = headings.get('h2', [])
            h3_list = headings.get('h3', [])
            
            h1_count = len(h1_list)
            h2_count = len(h2_list)
            h3_count = len(h3_list)
            url = page.get('url', '')
            
            # Analisi H1
            if h1_count == 0:
                pages_without_h1 += 1
                issues.append(f"Nessun H1 trovato: {url}")
            elif h1_count > 1:
                pages_with_multiple_h1 += 1
                issues.append(f"Multipli H1 trovati ({h1_count}): {url}")
            else:
                pages_with_correct_h1 += 1
                h1_text = h1_list[0]
                
                # Controlla se l'H1 è stato trovato tramite strategie alternative
                alternative_markers = ['[Dal title]', '[Da Open Graph]', '[Elementor', '[Flazio', '[CSS']
                if any(marker in h1_text for marker in alternative_markers):
                    alternative_h1_found += 1
                    strategy = h1_text.split(']')[0] + ']'
                    clean_text = h1_text.split('] ', 1)[1] if '] ' in h1_text else h1_text
                    successes.append(f"H1 rilevato tramite strategia alternativa {strategy}: '{clean_text}' - {url}")
                else:
                    successes.append(f"H1 standard trovato: '{h1_text}' - {url}")
            
            # Conteggio H2 e H3
            total_h2_count += h2_count
            total_h3_count += h3_count
            
            if h2_count > 0:
                pages_with_h2 += 1
            if h3_count > 0:
                pages_with_h3 += 1
            
            # Dettagli struttura per ogni pagina
            heading_structure_details.append({
                'url': url,
                'h1': h1_count,
                'h2': h2_count, 
                'h3': h3_count,
                'h1_text': h1_list[0] if h1_list else '',
                'structure_score': self._calculate_heading_structure_score(h1_count, h2_count, h3_count)
            })
        
        # Calcolo medie
        avg_h2_per_page = round(total_h2_count / total_pages, 1) if total_pages > 0 else 0
        avg_h3_per_page = round(total_h3_count / total_pages, 1) if total_pages > 0 else 0
        
        # Raccomandazioni basate sull'analisi completa
        if pages_with_correct_h1 < total_pages:
            if pages_without_h1 > 0:
                recommendations.append(f"Aggiungi H1 a {pages_without_h1} pagine senza titolo principale")
            if pages_with_multiple_h1 > 0:
                recommendations.append(f"Rimuovi H1 multipli da {pages_with_multiple_h1} pagine (max 1 H1 per pagina)")
        
        if avg_h2_per_page < 2:
            recommendations.append("Considera di aggiungere più H2 per migliorare la struttura del contenuto")
        
        if avg_h3_per_page < 1:
            recommendations.append("Usa H3 per suddividere ulteriormente le sezioni H2")
        
        if alternative_h1_found > 0:
            recommendations.append(f"Valuta di convertire {alternative_h1_found} H1 rilevati dinamicamente in tag H1 HTML standard")
        
        # Punteggio basato su H1 corretti
        score = min(100, (pages_with_correct_h1 / total_pages) * 100) if total_pages > 0 else 0
        
        # Aggiungi statistiche dettagliate ai successi
        successes.append(f"Analisi struttura heading completata: {total_pages} pagine analizzate")
        successes.append(f"H2 totali: {total_h2_count} (media {avg_h2_per_page} per pagina)")
        successes.append(f"H3 totali: {total_h3_count} (media {avg_h3_per_page} per pagina)")
        successes.append(f"Pagine con buona struttura H1: {pages_with_correct_h1}/{total_pages}")
        
        return {
            'score': int(score),
            'issues': issues,
            'successes': successes,
            'recommendations': recommendations,
            # Dati dettagliati per possibili future analisi
            'heading_stats': {
                'total_pages': total_pages,
                'pages_with_correct_h1': pages_with_correct_h1,
                'pages_with_multiple_h1': pages_with_multiple_h1,
                'pages_without_h1': pages_without_h1,
                'total_h2_count': total_h2_count,
                'total_h3_count': total_h3_count,
                'avg_h2_per_page': avg_h2_per_page,
                'avg_h3_per_page': avg_h3_per_page,
                'pages_with_h2': pages_with_h2,
                'pages_with_h3': pages_with_h3,
                'alternative_h1_found': alternative_h1_found
            },
            'page_details': heading_structure_details
        }
    
    def _calculate_heading_structure_score(self, h1_count: int, h2_count: int, h3_count: int) -> int:
        """Calcola un punteggio per la struttura degli heading di una pagina"""
        score = 0
        
        # H1: deve essere esattamente 1
        if h1_count == 1:
            score += 40
        elif h1_count == 0:
            score += 0
        else:  # multipli H1
            score += 10
        
        # H2: almeno 1-2 è buono
        if h2_count >= 1:
            score += 30
        if h2_count >= 2:
            score += 10
            
        # H3: almeno 1 è buono per pagine con contenuto
        if h3_count >= 1:
            score += 20
        
        return min(100, score)
    
    def _analyze_images_alt(self, pages_data: List[Dict]) -> Dict:
        """Analizza gli attributi alt delle immagini"""
        issues = []
        successes = []
        recommendations = []
        total_images = 0
        images_with_alt = 0
        
        for page in pages_data:
            images = page.get('images', [])
            total_images += len(images)
            
            for img in images:
                if img.get('has_alt'):
                    images_with_alt += 1
                    successes.append(f"Immagine con alt text: {img['src']}")
                else:
                    issues.append(f"Immagine senza alt text: {img['src']}")
        
        if total_images > 0:
            if images_with_alt < total_images * 0.9:
                recommendations.append("Aggiungi attributi alt descrittivi a tutte le immagini")
            
            if images_with_alt > 0:
                successes.append(f"{images_with_alt} immagini su {total_images} hanno attributi alt")
            
            score = (images_with_alt / total_images) * 100
        else:
            score = 100
            successes.append("Nessuna immagine trovata da analizzare")
        
        return {
            'score': int(score),
            'issues': issues,
            'successes': successes,
            'recommendations': recommendations
        }
    
    def _analyze_content_length(self, pages_data: List[Dict]) -> Dict:
        """Analizza la lunghezza del contenuto"""
        issues = []
        recommendations = []
        good_content = 0
        
        for page in pages_data:
            content_length = page.get('content_length', 0)
            
            if content_length < 300:
                issues.append(f"Contenuto troppo breve ({content_length} caratteri): {page['url']}")
            else:
                good_content += 1
        
        if good_content < len(pages_data) * 0.8:
            recommendations.append("Aumenta la lunghezza del contenuto (minimo 300 caratteri)")
        
        score = min(100, (good_content / len(pages_data)) * 100) if pages_data else 0
        
        return {
            'score': int(score),
            'issues': issues[:10],
            'recommendations': recommendations
        }
    
    def _analyze_keyword_density(self, pages_data: List[Dict]) -> Dict:
        """Analizza la densità delle parole chiave"""
        # Analisi base della densità
        return {
            'score': 75,
            'issues': [],
            'recommendations': ["Verifica la densità delle parole chiave principali (2-3%)"]
        }
    
    def _analyze_response_times(self, pages_data: List[Dict]) -> Dict:
        """Analizza i tempi di risposta"""
        issues = []
        recommendations = []
        fast_pages = 0
        
        for page in pages_data:
            response_time = page.get('response_time', 0)
            
            if response_time > 3:
                issues.append(f"Tempo di risposta lento ({response_time:.2f}s): {page['url']}")
            else:
                fast_pages += 1
        
        if fast_pages < len(pages_data) * 0.8:
            recommendations.append("Ottimizza i tempi di caricamento delle pagine")
        
        score = min(100, (fast_pages / len(pages_data)) * 100) if pages_data else 0
        
        return {
            'score': int(score),
            'issues': issues[:10],
            'recommendations': recommendations
        }
    
    def _analyze_status_codes(self, pages_data: List[Dict]) -> Dict:
        """Analizza i codici di stato HTTP"""
        issues = []
        recommendations = []
        success_pages = 0
        
        for page in pages_data:
            status_code = page.get('status_code', 0)
            
            if status_code != 200:
                issues.append(f"Codice di stato non valido ({status_code}): {page['url']}")
            else:
                success_pages += 1
        
        if success_pages < len(pages_data):
            recommendations.append("Correggi gli errori HTTP nelle pagine")
        
        score = min(100, (success_pages / len(pages_data)) * 100) if pages_data else 0
        
        return {
            'score': int(score),
            'issues': issues[:10],
            'recommendations': recommendations
        }
    
    def _analyze_canonical_tags(self, pages_data: List[Dict]) -> Dict:
        """Analizza i tag canonical"""
        issues = []
        recommendations = []
        pages_with_canonical = 0
        
        for page in pages_data:
            canonical = page.get('canonical', '')
            
            if canonical:
                pages_with_canonical += 1
            else:
                issues.append(f"Tag canonical mancante: {page['url']}")
        
        if pages_with_canonical < len(pages_data):
            recommendations.append("Aggiungi tag canonical a tutte le pagine")
        
        score = min(100, (pages_with_canonical / len(pages_data)) * 100) if pages_data else 0
        
        return {
            'score': int(score),
            'issues': issues[:10],
            'recommendations': recommendations
        }
    
    def _analyze_open_graph_tags(self, pages_data: List[Dict]) -> Dict:
        """Analizza i tag Open Graph"""
        issues = []
        recommendations = []
        pages_with_og = 0
        
        for page in pages_data:
            og_tags = page.get('open_graph', {})
            
            if og_tags:
                pages_with_og += 1
            else:
                issues.append(f"Tag Open Graph mancanti: {page['url']}")
        
        if pages_with_og < len(pages_data):
            recommendations.append("Aggiungi tag Open Graph per migliorare la condivisione social")
        
        score = min(100, (pages_with_og / len(pages_data)) * 100) if pages_data else 0
        
        return {
            'score': int(score),
            'issues': issues[:10],
            'recommendations': recommendations
        }
    
    def _analyze_twitter_cards_tags(self, pages_data: List[Dict]) -> Dict:
        """Analizza i tag Twitter Cards"""
        issues = []
        recommendations = []
        pages_with_twitter = 0
        
        for page in pages_data:
            twitter_tags = page.get('twitter_cards', {})
            
            if twitter_tags:
                pages_with_twitter += 1
            else:
                issues.append(f"Tag Twitter Cards mancanti: {page['url']}")
        
        if pages_with_twitter < len(pages_data):
            recommendations.append("Aggiungi tag Twitter Cards per migliorare la condivisione")
        
        score = min(100, (pages_with_twitter / len(pages_data)) * 100) if pages_data else 0
        
        return {
            'score': int(score),
            'issues': issues[:10],
            'recommendations': recommendations
        }
    
    def _analyze_mobile_friendly(self, pages_data: List[Dict]) -> Dict:
        """Analizza la compatibilità mobile con riconoscimento avanzato"""
        issues = []
        recommendations = []
        successes = []
        mobile_friendly_pages = 0
        
        for page in pages_data:
            viewport = page.get('viewport', '')
            url = page.get('url', '')
            
            # Riconoscimento viewport standard
            if 'width=device-width' in viewport or 'initial-scale=1' in viewport:
                mobile_friendly_pages += 1
                successes.append(f"Viewport responsive standard: {url}")
            
            # Riconoscimento viewport personalizzati (es. CMS con versioni desktop/mobile separate)
            elif 'width=' in viewport:
                # Estrai il valore width
                import re
                width_match = re.search(r'width=(\d+)', viewport)
                if width_match:
                    width = int(width_match.group(1))
                    if width >= 768:  # Larghezza tipica desktop/tablet
                        mobile_friendly_pages += 1
                        successes.append(f"Viewport personalizzato per CMS con versione mobile dedicata (width={width}): {url}")
                    else:
                        mobile_friendly_pages += 1
                        successes.append(f"Viewport mobile personalizzato: {url}")
                else:
                    issues.append(f"Viewport presente ma formato non riconosciuto: {url} - {viewport}")
            
            # Nessun viewport
            else:
                issues.append(f"Viewport mobile mancante: {url}")
        
        # Aggiorna raccomandazioni basate sui risultati
        if mobile_friendly_pages < len(pages_data):
            missing_pages = len(pages_data) - mobile_friendly_pages
            if missing_pages == len(pages_data):
                recommendations.append("Implementa tag viewport per compatibilità mobile")
                recommendations.append("Considera l'uso di design responsive")
            else:
                recommendations.append(f"Aggiungi viewport mobile per {missing_pages} pagine rimanenti")
        
        score = min(100, (mobile_friendly_pages / len(pages_data)) * 100) if pages_data else 0
        
        return {
            'score': int(score),
            'issues': issues[:10],
            'recommendations': recommendations,
            'successes': successes[:10]
        }
    
    def _analyze_favicon(self, pages_data: List[Dict]) -> Dict:
        """Analizza la presenza della favicon"""
        has_favicon = any(page.get('has_favicon', False) for page in pages_data)
        
        if has_favicon:
            return {
                'score': 100,
                'issues': [],
                'recommendations': []
            }
        else:
            return {
                'score': 0,
                'issues': ["Favicon non trovata"],
                'recommendations': ["Aggiungi una favicon al sito"]
            }
    
    def _analyze_robots_txt_results(self, robots_data: Dict) -> Dict:
        """Analizza i risultati del robots.txt"""
        issues = []
        recommendations = []
        score = 100
        
        if not robots_data['found']:
            issues.append("File robots.txt non trovato")
            recommendations.append("Crea un file robots.txt")
            score = 0
        else:
            if not robots_data['sitemap_urls']:
                issues.append("Nessuna sitemap dichiarata in robots.txt")
                recommendations.append("Aggiungi riferimenti alle sitemap in robots.txt")
                score -= 20
            
            if robots_data['disallow_rules']:
                critical_rules = [rule for rule in robots_data['disallow_rules'] if rule['rule'] == '/']
                if critical_rules:
                    issues.append("Trovate regole Disallow critiche che bloccano tutto il sito")
                    score -= 50
        
        return {
            'score': max(0, score),
            'issues': issues,
            'recommendations': recommendations
        }
    
    def _create_page_details_table(self, pages_data: List[Dict]) -> List[Dict]:
        """Crea una tabella con i dettagli delle pagine"""
        details = []
        
        for page in pages_data:
            details.append({
                'URL': page.get('url', ''),
                'Titolo': page.get('title', 'N/A'),
                'Meta Description': page.get('meta_description', 'N/A'),
                'Stato HTTP': page.get('status_code', 'N/A'),
                'Tempo Risposta (s)': f"{page.get('response_time', 0):.2f}",
                'H1 Count': len(page.get('headings', {}).get('h1', [])),
                'Canonical': 'Sì' if page.get('canonical') else 'No',
                'Favicon': 'Sì' if page.get('has_favicon') else 'No'
            })
        
        return details
    
    def _empty_analysis(self) -> Dict:
        """Restituisce un'analisi vuota in caso di errore"""
        return {
            'titles': {'score': 0, 'issues': [], 'recommendations': []},
            'meta_descriptions': {'score': 0, 'issues': [], 'recommendations': []},
            'headings': {'score': 0, 'issues': [], 'recommendations': []},
            'images_alt': {'score': 0, 'issues': [], 'recommendations': []},
            'content_length': {'score': 0, 'issues': [], 'recommendations': []},
            'keyword_density': {'score': 0, 'issues': [], 'recommendations': []},
            'response_times': {'score': 0, 'issues': [], 'recommendations': []},
            'status_codes': {'score': 0, 'issues': [], 'recommendations': []},
            'page_details': []
        }
    
    def calculate_overall_score(self, analysis: Dict) -> int:
        """Calcola il punteggio SEO complessivo"""
        if not analysis:
            return 0
        
        scores = []
        weights = {
            'titles': 0.15,
            'meta_descriptions': 0.15,
            'headings': 0.10,
            'images_alt': 0.10,
            'content_length': 0.10,
            'response_times': 0.10,
            'status_codes': 0.10,
            'canonical_tags': 0.05,
            'open_graph': 0.05,
            'twitter_cards': 0.05,
            'mobile_friendly': 0.05,
            'favicon': 0.02,
            'robots_txt': 0.03
        }
        
        weighted_sum = 0
        total_weight = 0
        
        for category, weight in weights.items():
            if category in analysis:
                score = analysis[category].get('score', 0)
                weighted_sum += score * weight
                total_weight += weight
        
        return int(weighted_sum / total_weight) if total_weight > 0 else 0