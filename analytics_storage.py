import json
import os
from datetime import datetime
from typing import List, Dict
from urllib.parse import urlparse
import streamlit as st

class AnalyticsStorage:
    def __init__(self, storage_file: str = "siti_analizzati.json"):
        self.storage_file = storage_file
        self.max_entries = 50  # Mantieni solo gli ultimi 50 siti
    
    def save_analysis(self, url: str, score: int, analysis_data: Dict = None):
        """Salva i risultati di un'analisi"""
        try:
            # Carica dati esistenti
            data = self.load_data()
            
            # Prepara nuovo entry
            domain = urlparse(url).netloc.replace('www.', '')
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            
            new_entry = {
                "url": url,
                "domain": domain,
                "score": score,
                "timestamp": timestamp,
                "analysis_summary": self._create_summary(analysis_data) if analysis_data else {}
            }
            
            # Rimuovi entry duplicati dello stesso dominio
            data = [entry for entry in data if entry.get('domain') != domain]
            
            # Aggiungi il nuovo entry all'inizio
            data.insert(0, new_entry)
            
            # Mantieni solo gli ultimi N entries
            data = data[:self.max_entries]
            
            # Salva i dati aggiornati
            with open(self.storage_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
                
            return True
            
        except Exception as e:
            st.error(f"Errore nel salvare l'analisi: {str(e)}")
            return False
    
    def load_data(self) -> List[Dict]:
        """Carica i dati salvati"""
        try:
            if os.path.exists(self.storage_file):
                with open(self.storage_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            return []
        except Exception:
            return []
    
    def get_recent_analyses(self, limit: int = 10) -> List[Dict]:
        """Ottieni le analisi più recenti"""
        data = self.load_data()
        return data[:limit]
    
    def get_stats(self) -> Dict:
        """Ottieni statistiche generali"""
        data = self.load_data()
        
        if not data:
            return {
                "total_sites": 0,
                "average_score": 0,
                "best_score": 0,
                "worst_score": 0,
                "today_analyses": 0
            }
        
        scores = [entry.get('score', 0) for entry in data if entry.get('score')]
        today = datetime.now().strftime("%Y-%m-%d")
        today_count = len([entry for entry in data if entry.get('timestamp', '').startswith(today)])
        
        return {
            "total_sites": len(data),
            "average_score": round(sum(scores) / len(scores)) if scores else 0,
            "best_score": max(scores) if scores else 0,
            "worst_score": min(scores) if scores else 0,
            "today_analyses": today_count
        }
    
    def _create_summary(self, analysis_data: Dict) -> Dict:
        """Crea un riassunto dell'analisi per lo storage"""
        if not analysis_data:
            return {}
        
        analysis = analysis_data.get('analysis', {})
        
        return {
            "total_pages": len(analysis_data.get('pages_data', [])),
            "titles_score": analysis.get('titles', {}).get('score', 0),
            "headings_score": analysis.get('headings', {}).get('score', 0),
            "images_score": analysis.get('images_alt', {}).get('score', 0),
            "meta_descriptions_score": analysis.get('meta_descriptions', {}).get('score', 0)
        }
    
    def clear_data(self):
        """Cancella tutti i dati (per admin/debug)"""
        try:
            if os.path.exists(self.storage_file):
                os.remove(self.storage_file)
            return True
        except Exception:
            return False