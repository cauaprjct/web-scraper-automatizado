"""
Configurações do Sistema
========================

Este módulo gerencia todas as configurações do sistema usando Pydantic.
Carrega configurações de variáveis de ambiente e arquivos .env.

Autor: Seu Nome
Data: 2025-09-20
"""

import os
from typing import List, Optional
from pydantic import Field, field_validator
from pydantic_settings import BaseSettings
from pathlib import Path


class Settings(BaseSettings):
    """
    Configurações principais do sistema.
    
    Utiliza Pydantic para validação e carregamento automático
    de variáveis de ambiente.
    """
    
    # Informações da aplicação
    app_name: str = "Web Scraper Automatizado"
    app_version: str = "1.0.0"
    debug: bool = False
    
    # Configurações de banco de dados
    database_url: str = "sqlite:///data/scraper_data.db"
    
    # Configurações de e-mail
    email_host: str = "smtp.gmail.com"
    email_port: int = 587
    email_use_tls: bool = True
    email_user: str = ""
    email_password: str = ""
    email_from_name: str = "Web Scraper Bot"
    email_subject_prefix: str = "[SCRAPER]"
    email_recipients: List[str] = []
    email_only_on_changes: bool = True
    send_daily_summary: bool = True
    max_products_per_email: int = 50
    
    # Configurações de scraping
    scraping_delay: float = 2.0
    max_retries: int = 3
    request_timeout: int = 30
    user_agent: str = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    
    # Configurações de agendamento
    daily_execution_time: str = "09:00"
    timezone: str = "America/Sao_Paulo"
    enable_scheduling: bool = False
    run_on_weekends: bool = False
    
    # Configurações de logging
    log_level: str = "INFO"
    log_dir: str = "logs"
    log_retention_days: int = 30
    log_max_size: str = "10MB"
    log_backup_count: int = 5
    
    # Configurações do dashboard
    streamlit_port: int = 8501
    streamlit_host: str = "localhost"
    
    # Configurações de sites específicos
    amazon_base_url: str = "https://www.amazon.com.br"
    amazon_search_url: str = "https://www.amazon.com.br/s"
    
    ebay_base_url: str = "https://www.ebay.com"
    ebay_search_url: str = "https://www.ebay.com/sch/i.html"
    
    mercadolivre_base_url: str = "https://www.mercadolivre.com.br"
    mercadolivre_search_url: str = "https://lista.mercadolivre.com.br"
    
    # Configurações de filtros
    default_max_price: float = 1000.0
    default_min_price: float = 0.0
    min_rating: float = 4.0
    free_shipping_only: bool = False
    
    # Configurações de segurança
    secret_key: str = "your-secret-key-here"
    
    # Configurações de proxy
    use_proxy: bool = False
    proxy_list: List[str] = []
    rotate_proxies: bool = False
    
    # Configurações de performance
    max_threads: int = 5
    cache_duration: int = 60
    use_cache: bool = True
    
    @field_validator('email_recipients', mode='before')
    @classmethod
    def parse_email_recipients(cls, v):
        """Parse lista de e-mails de string separada por vírgula."""
        if v is None or v == "":
            return []
        if isinstance(v, str):
            return [email.strip() for email in v.split(',') if email.strip()]
        return v
    
    @field_validator('proxy_list', mode='before')
    @classmethod
    def parse_proxy_list(cls, v):
        """Parse lista de proxies de string separada por vírgula."""
        if v is None or v == "":
            return []
        if isinstance(v, str):
            return [proxy.strip() for proxy in v.split(',') if proxy.strip()]
        return v
    
    @field_validator('database_url')
    @classmethod
    def validate_database_url(cls, v):
        """Valida e ajusta URL do banco de dados."""
        if v.startswith('sqlite:///'):
            # Garantir que o diretório existe
            db_path = v.replace('sqlite:///', '')
            db_dir = os.path.dirname(db_path)
            if db_dir:
                os.makedirs(db_dir, exist_ok=True)
        return v
    
    @field_validator('log_dir')
    @classmethod
    def create_log_dir(cls, v):
        """Cria diretório de logs se não existir."""
        os.makedirs(v, exist_ok=True)
        return v
    
    @field_validator('daily_execution_time')
    @classmethod
    def validate_time_format(cls, v):
        """Valida formato de hora (HH:MM)."""
        import re
        if not re.match(r'^([01]?[0-9]|2[0-3]):[0-5][0-9]$', v):
            raise ValueError('Formato de hora deve ser HH:MM')
        return v
    
    @field_validator('log_level')
    @classmethod
    def validate_log_level(cls, v):
        """Valida nível de log."""
        valid_levels = ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']
        if v.upper() not in valid_levels:
            raise ValueError(f'Nível de log deve ser um de: {valid_levels}')
        return v.upper()
    
    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "case_sensitive": False,
        "extra": "allow"
    }
    
    def get_site_config(self, site: str) -> dict:
        """Retorna configurações específicas de um site."""
        configs = {
            "amazon": {
                "base_url": self.amazon_base_url,
                "search_url": self.amazon_search_url,
                "delay": self.scraping_delay,
                "timeout": self.request_timeout
            },
            "ebay": {
                "base_url": self.ebay_base_url,
                "search_url": self.ebay_search_url,
                "delay": self.scraping_delay,
                "timeout": self.request_timeout
            },
            "mercadolivre": {
                "base_url": self.mercadolivre_base_url,
                "search_url": self.mercadolivre_search_url,
                "delay": self.scraping_delay,
                "timeout": self.request_timeout
            }
        }
        
        return configs.get(site, {})
    
    def validate_required_settings(self) -> List[str]:
        """Valida se as configurações obrigatórias estão presentes."""
        missing = []
        
        # Verificar configurações de e-mail se envio estiver habilitado
        if self.email_recipients:
            if not self.email_user:
                missing.append('EMAIL_USER')
            if not self.email_password:
                missing.append('EMAIL_PASSWORD')
        
        return missing


# Para criar uma instância das configurações, use:
# settings = Settings()
#
# Para validar configurações:
# missing_settings = settings.validate_required_settings()
# if missing_settings:
#     print(f"Configurações faltando: {', '.join(missing_settings)}")
