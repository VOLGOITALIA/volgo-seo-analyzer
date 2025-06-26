from reportlab.lib import colors
from reportlab.lib.pagesizes import letter, A4, landscape
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, PageBreak
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.graphics.shapes import Drawing
from reportlab.graphics.charts.barcharts import VerticalBarChart
from reportlab.graphics.charts.piecharts import Pie
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
import io
from datetime import datetime
from urllib.parse import urlparse

class PDFGenerator:
    def __init__(self):
        self.styles = getSampleStyleSheet()
        self._setup_custom_styles()
    
    def _setup_custom_styles(self):
        """Configura stili personalizzati per il PDF"""
        
        # Stile per il titolo principale
        self.title_style = ParagraphStyle(
            'CustomTitle',
            parent=self.styles['Heading1'],
            fontSize=24,
            spaceAfter=30,
            alignment=TA_CENTER,
            textColor=colors.HexColor('#1f77b4')
        )
        
        # Stile per i sottotitoli
        self.subtitle_style = ParagraphStyle(
            'CustomSubtitle',
            parent=self.styles['Heading2'],
            fontSize=16,
            spaceAfter=20,
            textColor=colors.HexColor('#2c3e50')
        )
        
        # Stile per il testo normale
        self.normal_style = ParagraphStyle(
            'CustomNormal',
            parent=self.styles['Normal'],
            fontSize=10,
            spaceAfter=12
        )
        
        # Stile per il punteggio
        self.score_style = ParagraphStyle(
            'ScoreStyle',
            parent=self.styles['Normal'],
            fontSize=36,
            alignment=TA_CENTER,
            textColor=colors.HexColor('#28a745'),
            spaceAfter=20
        )
    
    def generate_report(self, results: dict, url: str) -> io.BytesIO:
        """Genera il report PDF completo"""
        
        buffer = io.BytesIO()
        
        # Crea documento in formato orizzontale
        doc = SimpleDocTemplate(
            buffer, 
            pagesize=landscape(A4),  # Formato orizzontale
            rightMargin=50,
            leftMargin=50,
            topMargin=80,  # Spazio per header
            bottomMargin=70  # Spazio per footer
        )
        
        # Contenuto del documento
        story = []
        
        # Pagina del titolo
        story.extend(self._create_title_page(url, results))
        story.append(PageBreak())
        
        # Riepilogo esecutivo
        story.extend(self._create_executive_summary(results))
        story.append(PageBreak())
        
        # Analisi dettagliata
        story.extend(self._create_detailed_analysis(results))
        story.append(PageBreak())
        
        # Tabella delle pagine
        story.extend(self._create_pages_table(results))
        story.append(PageBreak())
        
        # Raccomandazioni
        story.extend(self._create_recommendations(results))
        
        # Genera il PDF
        doc.build(story)
        buffer.seek(0)
        
        return buffer
    
    def _get_gradient_color(self, score: int):
        """Restituisce un colore gradiente moderno basato sul punteggio"""
        if score >= 80:
            # Verde moderno per punteggi alti
            return colors.HexColor('#28a745')
        elif score >= 60:
            # Giallo-verde per punteggi buoni
            return colors.HexColor('#ffc107')
        elif score >= 40:
            # Arancione per punteggi sufficienti
            return colors.HexColor('#fd7e14')
        else:
            # Rosso moderno per punteggi bassi
            return colors.HexColor('#dc3545')
    
    def _draw_header_footer(self, canvas, doc, url: str, results: dict):
        """Disegna header e footer su ogni pagina"""
        page_width, page_height = landscape(A4)
        
        # HEADER con sfondo nero
        canvas.setFillColor(colors.black)
        canvas.rect(0, page_height - 80, page_width, 80, fill=1)
        
        # Logo VOLGO SEO in alto a sinistra (testo bianco)
        canvas.setFillColor(colors.white)
        canvas.setFont("Helvetica-Bold", 16)
        canvas.drawString(50, page_height - 45, "VOLGO SEO")
        
        # Titolo al centro
        canvas.setFont("Helvetica", 12)
        canvas.drawCentredText(page_width/2, page_height - 45, "Analisi SEO Professionale")
        
        # Data in alto a destra
        today = datetime.now().strftime("%d/%m/%Y")
        canvas.drawRightString(page_width - 50, page_height - 45, today)
        
        # FOOTER con sfondo nero
        canvas.setFillColor(colors.black)
        canvas.rect(0, 0, page_width, 60, fill=1)
        
        # Copyright al centro
        canvas.setFillColor(colors.white)
        canvas.setFont("Helvetica", 10)
        canvas.drawCentredText(page_width/2, 30, "© Copyright VOLGO Agenzia Pubblicitaria")
        
        # Numero pagina
        canvas.drawRightString(page_width - 50, 30, f"Pagina {doc.page}")
    
    def _create_title_page(self, url: str, results: dict) -> list:
        """Crea la pagina del titolo"""
        
        story = []
        
        # Titolo principale
        story.append(Paragraph("REPORT ANALISI SEO", self.title_style))
        story.append(Spacer(1, 20))
        
        # URL analizzato
        domain = urlparse(url).netloc
        story.append(Paragraph(f"Sito web: <b>{domain}</b>", self.subtitle_style))
        story.append(Spacer(1, 10))
        
        # Data di generazione
        today = datetime.now().strftime("%d/%m/%Y alle %H:%M")
        story.append(Paragraph(f"Report generato il: {today}", self.normal_style))
        story.append(Spacer(1, 40))
        
        # Riquadro Risultati Analisi SEO con gradiente colorato
        score = results.get('score', 0)
        
        # Crea tabella per il riquadro colorato principale
        gradient_bg_color = self._get_gradient_color(score)
        
        # Header con info VOLGO SEO
        story.append(Paragraph("VOLGO SEO - Analisi SEO Professionale", self.subtitle_style))
        story.append(Spacer(1, 10))
        
        main_results_data = [
            ["RISULTATI ANALISI SEO", ""],
            [f"Punteggio Complessivo: {score}/100", self._get_score_description(score)],
            [f"Stato: {self._get_status_text(score)}", f"Data analisi: {datetime.now().strftime('%d/%m/%Y')}"]
        ]
        
        main_results_table = Table(main_results_data, colWidths=[4*inch, 4*inch])
        main_results_table.setStyle(TableStyle([
            # Sfondo gradiente basato sul punteggio
            ('BACKGROUND', (0, 0), (-1, -1), gradient_bg_color),
            ('TEXTCOLOR', (0, 0), (-1, -1), colors.white),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 16),
            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 1), (-1, -1), 12),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('GRID', (0, 0), (-1, -1), 2, colors.white),
            ('SPAN', (0, 0), (-1, 0)),  # Unisce le celle del titolo
        ]))
        
        story.append(main_results_table)
        story.append(Spacer(1, 30))
        
        return story
    
    def _create_executive_summary(self, results: dict) -> list:
        """Crea il riepilogo esecutivo"""
        
        story = []
        
        story.append(Paragraph("RIEPILOGO ESECUTIVO", self.title_style))
        story.append(Spacer(1, 20))
        
        # Statistiche generali
        stats_data = [
            ['Metrica', 'Valore'],
            ['Pagine Analizzate', str(results.get('pages_count', 0))],
            ['Sitemap Trovata', 'Sì' if results.get('sitemap_found') else 'No'],
            ['URL in Sitemap', str(results.get('sitemap_urls_count', 0))],
            ['Punteggio Complessivo', f"{results.get('score', 0)}/100"]
        ]
        
        stats_table = Table(stats_data, colWidths=[3*inch, 2*inch])
        stats_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1f77b4')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 12),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        
        story.append(stats_table)
        story.append(Spacer(1, 30))
        
        # Punteggi per categoria
        story.append(Paragraph("PUNTEGGI PER CATEGORIA", self.subtitle_style))
        story.append(Spacer(1, 15))
        
        analysis = results.get('analysis', {})
        categories_data = [
            ['Categoria', 'Punteggio', 'Stato']
        ]
        
        category_names = {
            'titles': 'Titoli Pagine',
            'meta_descriptions': 'Meta Description',
            'headings': 'Struttura Headings',
            'images_alt': 'Alt Text Immagini',
            'content_length': 'Lunghezza Contenuto',
            'response_times': 'Tempi di Risposta',
            'status_codes': 'Codici di Stato'
        }
        
        for key, name in category_names.items():
            if key in analysis:
                score = analysis[key].get('score', 0)
                status = self._get_status_text(score)
                categories_data.append([name, f"{score}/100", status])
        
        categories_table = Table(categories_data, colWidths=[2.5*inch, 1*inch, 1.5*inch])
        categories_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2c3e50')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.lightgrey),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        
        story.append(categories_table)
        
        return story
    
    def _create_detailed_analysis(self, results: dict) -> list:
        """Crea l'analisi dettagliata"""
        
        story = []
        
        story.append(Paragraph("ANALISI DETTAGLIATA", self.title_style))
        story.append(Spacer(1, 20))
        
        analysis = results.get('analysis', {})
        
        category_names = {
            'titles': 'Titoli delle Pagine',
            'meta_descriptions': 'Meta Description',
            'headings': 'Struttura Headings',
            'images_alt': 'Alt Text delle Immagini',
            'content_length': 'Lunghezza del Contenuto',
            'response_times': 'Tempi di Risposta',
            'status_codes': 'Codici di Stato HTTP'
        }
        
        for key, name in category_names.items():
            if key in analysis:
                category_data = analysis[key]
                story.extend(self._create_category_section(name, category_data))
                story.append(Spacer(1, 20))
        
        return story
    
    def _create_category_section(self, title: str, data: dict) -> list:
        """Crea una sezione per una categoria di analisi"""
        
        story = []
        
        # Titolo della sezione
        story.append(Paragraph(title, self.subtitle_style))
        
        # Punteggio
        score = data.get('score', 0)
        score_color = self._get_score_color(score)
        story.append(Paragraph(f"Punteggio: <font color='{score_color.hexval()}'><b>{score}/100</b></font>", self.normal_style))
        story.append(Spacer(1, 10))
        
        # Problemi riscontrati
        issues = data.get('issues', [])
        if issues:
            story.append(Paragraph("<b>Problemi Riscontrati:</b>", self.normal_style))
            for issue in issues[:5]:  # Limita a 5 problemi
                story.append(Paragraph(f"• {issue}", self.normal_style))
            story.append(Spacer(1, 10))
        
        # Raccomandazioni
        recommendations = data.get('recommendations', [])
        if recommendations:
            story.append(Paragraph("<b>Raccomandazioni:</b>", self.normal_style))
            for rec in recommendations:
                story.append(Paragraph(f"• {rec}", self.normal_style))
        
        return story
    
    def _create_pages_table(self, results: dict) -> list:
        """Crea la tabella delle pagine analizzate"""
        
        story = []
        
        story.append(Paragraph("DETTAGLI PAGINE ANALIZZATE", self.title_style))
        story.append(Spacer(1, 20))
        
        analysis = results.get('analysis', {})
        page_details = analysis.get('page_details', [])
        
        if not page_details:
            story.append(Paragraph("Nessun dettaglio delle pagine disponibile.", self.normal_style))
            return story
        
        # Prepara i dati per la tabella con larghezze ottimizzate per formato orizzontale
        table_data = [
            ['URL', 'Titolo', 'Meta Description', 'HTTP', 'Tempo']
        ]
        
        for page in page_details[:15]:  # Aumenta pagine per formato orizzontale
            url = page.get('URL', '')
            if len(url) > 50:
                url = url[:47] + '...'
            
            title = page.get('Titolo', 'N/A')
            if len(title) > 40:
                title = title[:37] + '...'
            
            meta_desc = page.get('Meta Description', 'N/A')
            if len(meta_desc) > 60:
                meta_desc = meta_desc[:57] + '...'
            
            table_data.append([
                url,
                title,
                meta_desc,
                str(page.get('Stato HTTP', 'N/A')),
                page.get('Tempo Risposta (s)', 'N/A')
            ])
        
        # Crea la tabella con larghezze ottimizzate per landscape
        table = Table(table_data, colWidths=[3.2*inch, 2.5*inch, 3*inch, 0.8*inch, 1*inch])
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#34495e')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),  # Allineamento a sinistra per leggibilità
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 10),  # Font più grande per landscape
            ('FONTSIZE', (0, 1), (-1, -1), 9),  # Font più grande per testo
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('TOPPADDING', (0, 1), (-1, -1), 8),
            ('BOTTOMPADDING', (0, 1), (-1, -1), 8),
            ('BACKGROUND', (0, 1), (-1, -1), colors.lightgrey),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),  # Allineamento in alto per testo lungo
            ('WORDWRAP', (0, 0), (-1, -1), True)  # Abilita word wrap
        ]))
        
        story.append(table)
        
        if len(page_details) > 10:
            story.append(Spacer(1, 10))
            story.append(Paragraph(f"Nota: Mostrate solo le prime 10 pagine di {len(page_details)} totali.", self.normal_style))
        
        return story
    
    def _create_recommendations(self, results: dict) -> list:
        """Crea la sezione delle raccomandazioni"""
        
        story = []
        
        story.append(Paragraph("RACCOMANDAZIONI PRIORITARIE", self.title_style))
        story.append(Spacer(1, 20))
        
        # Raccoglie tutte le raccomandazioni
        all_recommendations = []
        analysis = results.get('analysis', {})
        
        for category_data in analysis.values():
            if isinstance(category_data, dict):
                recommendations = category_data.get('recommendations', [])
                all_recommendations.extend(recommendations)
        
        # Rimuove duplicati mantenendo l'ordine
        unique_recommendations = list(dict.fromkeys(all_recommendations))
        
        if unique_recommendations:
            story.append(Paragraph("Per migliorare il tuo punteggio SEO, ti consigliamo di:", self.normal_style))
            story.append(Spacer(1, 10))
            
            for i, rec in enumerate(unique_recommendations[:10], 1):
                story.append(Paragraph(f"{i}. {rec}", self.normal_style))
                story.append(Spacer(1, 5))
        else:
            story.append(Paragraph("Il tuo sito ha una buona ottimizzazione SEO generale!", self.normal_style))
        
        story.append(Spacer(1, 30))
        
        # Footer
        story.append(Paragraph("---", self.normal_style))
        story.append(Paragraph("Report generato dall'Analizzatore SEO", 
                              ParagraphStyle('Footer', parent=self.normal_style, 
                                           fontSize=8, alignment=TA_CENTER, 
                                           textColor=colors.grey)))
        
        return story
    
    def _get_score_color(self, score: int):
        """Restituisce il colore basato sul punteggio"""
        if score >= 80:
            return colors.HexColor('#28a745')  # Verde
        elif score >= 60:
            return colors.HexColor('#ffc107')  # Giallo
        elif score >= 40:
            return colors.HexColor('#fd7e14')  # Arancione
        else:
            return colors.HexColor('#dc3545')  # Rosso
    
    def _get_score_description(self, score: int) -> str:
        """Restituisce una descrizione basata sul punteggio"""
        if score >= 80:
            return "Eccellente! Il tuo sito ha una SEO ottimale."
        elif score >= 60:
            return "Buono! Ci sono alcune aree da migliorare."
        elif score >= 40:
            return "Discreto. Sono necessari diversi miglioramenti."
        else:
            return "Critico. Il sito necessita di ottimizzazioni urgenti."
    
    def _get_status_text(self, score: int) -> str:
        """Restituisce il testo di stato basato sul punteggio"""
        if score >= 80:
            return "Ottimo"
        elif score >= 60:
            return "Buono"
        elif score >= 40:
            return "Discreto"
        else:
            return "Critico"
