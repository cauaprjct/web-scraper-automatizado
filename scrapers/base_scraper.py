"""
Base scraper class with common functionality for all scrapers.
"""

import asyncio
import time
from abc import ABC, abstractmethod
from typing import List, Dict, Optional, Any
from urllib.parse import urljoin, urlparse
import requests
from bs4 import BeautifulSoup
from fake_useragent import UserAgent
import logging

from utils.helpers import rate_limit, retry, clean_text, format_price
from utils.logger import setup_logger

logger = setup_logger(__name__)


class BaseScraper(ABC):
    """
    Classe base abstrata para todos os scrapers.
    
    Fornece funcionalidades comuns como:
    - Rate limiting
    - Tratamento de erros
    - Headers HTTP apropriados
    - Parsing básico de HTML
    - Validação de robots.txt
    """
    
    def __init__(self, settings):
        """
        Inicializa o scraper base.
        
        Args:
            settings: Configurações do sistema
        """
        self.settings = settings
        self.session = requests.Session()
        self.ua = UserAgent()
        
        # Configurar headers padrão
        self.session.headers.update({
            'User-Agent': self.ua.random,
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'pt-BR,pt;q=0.9,en;q=0.8',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
        })
        
        # Configurações específicas
        self.delay = getattr(settings, 'scraping_delay', 2.0)
        self.timeout = getattr(settings, 'request_timeout', 30)
        self.max_retries = getattr(settings, 'max_retries', 3)
        
        logger.info(f"Scraper inicializado: {self.__class__.__name__}")
    
    @abstractmethod
    def get_base_url(self) -> str:
        """
        Retorna a URL base do site.
        
        Returns:
            URL base do site
        """
        pass
    
    @abstractmethod
    def get_search_url(self) -> str:
        """
        Retorna a URL de busca do site.
        
        Returns:
            URL de busca do site
        """
        pass
    
    @abstractmethod
    async def search_products(self, search_term: str, **filters) -> List[Dict[str, Any]]:
        """
        Busca produtos no site.
        
        Args:
            search_term: Termo de busca
            **filters: Filtros adicionais (preço, categoria, etc.)
            
        Returns:
            Lista de produtos encontrados
        """
        pass
    
    @abstractmethod
    def _parse_product_element(self, element, base_url: str) -> Optional[Dict[str, Any]]:
        """
        Faz parsing de um elemento de produto.
        
        Args:
            element: Elemento HTML do produto
            base_url: URL base para URLs relativas
            
        Returns:
            Dicionário com dados do produto ou None se inválido
        """
        pass
    
    @rate_limit(calls=1, period=2)
    @retry(max_attempts=3, delay=1.0)
    async def _make_request(self, url: str, params: Optional[Dict] = None) -> Optional[requests.Response]:
        """
        Faz requisição HTTP com rate limiting e retry.
        
        Args:
            url: URL para requisição
            params: Parâmetros da requisição
            
        Returns:
            Response object ou None se falhou
        """
        try:
            logger.debug(f"Fazendo requisição para: {url}")
            
            response = self.session.get(
                url,
                params=params,
                timeout=self.timeout,
                allow_redirects=True
            )
            
            response.raise_for_status()
            
            logger.debug(f"Requisição bem-sucedida: {response.status_code}")
            return response
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Erro na requisição para {url}: {e}")
            raise
    
    def _parse_html(self, html_content: str) -> BeautifulSoup:
        """
        Faz parsing do HTML usando BeautifulSoup.
        
        Args:
            html_content: Conteúdo HTML
            
        Returns:
            Objeto BeautifulSoup
        """
        return BeautifulSoup(html_content, 'html.parser')
    
    def _extract_text(self, element, selector: str = None, default: str = "") -> str:
        """
        Extrai texto de elemento HTML.
        
        Args:
            element: Elemento HTML
            selector: Seletor CSS (opcional)
            default: Valor padrão se não encontrar
            
        Returns:
            Texto extraído e limpo
        """
        try:
            if selector:
                target = element.select_one(selector)
                if target:
                    return clean_text(target.get_text())
            else:
                return clean_text(element.get_text())
        except (AttributeError, TypeError):
            pass
        
        return default
    
    def _extract_price(self, element, selector: str = None, default: float = 0.0) -> float:
        """
        Extrai preço de elemento HTML.
        
        Args:
            element: Elemento HTML
            selector: Seletor CSS (opcional)
            default: Valor padrão se não encontrar
            
        Returns:
            Preço como float
        """
        try:
            if selector:
                target = element.select_one(selector)
                if target:
                    return format_price(target.get_text())
            else:
                return format_price(element.get_text())
        except (AttributeError, TypeError):
            pass
        
        return default
    
    def _extract_url(self, element, selector: str = None, attr: str = "href", base_url: str = "") -> str:
        """
        Extrai URL de elemento HTML.
        
        Args:
            element: Elemento HTML
            selector: Seletor CSS (opcional)
            attr: Atributo que contém a URL
            base_url: URL base para URLs relativas
            
        Returns:
            URL completa
        """
        try:
            if selector:
                target = element.select_one(selector)
                if target:
                    url = target.get(attr, "")
            else:
                url = element.get(attr, "")
            
            if url and base_url:
                return urljoin(base_url, url)
            
            return url or ""
            
        except (AttributeError, TypeError):
            return ""
    
    def _extract_image_url(self, element, selector: str = None, base_url: str = "") -> str:
        """
        Extrai URL de imagem de elemento HTML.
        
        Args:
            element: Elemento HTML
            selector: Seletor CSS (opcional)
            base_url: URL base para URLs relativas
            
        Returns:
            URL da imagem
        """
        # Tentar diferentes atributos de imagem
        attrs = ['src', 'data-src', 'data-lazy-src', 'data-original']
        
        try:
            if selector:
                img_element = element.select_one(selector)
            else:
                img_element = element
            
            if img_element:
                for attr in attrs:
                    url = img_element.get(attr)
                    if url:
                        if base_url:
                            return urljoin(base_url, url)
                        return url
        
        except (AttributeError, TypeError):
            pass
        
        return ""
    
    def _validate_product(self, product: Dict[str, Any]) -> bool:
        """
        Valida se um produto tem dados mínimos necessários.
        
        Args:
            product: Dicionário com dados do produto
            
        Returns:
            True se produto é válido
        """
        required_fields = ['title', 'price', 'url']
        
        for field in required_fields:
            if not product.get(field):
                return False
        
        # Validar preço
        try:
            price = float(product['price'])
            if price <= 0:
                return False
        except (ValueError, TypeError):
            return False
        
        # Validar URL
        url = product.get('url', '')
        if not url or not url.startswith(('http://', 'https://')):
            return False
        
        return True
    
    def _apply_filters(self, products: List[Dict[str, Any]], **filters) -> List[Dict[str, Any]]:
        """
        Aplica filtros aos produtos.
        
        Args:
            products: Lista de produtos
            **filters: Filtros a aplicar
            
        Returns:
            Lista de produtos filtrados
        """
        filtered = products.copy()
        
        # Filtro de preço mínimo
        min_price = filters.get('min_price')
        if min_price is not None:
            filtered = [p for p in filtered if p.get('price', 0) >= min_price]
        
        # Filtro de preço máximo
        max_price = filters.get('max_price')
        if max_price is not None:
            filtered = [p for p in filtered if p.get('price', 0) <= max_price]
        
        # Filtro de avaliação mínima
        min_rating = filters.get('min_rating')
        if min_rating is not None:
            filtered = [p for p in filtered if p.get('rating', 0) >= min_rating]
        
        # Filtro de frete grátis
        free_shipping = filters.get('free_shipping_only')
        if free_shipping:
            filtered = [p for p in filtered if p.get('free_shipping', False)]
        
        # Limitar número de resultados
        max_results = filters.get('max_results')
        if max_results is not None:
            filtered = filtered[:max_results]
        
        return filtered
    
    async def check_robots_txt(self) -> bool:
        """
        Verifica se o scraping é permitido pelo robots.txt.
        
        Returns:
            True se permitido
        """
        try:
            base_url = self.get_base_url()
            robots_url = urljoin(base_url, '/robots.txt')
            
            response = await self._make_request(robots_url)
            if response and response.status_code == 200:
                robots_content = response.text
                
                # Verificação básica - implementação mais robusta seria usar robotparser
                if 'Disallow: /' in robots_content and 'User-agent: *' in robots_content:
                    logger.warning(f"Robots.txt pode proibir scraping em {base_url}")
                    return False
            
            return True
            
        except Exception as e:
            logger.warning(f"Erro ao verificar robots.txt: {e}")
            return True  # Assumir permitido se não conseguir verificar
    
    def get_site_name(self) -> str:
        """
        Retorna nome do site baseado na URL.
        
        Returns:
            Nome do site
        """
        try:
            domain = urlparse(self.get_base_url()).netloc
            return domain.replace('www.', '')
        except Exception:
            return self.__class__.__name__.replace('Scraper', '')
    
    async def get_product_details(self, product_url: str) -> Optional[Dict[str, Any]]:
        """
        Obtém detalhes adicionais de um produto específico.
        
        Args:
            product_url: URL do produto
            
        Returns:
            Dicionário com detalhes do produto ou None
        """
        try:
            response = await self._make_request(product_url)
            if not response:
                return None
            
            soup = self._parse_html(response.text)
            
            # Implementação básica - cada scraper pode sobrescrever
            return {
                'detailed_description': self._extract_text(soup, 'meta[name="description"]'),
                'images': [img.get('src', '') for img in soup.find_all('img') if img.get('src')],
                'specifications': {}  # Cada site tem formato diferente
            }
            
        except Exception as e:
            logger.error(f"Erro ao obter detalhes do produto {product_url}: {e}")
            return None
