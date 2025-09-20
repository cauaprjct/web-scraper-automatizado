"""
Módulo de Banco de Dados
========================

Este módulo gerencia todas as operações de banco de dados,
incluindo modelos, conexões e operações CRUD.

Classes disponíveis:
- Product: Modelo de produto
- PriceHistory: Histórico de preços
- ScrapingSession: Sessões de scraping
- EmailLog: Log de e-mails enviados
- DatabaseManager: Gerenciador de banco de dados
"""

from .models import Product, PriceHistory, ScrapingSession, EmailLog, Base
from .database import DatabaseManager

__all__ = [
    "Product",
    "PriceHistory", 
    "ScrapingSession",
    "EmailLog",
    "Base",
    "DatabaseManager"
]

__version__ = "1.0.0"
__author__ = "Seu Nome"
