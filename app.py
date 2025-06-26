import streamlit as st
import pandas as pd
import time
from seo_analyzer import SEOAnalyzer
from pdf_generator import PDFGenerator
from urllib.parse import urlparse
import validators
from utils import validate_url
from analytics_storage import AnalyticsStorage

# Configurazione pagina
st.set_page_config(
    page_title="Analizzatore SEO",
    page_icon="🔍",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# CSS personalizzato per design moderno
st.markdown("""
<style>
.stApp {
    background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
    display: flex;
    flex-direction: column;
    min-height: 100vh;
}
.header-container {
    background-color: #000000;
    padding: 1rem 2rem;
    margin: -1rem -1rem 0 -1rem;
    width: 100vw;
    position: relative;
    left: 50%;
    right: 50%;
    margin-left: -50vw;
    margin-right: -50vw;
    display: flex;
    align-items: center;
    justify-content: flex-start;
    box-shadow: 0 2px 10px rgba(0,0,0,0.2);
}
.logo-container {
    display: flex;
    align-items: center;
}
.header-logo {
    height: 60px;
    width: auto;
    object-fit: contain;
}
.main-header {
    text-align: center;
    color: #1f77b4;
    font-size: 2.5rem;
    font-weight: bold;
    margin-bottom: 1rem;
}
.footer-container {
    background-color: #000000;
    color: white;
    text-align: center;
    padding: 2rem;
    margin: 0 -1rem 0 -1rem;  /* togli margini top e bottom */
    width: 100vw;
    position: relative;
    left: 50%;
    right: 50%;
    margin-left: -50vw;
    margin-right: -50vw;
    font-size: 1rem;
    box-shadow: 0 -2px 10px rgba(0,0,0,0.2);
    flex-shrink: 0; /* aggiungi questa! */
}
.metric-card {
    background: rgba(255, 255, 255, 0.95);
    padding: 1.5rem;
    border-radius: 15px;
    box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1);
    border: 1px solid rgba(255, 255, 255, 0.18);
    backdrop-filter: blur(10px);
    margin-bottom: 1rem;
}
.score-display {
    text-align: center;
    font-size: 3rem;
    font-weight: bold;
    margin: 1rem 0;
}
.score-description {
    text-align: center;
    font-size: 1.2rem;
    margin-bottom: 1rem;
}
.info-section {
    background: rgba(255, 255, 255, 0.9);
    padding: 1.5rem;
    border-radius: 12px;
    margin: 1rem 0;
    border-left: 4px solid #1f77b4;
    box-shadow: 0 4px 16px rgba(0, 0, 0, 0.05);
}
.sitemap-item {
    background: rgba(248, 249, 250, 0.9);
    padding: 1rem;
    border-radius: 8px;
    margin: 0.5rem 0;
    border: 1px solid #e9ecef;
    font-family: monospace;
    font-size: 0.9rem;
}
.issue-item {
    background: rgba(255, 243, 243, 0.9);
    padding: 1rem;
    border-radius: 8px;
    margin: 0.5rem 0;
    border-left: 4px solid #ff6b6b;
    box-shadow: 0 2px 8px rgba(255, 107, 107, 0.1);
}
.recommendation-item {
    background: rgba(243, 255, 243, 0.9);
    padding: 1rem;
    border-radius: 8px;
    margin: 0.5rem 0;
    border-left: 4px solid #51cf66;
    box-shadow: 0 2px 8px rgba(81, 207, 102, 0.1);
}
.analysis-header {
    font-size: 1.3rem;
    font-weight: 600;
    color: #1f77b4;
    margin-bottom: 1rem;
    padding-bottom: 0.5rem;
    border-bottom: 2px solid #e9ecef;
}
.stTabs [data-baseweb="tab-list"] {
    gap: 8px;
    background: rgba(255, 255, 255, 0.5);
    padding: 0.5rem;
    border-radius: 12px;
}
.stTabs [data-baseweb="tab"] {
    background: rgba(255, 255, 255, 0.8);
    border-radius: 8px;
    padding: 0.8rem 1.5rem;
    border: none;
    font-weight: 500;
}
.stTabs [aria-selected="true"] {
    background: rgba(31, 119, 180, 0.15);
    border: 2px solid #1f77b4;
    color: #1f77b4;
}
.summary-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
    gap: 1rem;
    margin: 1rem 0;
}
</style>
""", unsafe_allow_html=True)

def main():
    # Header nero con logo
    st.markdown("""
    <div class="header-container">
        <div class="logo-container">
            <img src="volgoseo.png" alt="LOGO VOLGO SEO" class="header-logo">
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # Titolo principale fuori dall'header
    st.markdown('<h1 class="main-header">Analisi SEO Gratuita</h1>', unsafe_allow_html=True)
    
    # Sottotitolo e disclaimer
    st.markdown("""
    <div style="text-align: center; margin-bottom: 2rem;">
        <p style="font-size: 1.2rem; color: #666; margin-bottom: 1rem;">
            Analizza il tuo sito web e ottieni un report SEO dettagliato
        </p>
        <p style="font-size: 0.9rem; color: #888; font-style: italic; max-width: 800px; margin: 0 auto;">
            I dati forniti sono il risultato di un'analisi automatizzata che può presentare limitazioni. 
            I risultati potrebbero non essere completi o differire da analisi manuali professionali. 
            Questo strumento è pensato come supporto per comprendere le basi SEO del tuo sito web.
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    # Inizializza storage
    storage = AnalyticsStorage()
    
    # Sezione Ultimi Siti Analizzati
    display_recent_analyses(storage)
    
    st.markdown("---")
    
    # Inizializza session state
    if 'analysis_complete' not in st.session_state:
        st.session_state.analysis_complete = False
    if 'seo_results' not in st.session_state:
        st.session_state.seo_results = None
    if 'analyzed_url' not in st.session_state:
        st.session_state.analyzed_url = ""

    # Input URL
    st.markdown('<div class="url-input">', unsafe_allow_html=True)
    col1, col2, col3 = st.columns([1, 3, 1])
    
    with col2:
        url = st.text_input(
            "Inserisci l'URL del sito web da analizzare:",
            placeholder="https://esempio.com",
            key="url_input",
            label_visibility="visible"
        )
        
        st.markdown('<div class="analyze-button">', unsafe_allow_html=True)
        analyze_button = st.button("Analizza Sito", type="primary", use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)
    
    st.markdown('</div>', unsafe_allow_html=True)

    # Analizza quando si preme il bottone o si preme Invio
    if analyze_button or (url and url != st.session_state.get('last_analyzed_url', '')):
        if not url:
            st.error("Inserisci un URL valido per iniziare l'analisi.")
            return
        
        # Salva l'URL per evitare analisi ripetute
        st.session_state.last_analyzed_url = url
        
        # Valida e pulisci URL usando utils
        is_valid, clean_url = validate_url(url)
        if not is_valid:
            st.error("L'URL inserito non è valido. Verifica che sia corretto.")
            return
        
        # Controlla SSL
        if clean_url.startswith('http://'):
            st.warning("Attenzione: Il sito non utilizza HTTPS. Si consiglia di implementare SSL per la sicurezza.")
        
        # Reset stato precedente
        st.session_state.analysis_complete = False
        st.session_state.seo_results = None
        st.session_state.analyzed_url = clean_url
        
        # Avvia analisi
        perform_seo_analysis(clean_url, storage)
    
    # Mostra risultati se disponibili
    if st.session_state.analysis_complete and st.session_state.seo_results:
        display_results(st.session_state.seo_results, st.session_state.analyzed_url)
    
    # Footer nero con copyright
    st.markdown("""
    <div class="footer-container">
        <p>© Copyright VOLGO Agenzia Pubblicitaria</p>
    </div>
    """, unsafe_allow_html=True)

def display_recent_analyses(storage: AnalyticsStorage):
    """Mostra la sezione degli ultimi siti analizzati"""
    recent_analyses = storage.get_recent_analyses(limit=8)
    
    if recent_analyses:
        st.markdown("### Ultimi Siti Analizzati")
        st.markdown("*Ultimi siti che sono stati analizzati con VOLGO SEO*")
        
        # Mostra in griglia 4x2
        cols = st.columns(4)
        for i, analysis in enumerate(recent_analyses):
            col_idx = i % 4
            with cols[col_idx]:
                score = analysis.get('score', 0)
                domain = analysis.get('domain', 'N/A')
                timestamp = analysis.get('timestamp', 'N/A')
                
                # Colore basato sul punteggio
                if score >= 80:
                    color = "#28a745"  # Verde
                elif score >= 60:
                    color = "#ffc107"  # Giallo
                else:
                    color = "#dc3545"  # Rosso
                
                st.markdown(f"""
                <div style="
                    background: white;
                    padding: 1rem;
                    border-radius: 8px;
                    border-left: 4px solid {color};
                    margin-bottom: 0.5rem;
                    box-shadow: 0 2px 4px rgba(0,0,0,0.1);
                ">
                    <div style="font-weight: bold; font-size: 0.9rem; margin-bottom: 0.3rem;">
                        {domain}
                    </div>
                    <div style="font-size: 1.5rem; font-weight: bold; color: {color};">
                        {score}/100
                    </div>
                    <div style="font-size: 0.7rem; color: #666;">
                        {timestamp.split(' ')[0]}
                    </div>
                </div>
                """, unsafe_allow_html=True)

def perform_seo_analysis(url, storage: AnalyticsStorage):
    """Esegue l'analisi SEO del sito web"""
    
    # Barra di progresso e messaggi di stato
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    try:
        # Inizializza analyzer
        analyzer = SEOAnalyzer()
        
        # Step 1: Connessione al sito
        status_text.text("Connessione al sito web...")
        progress_bar.progress(10)
        time.sleep(0.5)
        
        # Step 2: Ricerca sitemap
        status_text.text("Ricerca e analisi sitemap...")
        progress_bar.progress(25)
        sitemap_urls = analyzer.get_sitemap_urls(url)
        time.sleep(0.5)
        
        # Step 3: Scansione pagine
        status_text.text("Scansione delle pagine del sito...")
        progress_bar.progress(40)
        pages_data = analyzer.scan_website_pages(url, sitemap_urls)
        
        # Step 4: Analisi SEO
        status_text.text("Analisi approfondita dei fattori SEO...")
        progress_bar.progress(65)
        seo_analysis = analyzer.analyze_seo_factors(pages_data, url)
        
        # Step 5: Calcolo punteggio
        status_text.text("Calcolo punteggio SEO finale...")
        progress_bar.progress(85)
        final_score = analyzer.calculate_overall_score(seo_analysis)
        
        # Step 6: Completamento
        status_text.text("Analisi completata!")
        progress_bar.progress(100)
        time.sleep(0.5)
        
        # Salva risultati in session state
        robots_analysis = analyzer.analyze_robots_txt(url)
        page_urls_from_sitemaps = analyzer.extract_urls_from_sitemaps(sitemap_urls) if sitemap_urls else []
        
        results_data = {
            'score': final_score,
            'analysis': seo_analysis,
            'pages_count': len(pages_data),
            'sitemap_found': len(sitemap_urls) > 0,
            'sitemap_count': len(sitemap_urls),
            'sitemap_urls': sitemap_urls,
            'pages_in_sitemaps': len(page_urls_from_sitemaps),
            'robots_found': robots_analysis.get('found', False),
            'robots_analysis': robots_analysis,
            'pages_data': pages_data
        }
        
        # Salva in session state
        st.session_state.seo_results = results_data
        st.session_state.analysis_complete = True
        
        # Salva nell'archivio per trasparenza
        storage.save_analysis(url, final_score, results_data)
        
        # Pulisci interfaccia
        progress_bar.empty()
        status_text.empty()
        
        # Ricarica per mostrare risultati
        st.rerun()
        
    except Exception as e:
        progress_bar.empty()
        status_text.empty()
        st.error(f"Errore durante l'analisi: {str(e)}")
        st.error("Verifica che l'URL sia corretto e che il sito sia accessibile.")

def display_results(results, url):
    """Mostra i risultati dell'analisi SEO"""
    
    st.markdown("---")
    st.markdown('<div class="analysis-header">Risultati Analisi SEO</div>', unsafe_allow_html=True)
    
    # Punteggio principale
    score = results['score']
    score_color = get_score_color(score)
    
    st.markdown(f"""
    <div class="metric-card">
        <div class="score-display" style="color: {score_color};">{score}/100</div>
        <div class="score-description">{get_score_description(score)}</div>
    </div>
    """, unsafe_allow_html=True)
    
    # Informazioni sitemap dettagliate
    if results.get('sitemap_urls'):
        st.markdown(f"""
        <div class="info-section">
            <h4>Sitemap Trovate ({results.get('sitemap_count', 0)})</h4>
            <p>Sono state individuate {results.get('sitemap_count', 0)} sitemap XML nel sito:</p>
        </div>
        """, unsafe_allow_html=True)
        
        for i, sitemap_url in enumerate(results['sitemap_urls'], 1):
            st.markdown(f"""
            <div class="sitemap-item">
                <strong>Sitemap {i}:</strong> {sitemap_url}
            </div>
            """, unsafe_allow_html=True)
    
    # Statistiche generali
    st.markdown('<div class="summary-grid">', unsafe_allow_html=True)
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.markdown(f"""
        <div class="metric-card" style="text-align: center;">
            <h3 style="color: #1f77b4; margin: 0;">{results['pages_count']}</h3>
            <p style="margin: 0.5rem 0 0 0;">Pagine Analizzate</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        sitemap_status = "Trovata" if results['sitemap_found'] else "Non trovata"
        sitemap_color = "#51cf66" if results['sitemap_found'] else "#ff6b6b"
        st.markdown(f"""
        <div class="metric-card" style="text-align: center;">
            <h3 style="color: {sitemap_color}; margin: 0;">{sitemap_status}</h3>
            <p style="margin: 0.5rem 0 0 0;">Sitemap</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        st.markdown(f"""
        <div class="metric-card" style="text-align: center;">
            <h3 style="color: #1f77b4; margin: 0;">{results.get('pages_in_sitemaps', 0)}</h3>
            <p style="margin: 0.5rem 0 0 0;">Pagine nelle Sitemap</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col4:
        robots_status = "Presente" if results.get('robots_found') else "Assente"
        robots_color = "#51cf66" if results.get('robots_found') else "#ff6b6b"
        st.markdown(f"""
        <div class="metric-card" style="text-align: center;">
            <h3 style="color: {robots_color}; margin: 0;">{robots_status}</h3>
            <p style="margin: 0.5rem 0 0 0;">Robots.txt</p>
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown('</div>', unsafe_allow_html=True)
    
    # Analisi dettagliata con tab
    st.markdown('<div style="margin: 2rem 0;"><div class="analysis-header">Analisi Dettagliata</div></div>', unsafe_allow_html=True)
    
    analysis = results['analysis']
    
    tab1, tab2, tab3, tab4, tab5 = st.tabs(["Contenuti", "Tecnico", "Social & Mobile", "Performance", "Sitemap & Pagine"])
    
    with tab1:
        st.markdown('<div style="padding: 1rem 0;">', unsafe_allow_html=True)
        display_modern_metric("Titoli delle Pagine", analysis['titles'])
        display_modern_metric("Meta Description", analysis['meta_descriptions'])
        display_modern_metric("Struttura Headings", analysis['headings'])
        display_modern_metric("Lunghezza Contenuto", analysis['content_length'])
        display_modern_metric("Densità Parole Chiave", analysis['keyword_density'])
        st.markdown('</div>', unsafe_allow_html=True)
    
    with tab2:
        st.markdown('<div style="padding: 1rem 0;">', unsafe_allow_html=True)
        display_modern_metric("Attributi Alt Immagini", analysis['images_alt'])
        display_modern_metric("Tag Canonical", analysis.get('canonical_tags', {}))
        display_modern_metric("Favicon", analysis.get('favicon', {}))
        display_modern_metric("Robots.txt", analysis.get('robots_txt', {}))
        display_modern_metric("Codici di Stato HTTP", analysis['status_codes'])
        st.markdown('</div>', unsafe_allow_html=True)
    
    with tab3:
        st.markdown('<div style="padding: 1rem 0;">', unsafe_allow_html=True)
        display_modern_metric("Tag Open Graph", analysis.get('open_graph', {}))
        display_modern_metric("Twitter Cards", analysis.get('twitter_cards', {}))
        display_modern_metric("Mobile Friendly", analysis.get('mobile_friendly', {}))
        st.markdown('</div>', unsafe_allow_html=True)
    
    with tab4:
        st.markdown('<div style="padding: 1rem 0;">', unsafe_allow_html=True)
        display_modern_metric("Tempi di Risposta", analysis['response_times'])
        
        # Tabella dettagliata
        if analysis.get('page_details'):
            st.markdown('<div class="analysis-header" style="margin-top: 2rem;">Dettagli per Pagina</div>', unsafe_allow_html=True)
            df = pd.DataFrame(analysis['page_details'])
            st.dataframe(df, use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)
    
    with tab5:
        st.markdown('<div style="padding: 1rem 0;">', unsafe_allow_html=True)
        st.markdown('<h3 style="color: #1f77b4; margin-bottom: 1rem;">Sitemap e Pagine Trovate</h3>', unsafe_allow_html=True)
        
        # Mostra sitemap trovate
        if results.get('sitemap_urls'):
            st.markdown(f"""
            <div class="metric-card">
                <h4 style="color: #1f77b4; margin-bottom: 1rem;">Sitemap XML Trovate ({len(results['sitemap_urls'])})</h4>
            """, unsafe_allow_html=True)
            
            for i, sitemap_url in enumerate(results['sitemap_urls'], 1):
                sitemap_link = f'<a href="{sitemap_url}" target="_blank" style="color: #1f77b4; text-decoration: underline;">{sitemap_url}</a>'
                st.markdown(f"""
                <div style="background: rgba(243, 255, 243, 0.9); padding: 0.8rem; border-radius: 6px; margin: 0.4rem 0; border-left: 4px solid #28a745;">
                    <strong>Sitemap {i}:</strong> {sitemap_link}
                </div>
                """, unsafe_allow_html=True)
            
            st.markdown('</div>', unsafe_allow_html=True)
        
        # Mostra pagine trovate nelle sitemap
        if results.get('pages_in_sitemaps', 0) > 0:
            st.markdown(f"""
            <div class="metric-card" style="margin-top: 1rem;">
                <h4 style="color: #1f77b4; margin-bottom: 1rem;">Pagine dalle Sitemap ({results.get('pages_in_sitemaps', 0)})</h4>
            """, unsafe_allow_html=True)
            
            # Estrai e mostra le pagine effettive dalle sitemap
            from seo_analyzer import SEOAnalyzer
            analyzer = SEOAnalyzer()
            if results.get('sitemap_urls'):
                page_urls = analyzer.extract_urls_from_sitemaps(results['sitemap_urls'])
                
                if page_urls:
                    for i, page_url in enumerate(page_urls[:20], 1):  # Mostra prime 20
                        page_link = f'<a href="{page_url}" target="_blank" style="color: #1f77b4; text-decoration: underline;">{page_url}</a>'
                        st.markdown(f"""
                        <div style="background: rgba(248, 249, 250, 0.9); padding: 0.6rem; border-radius: 6px; margin: 0.2rem 0; border-left: 3px solid #6c757d;">
                            <strong>{i}.</strong> {page_link}
                        </div>
                        """, unsafe_allow_html=True)
                    
                    if len(page_urls) > 20:
                        st.markdown(f"<p style='text-align: center; color: #666; font-style: italic; margin-top: 1rem;'>... e altre {len(page_urls) - 20} pagine</p>", unsafe_allow_html=True)
                else:
                    st.markdown("""
                    <div style="background: rgba(255, 243, 243, 0.9); padding: 1rem; border-radius: 8px; text-align: center; color: #721c24;">
                        Nessuna pagina trovata nelle sitemap
                    </div>
                    """, unsafe_allow_html=True)
            
            st.markdown('</div>', unsafe_allow_html=True)
        
        if not results.get('sitemap_urls'):
            st.markdown("""
            <div class="metric-card">
                <div style="background: rgba(255, 243, 243, 0.9); padding: 1rem; border-radius: 8px; text-align: center; color: #721c24;">
                    <strong>Attenzione:</strong> Nessuna sitemap trovata nel sito. Controlla che esistano i file sitemap.xml, sitemap_pages.xml, sitemap_ecommerce.xml o sitemap_blog.xml nella root del dominio.
                </div>
            </div>
            """, unsafe_allow_html=True)
        
        st.markdown('</div>', unsafe_allow_html=True)
    
    # Pulsante download PDF
    st.markdown("---")
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        if st.button("Genera Report PDF", type="secondary", use_container_width=True):
            generate_pdf_report(results, url)

def display_metric_card(title, metric_data):
    """Mostra una card per una metrica specifica"""
    
    score = metric_data.get('score', 0)
    issues = metric_data.get('issues', [])
    recommendations = metric_data.get('recommendations', [])
    
    score_color = get_score_color(score)
    
    with st.expander(f"{title} - Punteggio: {score}/100", expanded=False):
        
        # Barra di progresso per il punteggio
        st.progress(score / 100)
        
        if issues:
            st.markdown("**Problemi Riscontrati:**")
            for issue in issues:
                st.markdown(f"- {issue}")
        
        if recommendations:
            st.markdown("**Raccomandazioni:**")
            for rec in recommendations:
                st.markdown(f"- {rec}")
        
        if not issues and not recommendations:
            st.success("Nessun problema riscontrato per questo aspetto!")

def display_modern_metric(title, metric_data):
    """Mostra una metrica con design moderno e card eleganti"""
    
    score = metric_data.get('score', 0)
    issues = metric_data.get('issues', [])
    recommendations = metric_data.get('recommendations', [])
    successes = metric_data.get('successes', [])
    
    score_color = get_score_color(score)
    
    # Card completa con tutti i contenuti all'interno
    st.markdown(f"""
    <div class="metric-card">
        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 1rem;">
            <h3 style="margin: 0; color: #1f77b4;">{title}</h3>
            <div style="font-size: 1.5rem; font-weight: bold; color: {score_color};">{score}/100</div>
        </div>
        <div style="background: #f0f0f0; border-radius: 8px; height: 8px; margin-bottom: 1.5rem;">
            <div style="background: {score_color}; height: 100%; width: {score}%; border-radius: 8px;"></div>
        </div>
    """, unsafe_allow_html=True)
    
    # Problemi rilevati - TUTTI all'interno della card
    if issues:
        st.markdown("""
        <div style="margin-bottom: 1rem;">
            <h4 style="color: #dc3545; margin-bottom: 0.8rem; font-size: 1.1rem;">Problemi Rilevati:</h4>
        """, unsafe_allow_html=True)
        
        for issue in issues:  # Mostra TUTTI i problemi
            # Rendi i link cliccabili
            issue_html = make_links_clickable(issue)
            st.markdown(f"""
            <div style="background: rgba(255, 243, 243, 0.9); padding: 0.8rem; border-radius: 6px; margin: 0.4rem 0; border-left: 4px solid #dc3545;">
                {issue_html}
            </div>
            """, unsafe_allow_html=True)
        
        st.markdown('</div>', unsafe_allow_html=True)
    
    # Aspetti positivi - TUTTI all'interno della card
    if successes:
        st.markdown("""
        <div style="margin-bottom: 1rem;">
            <h4 style="color: #28a745; margin-bottom: 0.8rem; font-size: 1.1rem;">Aspetti Positivi:</h4>
        """, unsafe_allow_html=True)
        
        for success in successes:  # Mostra TUTTI i successi
            success_html = make_links_clickable(success)
            st.markdown(f"""
            <div style="background: rgba(243, 255, 243, 0.9); padding: 0.8rem; border-radius: 6px; margin: 0.4rem 0; border-left: 4px solid #28a745;">
                {success_html}
            </div>
            """, unsafe_allow_html=True)
        
        st.markdown('</div>', unsafe_allow_html=True)
    
    # Raccomandazioni - TUTTE all'interno della card (solo testo)
    if recommendations:
        st.markdown("""
        <div style="margin-bottom: 1rem;">
            <h4 style="color: #6c757d; margin-bottom: 0.8rem; font-size: 1.1rem;">Raccomandazioni:</h4>
        """, unsafe_allow_html=True)
        
        for rec in recommendations:  # Mostra TUTTE le raccomandazioni
            st.markdown(f"""
            <div style="padding: 0.5rem 0; margin: 0.2rem 0; color: #6c757d;">
                • {rec}
            </div>
            """, unsafe_allow_html=True)
        
        st.markdown('</div>', unsafe_allow_html=True)
    
    # Messaggio se tutto è perfetto
    if not issues and not recommendations and not successes:
        st.markdown("""
        <div style="background: rgba(212, 237, 218, 0.9); padding: 1rem; border-radius: 8px; margin-bottom: 1rem; text-align: center; color: #155724;">
            <strong>Perfetto!</strong> Tutto appare ottimale per questa metrica.
        </div>
        """, unsafe_allow_html=True)
    
    # Chiudi la card
    st.markdown('</div>', unsafe_allow_html=True)

def make_links_clickable(text):
    """Rende i link nel testo cliccabili"""
    import re
    
    # Pattern per trovare URL
    url_pattern = r'https?://[^\s<>"]+'
    
    def replace_url(match):
        url = match.group(0)
        return f'<a href="{url}" target="_blank" style="color: #1f77b4; text-decoration: underline;">{url}</a>'
    
    return re.sub(url_pattern, replace_url, text)

def generate_pdf_report(results, url):
    """Genera e offre il download del report PDF"""
    
    try:
        with st.spinner("Generazione report PDF..."):
            pdf_generator = PDFGenerator()
            pdf_buffer = pdf_generator.generate_report(results, url)
            
            # Prepara il nome file
            domain = urlparse(url).netloc.replace('www.', '')
            filename = f"report_seo_{domain}_{time.strftime('%Y%m%d_%H%M%S')}.pdf"
            
            # Offri il download
            st.download_button(
                label="Scarica Report PDF",
                data=pdf_buffer.getvalue(),
                file_name=filename,
                mime="application/pdf",
                type="primary",
                use_container_width=True
            )
            
            st.success("Report PDF generato con successo!")
            
    except Exception as e:
        st.error(f"Errore nella generazione del PDF: {str(e)}")

def get_score_color(score):
    """Restituisce il colore basato sul punteggio"""
    if score >= 80:
        return "#28a745"  # Verde
    elif score >= 60:
        return "#ffc107"  # Giallo
    elif score >= 40:
        return "#fd7e14"  # Arancione
    else:
        return "#dc3545"  # Rosso

def get_score_description(score):
    """Restituisce una descrizione basata sul punteggio"""
    if score >= 80:
        return "Eccellente! Il tuo sito ha una SEO ottimale."
    elif score >= 60:
        return "Buono! Ci sono alcune aree da migliorare."
    elif score >= 40:
        return "Discreto. Sono necessari diversi miglioramenti."
    else:
        return "Critico. Il sito necessita di ottimizzazioni urgenti."

if __name__ == "__main__":
    main()
