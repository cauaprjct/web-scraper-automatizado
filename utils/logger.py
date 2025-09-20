"""
Sistema de Logging
==================

Este módulo configura o sistema de logging usando Loguru.
Fornece logging estruturado com rotação automática e diferentes níveis.

Autor: Seu Nome
Data: 2025-09-20
"""

import sys
from pathlib import Path
from typing import Optional
from loguru import logger
import os

# Configurar diretório de logs
LOG_DIR = Path("logs")
LOG_DIR.mkdir(exist_ok=True)

# Remover handler padrão do loguru
logger.remove()

# Configurar formato de log
LOG_FORMAT = (
    "<green>{time:YYYY-MM-DD HH:mm:ss}</green> | "
    "<level>{level: <8}</level> | "
    "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> | "
    "<level>{message}</level>"
)

# Handler para console (apenas INFO e acima)
logger.add(
    sys.stdout,
    format=LOG_FORMAT,
    level="INFO",
    colorize=True,
    backtrace=True,
    diagnose=True
)

# Handler para arquivo geral
logger.add(
    LOG_DIR / "scraper.log",
    format=LOG_FORMAT,
    level="DEBUG",
    rotation="10 MB",
    retention="30 days",
    compression="zip",
    backtrace=True,
    diagnose=True
)

# Handler para erros
logger.add(
    LOG_DIR / "errors.log",
    format=LOG_FORMAT,
    level="ERROR",
    rotation="5 MB",
    retention="60 days",
    compression="zip",
    backtrace=True,
    diagnose=True
)

# Handler para scraping específico
logger.add(
    LOG_DIR / "scraping.log",
    format=LOG_FORMAT,
    level="INFO",
    rotation="20 MB",
    retention="15 days",
    compression="zip",
    filter=lambda record: "scraping" in record["name"].lower() or "scraper" in record["name"].lower()
)


def setup_logger(name: str, level: str = "INFO") -> logger:
    """
    Configura logger para um módulo específico.
    
    Args:
        name: Nome do módulo
        level: Nível de log
        
    Returns:
        Logger configurado
    """
    # Criar logger com contexto
    module_logger = logger.bind(name=name)
    
    # Log de inicialização
    module_logger.info(f"Logger configurado: {name}")
    
    return module_logger


def log_scraping_session(session_id: str, site: str, search_term: str, status: str):
    """
    Log específico para sessões de scraping.
    
    Args:
        session_id: ID da sessão
        site: Site sendo scrapado
        search_term: Termo de busca
        status: Status da sessão
    """
    scraping_logger = logger.bind(name="scraping")
    scraping_logger.info(
        f"Sessão {session_id} | Site: {site} | Busca: '{search_term}' | Status: {status}"
    )


def log_product_found(site: str, title: str, price: float, url: str):
    """
    Log específico para produtos encontrados.
    
    Args:
        site: Site do produto
        title: Título do produto
        price: Preço do produto
        url: URL do produto
    """
    scraping_logger = logger.bind(name="scraping")
    scraping_logger.debug(
        f"Produto encontrado | Site: {site} | Título: {title[:50]}... | Preço: R$ {price:.2f}"
    )


def log_email_sent(recipients: list, subject: str, success: bool):
    """
    Log específico para envio de e-mails.
    
    Args:
        recipients: Lista de destinatários
        subject: Assunto do e-mail
        success: Se o envio foi bem-sucedido
    """
    email_logger = logger.bind(name="email")
    status = "SUCESSO" if success else "FALHA"
    email_logger.info(
        f"E-mail {status} | Destinatários: {len(recipients)} | Assunto: {subject}"
    )


def log_database_operation(operation: str, table: str, count: int, success: bool):
    """
    Log específico para operações de banco de dados.
    
    Args:
        operation: Tipo de operação (INSERT, UPDATE, DELETE, SELECT)
        table: Nome da tabela
        count: Número de registros afetados
        success: Se a operação foi bem-sucedida
    """
    db_logger = logger.bind(name="database")
    status = "SUCESSO" if success else "FALHA"
    db_logger.info(
        f"BD {status} | Operação: {operation} | Tabela: {table} | Registros: {count}"
    )


def log_scheduler_job(job_name: str, status: str, next_run: Optional[str] = None):
    """
    Log específico para jobs do agendador.
    
    Args:
        job_name: Nome do job
        status: Status do job (STARTED, COMPLETED, FAILED, SCHEDULED)
        next_run: Próxima execução (opcional)
    """
    scheduler_logger = logger.bind(name="scheduler")
    message = f"Job '{job_name}' | Status: {status}"
    if next_run:
        message += f" | Próxima execução: {next_run}"
    
    scheduler_logger.info(message)


def log_performance_metric(operation: str, duration: float, details: Optional[str] = None):
    """
    Log específico para métricas de performance.
    
    Args:
        operation: Nome da operação
        duration: Duração em segundos
        details: Detalhes adicionais (opcional)
    """
    perf_logger = logger.bind(name="performance")
    message = f"Operação: {operation} | Duração: {duration:.2f}s"
    if details:
        message += f" | Detalhes: {details}"
    
    perf_logger.info(message)


def log_error_with_context(error: Exception, context: dict):
    """
    Log de erro com contexto adicional.
    
    Args:
        error: Exceção
        context: Contexto adicional
    """
    error_logger = logger.bind(name="error")
    error_logger.error(
        f"Erro: {type(error).__name__}: {str(error)} | Contexto: {context}"
    )


def configure_log_level(level: str):
    """
    Configura nível de log globalmente.
    
    Args:
        level: Nível de log (DEBUG, INFO, WARNING, ERROR, CRITICAL)
    """
    # Remover handlers existentes
    logger.remove()
    
    # Reconfigurar com novo nível
    logger.add(
        sys.stdout,
        format=LOG_FORMAT,
        level=level,
        colorize=True,
        backtrace=True,
        diagnose=True
    )
    
    logger.add(
        LOG_DIR / "scraper.log",
        format=LOG_FORMAT,
        level="DEBUG",  # Arquivo sempre DEBUG
        rotation="10 MB",
        retention="30 days",
        compression="zip",
        backtrace=True,
        diagnose=True
    )
    
    logger.info(f"Nível de log configurado para: {level}")


def get_log_stats() -> dict:
    """
    Retorna estatísticas dos arquivos de log.
    
    Returns:
        Dicionário com estatísticas
    """
    stats = {}
    
    for log_file in LOG_DIR.glob("*.log"):
        if log_file.exists():
            stats[log_file.name] = {
                "size_mb": log_file.stat().st_size / (1024 * 1024),
                "modified": log_file.stat().st_mtime
            }
    
    return stats


def cleanup_old_logs(days: int = 30):
    """
    Remove logs antigos.
    
    Args:
        days: Número de dias para manter logs
    """
    import time
    
    cutoff_time = time.time() - (days * 24 * 60 * 60)
    removed_count = 0
    
    for log_file in LOG_DIR.glob("*.log*"):
        if log_file.stat().st_mtime < cutoff_time:
            try:
                log_file.unlink()
                removed_count += 1
            except OSError:
                pass
    
    if removed_count > 0:
        logger.info(f"Removidos {removed_count} arquivos de log antigos")


# Configurar limpeza automática na importação
try:
    cleanup_old_logs()
except Exception:
    pass  # Ignorar erros na limpeza inicial
