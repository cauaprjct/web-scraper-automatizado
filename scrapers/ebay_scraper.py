"""
Scraper para eBay
=================

Este módulo implementa o scraper específico para eBay.
Extrai informações de produtos, preços, avaliações e vendedores.

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


class EbayScraper(BaseScraper):
    """
    Scraper específico para eBay.
    
    Extrai informações de produtos incluindo:
    - Título
    - Preço atual e de compra imediata
    - Tipo de leilão (auction/buy-it-now)
    - Vendedor e avaliações
    - Localização
    - Tempo restante (para leilões)
    - Imagens
    """
    
    def __init__(self, settings: Any):
        """
        Inicializa o scraper do eBay.
        
        Args:
            settings: Configurações do sistema
        """
        super().__init__(settings)
        
        self.base_url = getattr(settings, 'ebay_base_url', 'https://www.ebay.com')
        self.search_url = getattr(settings, 'ebay_search_url', 'https://www.ebay.com/sch/i.html')
        
        # Configurar headers específicos do eBay
        self._setup_ebay_headers()
        
        logger.info("eBay scraper inicializado")
    
    def _setup_ebay_headers(self):
        """Configura headers específicos para eBay."""
        self.session.headers.update({
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.9,pt;q=0.8',
            'Cache-Control': 'no-cache',
            'Pragma': 'no-cache',
        })
    
    def get_base_url(self) -> str:
        """Retorna URL base do eBay."""
        return self.base_url
    
    def get_search_url(self) -> str:
        """Retorna URL de busca do eBay."""
        return self.search_url
    
    async def search_products(self, search_term: str, **filters) -> List[Dict[str, Any]]:
        """
        Busca produtos no eBay.
        
        Args:
            search_term: Termo de busca
            **filters: Filtros (min_price, max_price, max_results, etc.)
            
        Returns:
            Lista de produtos encontrados
        """
        logger.info(f"Buscando produtos no eBay: '{search_term}'")
        
        products = []
        page = 1
        max_results = filters.get('max_results', 50)
        
        while len(products) < max_results:
            try:
                # Construir parâmetros de busca
                params = {
                    '_nkw': search_term,
                    '_pgn': page,
                    '_skc': 0,
                    'rt': 'nc'
                }
                
                # Adicionar filtros de preço
                if 'min_price' in filters:
                    params['_udlo'] = filters['min_price']
                if 'max_price' in filters:
                    params['_udhi'] = filters['max_price']
                
                # Filtro para Buy It Now apenas
                if filters.get('buy_it_now_only'):
                    params['LH_BIN'] = 1
                
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
        
        logger.info(f"eBay: {len(filtered_products)} produtos após filtros")
        return filtered_products
    
    def _extract_products_from_page(self, soup) -> List[Dict[str, Any]]:
        """Extrai produtos de uma página de resultados."""
        products = []
        
        # Seletores para diferentes layouts do eBay
        selectors = [
            '.s-item',
            '.sresult',
            '[data-view="mi:1686|iid:1"]'
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
        """Faz parsing de um elemento de produto do eBay."""
        try:
            # Título
            title_selectors = [
                '.s-item__title',
                'h3.s-item__title',
                '.it-ttl a'
            ]
            title = ""
            for selector in title_selectors:
                title = self._extract_text(element, selector)
                if title and title.lower() != 'new listing':
                    break
            
            if not title or title.lower() in ['new listing', 'shop on ebay']:
                return None
            
            # URL
            url_selectors = [
                '.s-item__link',
                '.it-ttl a',
                'a[href*="/itm/"]'
            ]
            url = ""
            for selector in url_selectors:
                url = self._extract_url(element, selector, base_url=base_url)
                if url:
                    break
            
            # Preço
            price_selectors = [
                '.s-item__price .notranslate',
                '.s-item__price',
                '.u-flL.condText + .notranslate'
            ]
            price = 0.0
            for selector in price_selectors:
                price_text = self._extract_text(element, selector)
                if price_text:
                    # eBay pode ter ranges de preço, pegar o menor
                    if 'to' in price_text.lower():
                        prices = re.findall(r'[\d,]+\.\d{2}', price_text)
                        if prices:
                            price = format_price(prices[0])
                    else:
                        price = format_price(price_text)
                    if price > 0:
                        break
            
            # Tipo de leilão
            auction_type = 'Buy It Now'
            if element.select('.s-item__time-left, .timeMs'):
                auction_type = 'Auction'
            
            # Tempo restante (para leilões)
            time_left = ""
            if auction_type == 'Auction':
                time_left = self._extract_text(element, '.s-item__time-left, .timeMs')
            
            # Vendedor
            seller_selectors = [
                '.s-item__seller-info-text',
                '.s-item__seller'
            ]
            seller = ""
            for selector in seller_selectors:
                seller = self._extract_text(element, selector)
                if seller:
                    break
            
            # Localização
            location_selectors = [
                '.s-item__location',
                '.s-item__itemLocation'
            ]
            location = ""
            for selector in location_selectors:
                location = self._extract_text(element, selector)
                if location:
                    break
            
            # Frete
            shipping_selectors = [
                '.s-item__shipping',
                '.s-item__logisticsCost'
            ]
            shipping_cost = ""
            for selector in shipping_selectors:
                shipping_cost = self._extract_text(element, selector)
                if shipping_cost:
                    break
            
            free_shipping = 'free' in shipping_cost.lower() or 'grátis' in shipping_cost.lower()
            
            # Imagem
            image_selectors = [
                '.s-item__image img',
                '.img img'
            ]
            image_url = ""
            for selector in image_selectors:
                image_url = self._extract_image_url(element, selector, base_url)
                if image_url:
                    break
            
            # Condição
            condition_selectors = [
                '.s-item__subtitle',
                '.condText'
            ]
            condition = ""
            for selector in condition_selectors:
                condition = self._extract_text(element, selector)
                if condition and any(word in condition.lower() for word in ['new', 'used', 'refurbished']):
                    break
            
            # Watchers (pessoas observando)
            watchers = 0
            watchers_text = self._extract_text(element, '.s-item__watchheart')
            if watchers_text:
                watchers = extract_number(watchers_text)
            
            product = {
                'title': title,
                'price': price,
                'url': url,
                'image_url': image_url,
                'auction_type': auction_type,
                'time_left': time_left,
                'seller': seller,
                'location': location,
                'shipping_cost': shipping_cost,
                'free_shipping': free_shipping,
                'condition': condition,
                'watchers': watchers,
                'site': 'eBay',
                'currency': 'USD'  # eBay principalmente USD
            }
            
            return product
            
        except Exception as e:
            logger.debug(f"Erro ao fazer parse do produto eBay: {e}")
            return None
    
    async def get_product_details(self, product_url: str) -> Optional[Dict[str, Any]]:
        """
        Obtém detalhes adicionais de um produto específico do eBay.
        
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
            description = self._extract_text(soup, '#desc_div, .u-flL.condText')
            
            # Especificações
            specs = {}
            spec_rows = soup.select('.u-flL.condText tr')
            for row in spec_rows:
                cells = row.select('td')
                if len(cells) >= 2:
                    key = clean_text(cells[0].get_text())
                    value = clean_text(cells[1].get_text())
                    if key and value:
                        specs[key] = value
            
            # Imagens adicionais
            images = []
            img_elements = soup.select('#vi_main_img_fs img, .img img')
            for img in img_elements:
                src = img.get('src') or img.get('data-src')
                if src:
                    images.append(src)
            
            return {
                'detailed_description': description,
                'specifications': specs,
                'images': list(set(images)),
                'seller_feedback': self._extract_text(soup, '.mbg-nw'),
                'return_policy': self._extract_text(soup, '.u-flL.condText')
            }
            
        except Exception as e:
            logger.error(f"Erro ao obter detalhes do produto eBay: {e}")
            return None
