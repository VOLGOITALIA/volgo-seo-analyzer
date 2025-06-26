# VOLGO SEO - Setup Streamlit Cloud

## Passo 1: Prepara i file per GitHub

### File necessari (già pronti):
- `app.py` - Applicazione principale
- `seo_analyzer.py` - Motore SEO
- `pdf_generator.py` - Generatore PDF
- `analytics_storage.py` - Storage analisi
- `utils.py` - Utilities
- `requirements.txt` - Dipendenze (da creare)

### File da aggiungere:
- `volgoseo.png` - Il tuo logo

## Passo 2: Crea repository GitHub

1. Vai su https://github.com
2. Clicca "New repository"
3. Nome: `volgo-seo-analyzer`
4. Descrizione: `Analisi SEO gratuita per siti web`
5. Pubblico (per Streamlit Cloud gratuito)
6. Clicca "Create repository"

## Passo 3: Carica i file

Trascina tutti i file nel repository GitHub:
- Tutti i file Python
- `requirements.txt` 
- `volgoseo.png` (il tuo logo)

## Passo 4: Deploy su Streamlit Cloud

1. Vai su https://share.streamlit.io/
2. Clicca "New app"
3. Connetti il tuo account GitHub
4. Seleziona il repository `volgo-seo-analyzer`
5. Main file path: `app.py`
6. Clicca "Deploy!"

## Passo 5: Configura dominio personalizzato

Dopo il deploy, avrai una URL tipo:
`https://volgo-seo-analyzer-xyz.streamlit.app`

Per usare `seo.n00n.it`:

### Opzione A: Redirect (più semplice)
Nel cPanel di Netsons:
1. Crea un redirect 301
2. Da: `seo.n00n.it`
3. A: `https://volgo-seo-analyzer-xyz.streamlit.app`

### Opzione B: Frame (mantiene l'URL)
Crea un file `index.html` in `seo.n00n.it`:
```html
<!DOCTYPE html>
<html>
<head>
    <title>VOLGO SEO - Analisi SEO Gratuita</title>
    <style>
        body, html { margin:0; padding:0; height:100%; overflow:hidden; }
        iframe { width:100%; height:100%; border:none; }
    </style>
</head>
<body>
    <iframe src="https://volgo-seo-analyzer-xyz.streamlit.app"></iframe>
</body>
</html>
```

## Vantaggi di Streamlit Cloud:
- Completamente gratuito
- SSL automatico
- Aggiornamenti automatici da GitHub
- Zero configurazione server
- Uptime garantito

## Tempo totale: ~15 minuti