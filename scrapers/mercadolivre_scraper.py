"""
Scraper para Mercado Livre
==========================

Este módulo implementa o scraper específico para Mercado Livre Brasil.
Extrai informações de produtos, preços, avaliações e disponibilidade.

Autor: Seu Nome
Data: 2025-09-20
"""

import asyncio
from typing import List, Dict, Optional, Any
from urllib.parse import urlencode

from .base_scraper import BaseScraper
from utils.helpers import clean_text, format_price, extract_rating, extract_number
from utils.logger import setup_logger

logger = setup_logger(__name__)


class MercadoLivreScraper(BaseScraper):
    """
    Scraper específico para Mercado Livre Brasil.
    
    Extrai informações de produtos incluindo:
    - Título
    - Preço atual e original
    - Avaliações
    - Frete grátis
    - Vendedor
    """
    
    def __init__(self, settings: Any):
        """
        Inicializa o scraper do Mercado Livre.
        
        Args:
            settings: Configurações do sistema
        """
        super().__init__(settings)
        
        self.base_url = getattr(settings, 'mercadolivre_base_url', 'https://www.mercadolivre.com.br')
        self.search_url = getattr(settings, 'mercadolivre_search_url', 'https://lista.mercadolivre.com.br')
        
        # Configurar headers específicos do ML
        self._setup_ml_headers()
        
        logger.info("MercadoLivre scraper inicializado")
    
    def _setup_ml_headers(self):
        """Configura headers específicos para Mercado Livre."""
        self.session.headers.update({
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'pt-BR,pt;q=0.9,en;q=0.8',
            'Cache-Control': 'no-cache',
            'Pragma': 'no-cache',
        })
    
    def get_base_url(self) -> str:
        """Retorna URL base do Mercado Livre."""
        return self.base_url
    
    def get_search_url(self) -> str:
        """Retorna URL de busca do Mercado Livre."""
        return self.search_url
    
    async def search_products(self, search_term: str, **filters) -> List[Dict[str, Any]]:
        """
        Busca produtos no Mercado Livre.
        
        Args:
            search_term: Termo de busca
            **filters: Filtros (min_price, max_price, max_results, etc.)
            
        Returns:
            Lista de produtos encontrados
        """
        logger.info(f"Buscando produtos no Mercado Livre: '{search_term}'")
        
        products = []
        page = 1
        max_results = filters.get('max_results', 50)
        
        while len(products) < max_results:
            try:
                # Construir URL de busca
                search_url = f"{self.search_url}/{search_term.replace(' ', '-')}"
                
                # Parâmetros
                params = {}
                
                if page > 1:
                    params['_from'] = (page - 1) * 50 + 1
                
                # Filtros de preço
                if 'min_price' in filters or 'max_price' in filters:
                    price_filter = self._build_price_filter(filters)
                    if price_filter:
                        params.update(price_filter)
                
                # Fazer requisição
                response = await self._make_request(search_url, params)
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
        
        logger.info(f"Mercado Livre: {len(filtered_products)} produtos após filtros")
        return filtered_products
    
    def _build_price_filter(self, filters: Dict) -> Dict:
        """Constrói filtros de preço para Mercado Livre."""
        price_params = {}
        
        min_price = filters.get('min_price')
        max_price = filters.get('max_price')
        
        if min_price is not None:
            price_params['precio_desde'] = int(min_price)
        
        if max_price is not None:
            price_params['precio_hasta'] = int(max_price)
        
        return price_params
    
    def _extract_products_from_page(self, soup) -> List[Dict[str, Any]]:
        """Extrai produtos de uma página de resultados."""
        products = []
        
        # Seletores para diferentes layouts do ML
        selectors = [
            '.ui-search-result',
            '.results-item',
            '.item'
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
        """Faz parsing de um elemento de produto do Mercado Livre."""
        try:
            # Título
            title_selectors = [
                '.ui-search-item__title',
                '.item__title',
                'h2 a'
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
                '.ui-search-item__group__element a',
                '.item__title a',
                'a[href*="/MLB-"]'
            ]
            url = ""
            for selector in url_selectors:
                url = self._extract_url(element, selector, base_url=base_url)
                if url:
                    break
            
            # Preço
            price_selectors = [
                '.price-tag-amount',
                '.ui-search-price__second-line .price-tag-amount',
                '.item__price'
            ]
            price = 0.0
            for selector in price_selectors:
                price = self._extract_price(element, selector)
                if price > 0:
                    break
            
            # Preço original (se em desconto)
            original_price_selectors = [
                '.ui-search-price__original-value',
                '.item__discount-price'
            ]
            original_price = 0.0
            for selector in original_price_selectors:
                original_price = self._extract_price(element, selector)
                if original_price > 0:
                    break
            
            # Desconto
            discount_text = self._extract_text(element, '.ui-search-price__discount')
            discount_percent = 0
            if discount_text:
                discount_percent = extract_number(discount_text)
            
            # Frete grátis
            free_shipping = bool(
                element.select('.ui-search-item__shipping') and
                'grátis' in self._extract_text(element, '.ui-search-item__shipping').lower()
            )
            
            # Mercado Envios
            mercado_envios = bool(element.select('.ui-search-item__shipping-label'))
            
            # Vendedor
            seller_selectors = [
                '.ui-search-item__group__element--seller',
                '.item__seller'
            ]
            seller = ""
            for selector in seller_selectors:
                seller = self._extract_text(element, selector)
                if seller:
                    break
            
            # Localização
            location = self._extract_text(element, '.ui-search-item__group__element--location')
            
            # Avaliação
            rating_selectors = [
                '.ui-search-reviews__rating-number',
                '.item__reviews-rating'
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
                '.ui-search-reviews__amount',
                '.item__reviews-total'
            ]
            num_reviews = 0
            for selector in reviews_selectors:
                reviews_text = self._extract_text(element, selector)
                if reviews_text:
                    num_reviews = extract_number(reviews_text)
                    if num_reviews > 0:
                        break
            
            # Imagem
            image_selectors = [
                '.ui-search-result-image__element img',
                '.item__image img'
            ]
            image_url = ""
            for selector in image_selectors:
                image_url = self._extract_image_url(element, selector, base_url)
                if image_url:
                    break
            
            # Mercado Líder
            is_leader = bool(element.select('.ui-search-item__group__element--leader'))
            
            # Condição (novo/usado)
            condition_text = self._extract_text(element, '.ui-search-item__group__element--condition')
            condition = 'Novo' if 'novo' in condition_text.lower() else 'Usado' if 'usado' in condition_text.lower() else ''
            
            # Parcelamento
            installments_text = self._extract_text(element, '.ui-search-item__group__element--installments')
            
            product = {
                'title': title,
                'price': price,
                'original_price': original_price if original_price > price else None,
                'discount_percent': discount_percent,
                'url': url,
                'image_url': image_url,
                'rating': rating,
                'num_reviews': num_reviews,
                'free_shipping': free_shipping,
                'mercado_envios': mercado_envios,
                'seller': seller,
                'location': location,
                'is_leader': is_leader,
                'condition': condition,
                'installments': installments_text,
                'site': 'Mercado Livre',
                'currency': 'BRL'
            }
            
            return product
            
        except Exception as e:
            logger.debug(f"Erro ao fazer parse do produto ML: {e}")
            return None
    
    async def get_product_details(self, product_url: str) -> Optional[Dict[str, Any]]:
        """
        Obtém detalhes adicionais de um produto específico do Mercado Livre.
        
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
            
            # Descrição
            description_selectors = [
                '.ui-pdp-description__content',
                '.item-description'
            ]
            description = ""
            for selector in description_selectors:
                description = self._extract_text(soup, selector)
                if description:
                    break
            
            # Especificações
            specs = {}
            spec_rows = soup.select('.ui-pdp-specs__table tr')
            for row in spec_rows:
                cells = row.select('td, th')
                if len(cells) >= 2:
                    key = clean_text(cells[0].get_text())
                    value = clean_text(cells[1].get_text())
                    if key and value:
                        specs[key] = value
            
            # Imagens adicionais
            images = []
            img_elements = soup.select('.ui-pdp-gallery img')
            for img in img_elements:
                src = img.get('src') or img.get('data-src')
                if src:
                    images.append(src)
            
            # Informações do vendedor
            seller_info = {
                'name': self._extract_text(soup, '.ui-pdp-seller__header__title'),
                'reputation': self._extract_text(soup, '.ui-seller-info__status-info__title'),
                'sales': self._extract_text(soup, '.ui-seller-info__status-info__subtitle')
            }
            
            return {
                'detailed_description': description,
                'specifications': specs,
                'images': list(set(images)),
                'seller_info': seller_info,
                'warranty': self._extract_text(soup, '.ui-pdp-warranty'),
                'return_policy': self._extract_text(soup, '.ui-pdp-returns')
            }
            
        except Exception as e:
            logger.error(f"Erro ao obter detalhes do produto ML: {e}")
            return None
