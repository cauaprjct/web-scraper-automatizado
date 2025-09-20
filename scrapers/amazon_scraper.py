"""
Scraper para Amazon
===================

Este módulo implementa o scraper específico para Amazon.
Extrai informações de produtos, preços, avaliações e disponibilidade.

Autor: Seu Nome
Data: 2025-09-20
"""

import asyncio
from typing import List, Dict, Optional, Any
from urllib.parse import urlencode
import re

from .base_scraper import BaseScraper
from utils.helpers import clean_text, format_price, extract_rating, extract_number
from utils.logger import setup_logger

logger = setup_logger(__name__)


class AmazonScraper(BaseScraper):
    """
    Scraper específico para Amazon Brasil.
    
    Extrai informações de produtos incluindo:
    - Título
    - Preço atual e original
    - Avaliações e número de reviews
    - Disponibilidade
    - Imagens
    - URLs
    """
    
    def __init__(self, settings: Any):
        """
        Inicializa o scraper da Amazon.
        
        Args:
            settings: Configurações do sistema
        """
        super().__init__(settings)
        
        self.base_url = getattr(settings, 'amazon_base_url', 'https://www.amazon.com.br')
        self.search_url = getattr(settings, 'amazon_search_url', 'https://www.amazon.com.br/s')
        
        # Configurar headers específicos da Amazon
        self._setup_amazon_headers()
        
        logger.info("Amazon scraper inicializado")
    
    def _setup_amazon_headers(self):
        """Configura headers específicos para Amazon."""
        self.session.headers.update({
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'pt-BR,pt;q=0.9,en-US;q=0.8,en;q=0.7',
            'Cache-Control': 'no-cache',
            'Pragma': 'no-cache',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'none',
            'Sec-Fetch-User': '?1',
        })
    
    def get_base_url(self) -> str:
        """Retorna URL base da Amazon."""
        return self.base_url
    
    def get_search_url(self) -> str:
        """Retorna URL de busca da Amazon."""
        return self.search_url
    
    async def search_products(self, search_term: str, **filters) -> List[Dict[str, Any]]:
        """
        Busca produtos na Amazon.
        
        Args:
            search_term: Termo de busca
            **filters: Filtros (min_price, max_price, max_results, etc.)
            
        Returns:
            Lista de produtos encontrados
        """
        logger.info(f"Buscando produtos na Amazon: '{search_term}'")
        
        products = []
        page = 1
        max_results = filters.get('max_results', 50)
        
        while len(products) < max_results:
            try:
                # Construir parâmetros de busca
                params = {
                    'k': search_term,
                    'page': page,
                    'ref': 'sr_pg_' + str(page)
                }
                
                # Adicionar filtros de preço se especificados
                if 'min_price' in filters or 'max_price' in filters:
                    price_range = self._build_price_filter(filters)
                    if price_range:
                        params.update(price_range)
                
                # Fazer requisição
                response = await self._make_request(self.search_url, params)
                if not response:
                    break
                
                # Parse da página
                soup = self._parse_html(response.text)
                page_products = self._extract_products_from_page(soup)
                
                if not page_products:
                    logger.info(f"Nenhum produto encontrado na página {page}")
                    break
                
                products.extend(page_products)
                logger.info(f"Página {page}: {len(page_products)} produtos encontrados")
                
                page += 1
                
                # Evitar muitas páginas
                if page > 10:
                    break
                    
            except Exception as e:
                logger.error(f"Erro na página {page}: {e}")
                break
        
        # Aplicar filtros
        filtered_products = self._apply_filters(products, **filters)
        
        logger.info(f"Amazon: {len(filtered_products)} produtos após filtros")
        return filtered_products
    
    def _build_price_filter(self, filters: Dict) -> Dict:
        """Constrói filtros de preço para Amazon."""
        price_params = {}
        
        min_price = filters.get('min_price')
        max_price = filters.get('max_price')
        
        if min_price is not None or max_price is not None:
            # Amazon usa formato: rh=p_36:min-max (em centavos)
            min_cents = int(min_price * 100) if min_price else 0
            max_cents = int(max_price * 100) if max_price else 999999999
            
            price_params['rh'] = f'p_36:{min_cents}-{max_cents}'
        
        return price_params
    
    def _extract_products_from_page(self, soup) -> List[Dict[str, Any]]:
        """Extrai produtos de uma página de resultados."""
        products = []
        
        # Seletores para diferentes layouts da Amazon
        selectors = [
            '[data-component-type="s-search-result"]',
            '.s-result-item',
            '[data-asin]'
        ]
        
        product_elements = []
        for selector in selectors:
            elements = soup.select(selector)
            if elements:
                product_elements = elements
                break
        
        logger.debug(f"Encontrados {len(product_elements)} elementos de produto")
        
        for element in product_elements:
            try:
                product = self._parse_product_element(element, self.base_url)
                if product and self._validate_product(product):
                    products.append(product)
            except Exception as e:
                logger.debug(f"Erro ao processar elemento: {e}")
                continue
        
        return products
    
    def _parse_product_element(self, element, base_url: str) -> Optional[Dict[str, Any]]:
        """Faz parsing de um elemento de produto da Amazon."""
        try:
            # Título
            title_selectors = [
                'h2 a span',
                '.s-size-mini .s-link-style a',
                'h2 .a-link-normal',
                '.s-title-instructions-style'
            ]
            title = ""
            for selector in title_selectors:
                title = self._extract_text(element, selector)
                if title:
                    break
            
            if not title:
                return None
            
            # URL
            url_selectors = [
                'h2 a',
                '.s-link-style',
                'a[href*="/dp/"]'
            ]
            url = ""
            for selector in url_selectors:
                url = self._extract_url(element, selector, base_url=base_url)
                if url:
                    break
            
            # Preço
            price_selectors = [
                '.a-price-whole',
                '.a-price .a-offscreen',
                '.a-price-range .a-offscreen',
                '.a-price-symbol + .a-price-whole'
            ]
            price = 0.0
            for selector in price_selectors:
                price = self._extract_price(element, selector)
                if price > 0:
                    break
            
            # Preço original (se em promoção)
            original_price_selectors = [
                '.a-text-price .a-offscreen',
                '.a-price.a-text-price .a-offscreen'
            ]
            original_price = 0.0
            for selector in original_price_selectors:
                original_price = self._extract_price(element, selector)
                if original_price > 0:
                    break
            
            # Avaliação
            rating_selectors = [
                '.a-icon-alt',
                '[aria-label*="estrela"]',
                '.a-star-mini .a-icon-alt'
            ]
            rating = 0.0
            for selector in rating_selectors:
                rating_text = self._extract_text(element, selector)
                if rating_text:
                    rating = extract_rating(rating_text)
                    if rating > 0:
                        break
            
            # Número de avaliações
            reviews_selectors = [
                '.a-size-base',
                'a[href*="#customerReviews"]',
                '.a-link-normal[href*="reviews"]'
            ]
            num_reviews = 0
            for selector in reviews_selectors:
                reviews_text = self._extract_text(element, selector)
                if reviews_text and any(char.isdigit() for char in reviews_text):
                    num_reviews = extract_number(reviews_text)
                    if num_reviews > 0:
                        break
            
            # Imagem
            image_selectors = [
                '.s-image',
                'img[data-src]',
                '.a-dynamic-image'
            ]
            image_url = ""
            for selector in image_selectors:
                image_url = self._extract_image_url(element, selector, base_url)
                if image_url:
                    break
            
            # Frete grátis
            free_shipping = bool(
                element.select('.a-color-base:contains("Frete GRÁTIS")') or
                element.select('[aria-label*="Frete grátis"]')
            )
            
            # Prime
            is_prime = bool(element.select('.a-icon-prime'))
            
            # Disponibilidade
            availability_text = self._extract_text(element, '.a-color-success, .a-color-price')
            in_stock = 'estoque' in availability_text.lower() or 'disponível' in availability_text.lower()
            
            # ASIN (identificador único da Amazon)
            asin = element.get('data-asin', '')
            
            product = {
                'title': title,
                'price': price,
                'original_price': original_price if original_price > price else None,
                'url': url,
                'image_url': image_url,
                'rating': rating,
                'num_reviews': num_reviews,
                'free_shipping': free_shipping,
                'is_prime': is_prime,
                'in_stock': in_stock,
                'site': 'Amazon',
                'asin': asin,
                'currency': 'BRL'
            }
            
            return product
            
        except Exception as e:
            logger.debug(f"Erro ao fazer parse do produto: {e}")
            return None
    
    async def get_product_details(self, product_url: str) -> Optional[Dict[str, Any]]:
        """
        Obtém detalhes adicionais de um produto específico da Amazon.
        
        Args:
            product_url: URL do produto
            
        Returns:
            Dicionário com detalhes do produto
        """
        try:
            response = await self._make_request(product_url)
            if not response:
                return None
            
            soup = self._parse_html(response.text)
            
            # Descrição detalhada
            description_selectors = [
                '#feature-bullets ul',
                '#productDescription',
                '.a-unordered-list.a-vertical'
            ]
            description = ""
            for selector in description_selectors:
                description = self._extract_text(soup, selector)
                if description:
                    break
            
            # Especificações técnicas
            specs = {}
            spec_table = soup.select('#productDetails_techSpec_section_1 tr')
            for row in spec_table:
                cells = row.select('td')
                if len(cells) >= 2:
                    key = clean_text(cells[0].get_text())
                    value = clean_text(cells[1].get_text())
                    if key and value:
                        specs[key] = value
            
            # Imagens adicionais
            images = []
            img_elements = soup.select('#altImages img, #imageBlock img')
            for img in img_elements:
                src = img.get('src') or img.get('data-src')
                if src and 'amazon' in src:
                    images.append(src)
            
            # Categoria
            category_elements = soup.select('#wayfinding-breadcrumbs_feature_div a')
            categories = [clean_text(cat.get_text()) for cat in category_elements]
            
            return {
                'detailed_description': description,
                'specifications': specs,
                'images': list(set(images)),  # Remover duplicatas
                'categories': categories,
                'brand': self._extract_text(soup, '#bylineInfo'),
                'model': specs.get('Número do modelo', '')
            }
            
        except Exception as e:
            logger.error(f"Erro ao obter detalhes do produto Amazon: {e}")
            return None
