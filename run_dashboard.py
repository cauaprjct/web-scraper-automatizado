#!/usr/bin/env python3
"""
Script para executar o dashboard Streamlit
==========================================

Script de conveniência para iniciar o dashboard web
do Web Scraper Automatizado.

Autor: Seu Nome
Data: 2025-09-20
"""

import subprocess
import sys
from pathlib import Path

def main():
    """
    Executa o dashboard Streamlit.
    """
    print("🕷️ Web Scraper Automatizado - Dashboard")
    print("="*50)
    print("Iniciando dashboard web...")
    print("O dashboard estará disponível em: http://localhost:8501")
    print("Pressione Ctrl+C para parar")
    print("="*50)
    
    # Caminho para o arquivo do dashboard
    dashboard_path = Path(__file__).parent / "dashboard" / "app.py"
    
    try:
        # Executar Streamlit
        subprocess.run([
            sys.executable, "-m", "streamlit", "run", 
            str(dashboard_path),
            "--server.port=8501",
            "--server.address=localhost",
            "--browser.gatherUsageStats=false"
        ])
    
    except KeyboardInterrupt:
        print("\n👋 Dashboard encerrado pelo usuário")
    
    except Exception as e:
        print(f"\n❌ Erro ao executar dashboard: {e}")
        print("\nVerifique se o Streamlit está instalado:")
        print("pip install streamlit")
        sys.exit(1)

if __name__ == "__main__":
    main()
