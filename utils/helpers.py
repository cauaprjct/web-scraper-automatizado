"""
Funções Utilitárias
==================

Este módulo contém funções auxiliares usadas em todo o sistema.
Inclui decorators, formatação de dados e outras utilidades.

Autor: Seu Nome
Data: 2025-09-20
"""

import asyncio
import functools
import re
import time
from typing import Any, Callable, Optional
import logging

logger = logging.getLogger(__name__)


def rate_limit(calls: int = 1, period: int = 1):
    """
    Decorator para implementar rate limiting.
    
    Args:
        calls: Número de chamadas permitidas
        period: Período em segundos
    """
    def decorator(func: Callable) -> Callable:
        last_called = [0.0]
        
        @functools.wraps(func)
        async def async_wrapper(*args, **kwargs):
            elapsed = time.time() - last_called[0]
            left_to_wait = period - elapsed
            
            if left_to_wait > 0:
                await asyncio.sleep(left_to_wait)
            
            ret = await func(*args, **kwargs)
            last_called[0] = time.time()
            return ret
        
        @functools.wraps(func)
        def sync_wrapper(*args, **kwargs):
            elapsed = time.time() - last_called[0]
            left_to_wait = period - elapsed
            
            if left_to_wait > 0:
                time.sleep(left_to_wait)
            
            ret = func(*args, **kwargs)
            last_called[0] = time.time()
            return ret
        
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper
    
    return decorator


def retry(max_attempts: int = 3, delay: float = 1.0, backoff: float = 2.0):
    """
    Decorator para implementar retry automático.
    
    Args:
        max_attempts: Número máximo de tentativas
        delay: Delay inicial entre tentativas
        backoff: Multiplicador do delay a cada tentativa
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        async def async_wrapper(*args, **kwargs):
            last_exception = None
            current_delay = delay
            
            for attempt in range(max_attempts):
                try:
                    return await func(*args, **kwargs)
                except Exception as e:
                    last_exception = e
                    logger.warning(
                        f"Tentativa {attempt + 1}/{max_attempts} falhou: {e}"
                    )
                    
                    if attempt < max_attempts - 1:
                        await asyncio.sleep(current_delay)
                        current_delay *= backoff
            
            logger.error(f"Todas as {max_attempts} tentativas falharam")
            raise last_exception
        
        @functools.wraps(func)
        def sync_wrapper(*args, **kwargs):
            last_exception = None
            current_delay = delay
            
            for attempt in range(max_attempts):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    last_exception = e
                    logger.warning(
                        f"Tentativa {attempt + 1}/{max_attempts} falhou: {e}"
                    )
                    
                    if attempt < max_attempts - 1:
                        time.sleep(current_delay)
                        current_delay *= backoff
            
            logger.error(f"Todas as {max_attempts} tentativas falharam")
            raise last_exception
        
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper
    
    return decorator


def clean_text(text: str) -> str:
    """
    Limpa e normaliza texto.
    
    Args:
        text: Texto para limpar
        
    Returns:
        Texto limpo
    """
    if not text:
        return ""
    
    # Remover espaços extras
    text = re.sub(r'\s+', ' ', text.strip())
    
    # Remover caracteres de controle
    text = re.sub(r'[\x00-\x1f\x7f-\x9f]', '', text)
    
    # Normalizar aspas
    text = text.replace('“', '"').replace('”', '"')
    text = text.replace('‘', "'").replace('’', "'")
    
    return text


def format_price(price_text: str) -> float:
    """
    Extrai e formata preço de texto.
    
    Args:
        price_text: Texto contendo preço
        
    Returns:
        Preço como float
    """
    if not price_text:
        return 0.0
    
    # Remover caracteres não numéricos exceto vírgula e ponto
    price_clean = re.sub(r'[^\d,.]', '', str(price_text))
    
    if not price_clean:
        return 0.0
    
    try:
        # Tratar formato brasileiro (1.234,56)
        if ',' in price_clean and '.' in price_clean:
            # Se tem ambos, assumir formato brasileiro
            if price_clean.rindex(',') > price_clean.rindex('.'):
                price_clean = price_clean.replace('.', '').replace(',', '.')
        elif ',' in price_clean:
            # Se só tem vírgula, pode ser decimal brasileiro
            parts = price_clean.split(',')
            if len(parts) == 2 and len(parts[1]) <= 2:
                price_clean = price_clean.replace(',', '.')
        
        return float(price_clean)
    except (ValueError, AttributeError):
        return 0.0


def extract_rating(rating_text: str) -> float:
    """
    Extrai avaliação numérica de texto.
    
    Args:
        rating_text: Texto contendo avaliação
        
    Returns:
        Avaliação como float (0-5)
    """
    if not rating_text:
        return 0.0
    
    # Procurar por números com ponto ou vírgula
    rating_match = re.search(r'(\d+[.,]?\d*)', str(rating_text))
    
    if rating_match:
        try:
            rating = float(rating_match.group(1).replace(',', '.'))
            # Normalizar para escala 0-5
            if rating > 5:
                rating = rating / 2  # Assumir escala 0-10
            return min(5.0, max(0.0, rating))
        except ValueError:
            pass
    
    # Contar estrelas
    stars = rating_text.count('★') + rating_text.count('⭐')
    if stars > 0:
        return float(min(5, stars))
    
    return 0.0


def extract_number(text: str) -> int:
    """
    Extrai número inteiro de texto.
    
    Args:
        text: Texto contendo número
        
    Returns:
        Número como int
    """
    if not text:
        return 0
    
    # Procurar por números
    number_match = re.search(r'(\d+)', str(text))
    
    if number_match:
        try:
            return int(number_match.group(1))
        except ValueError:
            pass
    
    return 0


def normalize_url(url: str, base_url: str = "") -> str:
    """
    Normaliza URL relativa para absoluta.
    
    Args:
        url: URL para normalizar
        base_url: URL base para URLs relativas
        
    Returns:
        URL normalizada
    """
    if not url:
        return ""
    
    from urllib.parse import urljoin, urlparse
    
    # Se já é URL absoluta
    if urlparse(url).netloc:
        return url
    
    # Se é URL relativa e temos base_url
    if base_url:
        return urljoin(base_url, url)
    
    return url


def truncate_text(text: str, max_length: int = 100, suffix: str = "...") -> str:
    """
    Trunca texto se exceder tamanho máximo.
    
    Args:
        text: Texto para truncar
        max_length: Tamanho máximo
        suffix: Sufixo para texto truncado
        
    Returns:
        Texto truncado
    """
    if not text or len(text) <= max_length:
        return text
    
    return text[:max_length - len(suffix)] + suffix


def safe_get(dictionary: dict, key: str, default: Any = None) -> Any:
    """
    Obtém valor de dicionário de forma segura.
    
    Args:
        dictionary: Dicionário
        key: Chave
        default: Valor padrão
        
    Returns:
        Valor ou padrão
    """
    try:
        return dictionary.get(key, default)
    except (AttributeError, TypeError):
        return default


def format_currency(value: float, currency: str = "R$") -> str:
    """
    Formata valor como moeda.
    
    Args:
        value: Valor numérico
        currency: Símbolo da moeda
        
    Returns:
        Valor formatado
    """
    try:
        return f"{currency} {value:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')
    except (ValueError, TypeError):
        return f"{currency} 0,00"


def validate_email(email: str) -> bool:
    """
    Valida formato de e-mail.
    
    Args:
        email: E-mail para validar
        
    Returns:
        True se válido
    """
    if not email:
        return False
    
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return bool(re.match(pattern, email))


def get_domain(url: str) -> str:
    """
    Extrai domínio de URL.
    
    Args:
        url: URL
        
    Returns:
        Domínio
    """
    try:
        from urllib.parse import urlparse
        return urlparse(url).netloc
    except Exception:
        return ""


def is_valid_url(url: str) -> bool:
    """
    Valida se URL é válida.
    
    Args:
        url: URL para validar
        
    Returns:
        True se válida
    """
    try:
        from urllib.parse import urlparse
        result = urlparse(url)
        return all([result.scheme, result.netloc])
    except Exception:
        return False


def calculate_percentage_change(old_value: float, new_value: float) -> float:
    """
    Calcula mudança percentual entre dois valores.
    
    Args:
        old_value: Valor antigo
        new_value: Valor novo
        
    Returns:
        Mudança percentual
    """
    if old_value == 0:
        return 0.0
    
    try:
        return ((new_value - old_value) / old_value) * 100
    except (ValueError, TypeError, ZeroDivisionError):
        return 0.0
