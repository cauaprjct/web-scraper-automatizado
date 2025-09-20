"""
Módulo de Serviço de E-mail
============================

Este módulo gerencia o envio de e-mails do sistema,
incluindo templates, anexos e logs.

Classes disponíveis:
- EmailService: Serviço principal de e-mail
- EmailTemplates: Gerenciador de templates
"""

from .email_sender import EmailService
from .email_templates import EmailTemplates

__all__ = [
    "EmailService",
    "EmailTemplates"
]

__version__ = "1.0.0"
__author__ = "Seu Nome"
