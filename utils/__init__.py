"""
Módulo de Utilitários
=====================

Este módulo contém funções auxiliares e utilitários
usados em todo o sistema.

Módulos disponíveis:
- helpers: Funções auxiliares e decorators
- logger: Sistema de logging
"""

from .helpers import rate_limit, retry, clean_text, format_price
from .logger import setup_logger, log_email_sent

__all__ = [
    "rate_limit",
    "retry", 
    "clean_text",
    "format_price",
    "setup_logger",
    "log_email_sent"
]

__version__ = "1.0.0"
__author__ = "Seu Nome"
