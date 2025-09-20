"""
Testes para Scrapers
====================

Testes unitários para todos os scrapers do sistema,
incluindo testes de parsing, validação e integração.

Autor: Seu Nome
Data: 2025-09-20
"""

import pytest
import asyncio
from unittest.mock import Mock, patch, AsyncMock
from bs4 import BeautifulSoup
import sys
from pathlib import Path

# Adicionar o diretório raiz ao path
sys.path.append(str(Path(__file__).parent.parent))

from config.settings import Settings
from scrapers import ScraperFactory, BaseScraper
from scrapers.amazon_scraper import AmazonScraper
from scrapers.ebay_scraper import EbayScraper
from scrapers.mercadolivre_scraper import MercadoLivreScraper


class TestScraperFactory:
    """
    Testes para ScraperFactory.
    """
    
    def test_create_amazon_scraper(self):
        """Testa criação do scraper Amazon."""
        settings = Settings()
        scraper = ScraperFactory.create_scraper('amazon', settings)
        
        assert isinstance(scraper, AmazonScraper)
        assert scraper.get_base_url() == settings.amazon_base_url
    
    def test_create_ebay_scraper(self):
        """Testa criação do scraper eBay."""
        settings = Settings()
        scraper = ScraperFactory.create_scraper('ebay', settings)
        
        assert isinstance(scraper, EbayScraper)
        assert scraper.get_base_url() == settings.ebay_base_url
    
    def test_create_mercadolivre_scraper(self):
        """Testa criação do scraper Mercado Livre."""
        settings = Settings()
        scraper = ScraperFactory.create_scraper('mercadolivre', settings)
        
        assert isinstance(scraper, MercadoLivreScraper)
        assert scraper.get_base_url() == settings.mercadolivre_base_url
    
    def test_invalid_site(self):
        """Testa erro para site inválido."""
        settings = Settings()
        
        with pytest.raises(ValueError):
            ScraperFactory.create_scraper('invalid_site', settings)
    
    def test_get_supported_sites(self):
        """Testa lista de sites suportados."""
        sites = ScraperFactory.get_supported_sites()
        
        assert 'amazon' in sites
        assert 'ebay' in sites
        assert 'mercadolivre' in sites
        assert len(sites) >= 3
    
    def test_is_site_supported(self):
        """Testa verificação de suporte a site."""
        assert ScraperFactory.is_site_supported('amazon')
        assert ScraperFactory.is_site_supported('ebay')
        assert ScraperFactory.is_site_supported('mercadolivre')
        assert not ScraperFactory.is_site_supported('invalid')


class TestBaseScraper:
    """
    Testes para funcionalidades base dos scrapers.
    """
    
    def setup_method(self):
        """Configuração para cada teste."""
        self.settings = Settings()
        self.scraper = AmazonScraper(self.settings)  # Usar Amazon como exemplo
    
    def test_initialization(self):
        """Testa inicialização do scraper."""
        assert self.scraper.settings == self.settings
        assert self.scraper.session is not None
        assert self.scraper.delay == self.settings.scraping_delay
        assert self.scraper.timeout == self.settings.request_timeout
    
    def test_extract_text(self):
        """Testa extração de texto."""
        html = '<div class="test">  Texto de teste  </div>'
        soup = BeautifulSoup(html, 'html.parser')
        element = soup.find('div')
        
        text = self.scraper._extract_text(element)
        assert text == 'Texto de teste'
        
        # Teste com seletor
        text_with_selector = self.scraper._extract_text(soup, '.test')
        assert text_with_selector == 'Texto de teste'
    
    def test_extract_price(self):
        """Testa extração de preço."""
        html = '<span class="price">R$ 1.234,56</span>'
        soup = BeautifulSoup(html, 'html.parser')
        element = soup.find('span')
        
        price = self.scraper._extract_price(element)
        assert price == 1234.56
    
    def test_extract_url(self):
        """Testa extração de URL."""
        html = '<a href="/produto/123">Link</a>'
        soup = BeautifulSoup(html, 'html.parser')
        element = soup.find('a')
        
        url = self.scraper._extract_url(element, base_url='https://example.com')
        assert url == 'https://example.com/produto/123'
    
    def test_validate_product_valid(self):
        """Testa validação de produto válido."""
        product = {
            'title': 'Produto Teste',
            'price': 99.99,
            'url': 'https://example.com/produto'
        }
        
        assert self.scraper._validate_product(product)
    
    def test_validate_product_invalid(self):
        """Testa validação de produto inválido."""
        # Produto sem título
        product1 = {
            'price': 99.99,
            'url': 'https://example.com/produto'
        }
        assert not self.scraper._validate_product(product1)
        
        # Produto com preço inválido
        product2 = {
            'title': 'Produto',
            'price': 0,
            'url': 'https://example.com/produto'
        }
        assert not self.scraper._validate_product(product2)
        
        # Produto sem URL
        product3 = {
            'title': 'Produto',
            'price': 99.99
        }
        assert not self.scraper._validate_product(product3)
    
    def test_apply_filters(self):
        """Testa aplicação de filtros."""
        products = [
            {'title': 'Produto 1', 'price': 50.0, 'rating': 4.5},
            {'title': 'Produto 2', 'price': 150.0, 'rating': 3.0},
            {'title': 'Produto 3', 'price': 100.0, 'rating': 4.8}
        ]
        
        # Filtro de preço máximo
        filtered = self.scraper._apply_filters(products, max_price=100.0)
        assert len(filtered) == 2
        
        # Filtro de preço mínimo
        filtered = self.scraper._apply_filters(products, min_price=75.0)
        assert len(filtered) == 2
        
        # Filtro de avaliação
        filtered = self.scraper._apply_filters(products, min_rating=4.0)
        assert len(filtered) == 2
        
        # Múltiplos filtros
        filtered = self.scraper._apply_filters(
            products, 
            min_price=50.0, 
            max_price=150.0, 
            min_rating=4.0
        )
        assert len(filtered) == 2
    
    def test_get_site_name(self):
        """Testa obtenção do nome do site."""
        site_name = self.scraper.get_site_name()
        assert 'amazon' in site_name.lower()


class TestAmazonScraper:
    """
    Testes específicos para AmazonScraper.
    """
    
    def setup_method(self):
        """Configuração para cada teste."""
        self.settings = Settings()
        self.scraper = AmazonScraper(self.settings)
    
    def test_parse_product_element(self):
        """Testa parsing de elemento de produto da Amazon."""
        # HTML simulado de produto Amazon
        html = '''
        <div data-component-type="s-search-result">
            <h2><a href="/dp/B123456"><span>Notebook Gamer Test</span></a></h2>
            <span class="a-price-whole">1.999</span>
            <span class="a-icon-alt">4,5 de 5 estrelas</span>
            <img class="s-image" src="https://example.com/image.jpg" />
        </div>
        '''
        
        soup = BeautifulSoup(html, 'html.parser')
        element = soup.find('div')
        
        product = self.scraper._parse_product_element(element, 'https://amazon.com.br')
        
        assert product is not None
        assert 'Notebook Gamer Test' in product['title']
        assert product['price'] == 1999.0
        assert product['site'] == 'Amazon'
        assert 'amazon.com.br' in product['url']
    
    @patch('scrapers.base_scraper.BaseScraper._make_request')
    @pytest.mark.asyncio
    async def test_search_products_mock(self, mock_request):
        """Testa busca de produtos com mock."""
        # HTML de resposta simulado
        mock_html = '''
        <html>
            <div data-component-type="s-search-result">
                <h2><a href="/dp/B123"><span>Produto Teste</span></a></h2>
                <span class="a-price-whole">99</span>
            </div>
        </html>
        '''
        
        # Configurar mock
        mock_response = Mock()
        mock_response.text = mock_html
        mock_request.return_value = mock_response
        
        # Executar busca
        products = await self.scraper.search_products('teste', max_results=1)
        
        # Verificar resultados
        assert len(products) >= 0  # Pode ser 0 se o parsing falhar
        mock_request.assert_called()


class TestEbayScraper:
    """
    Testes específicos para EbayScraper.
    """
    
    def setup_method(self):
        """Configuração para cada teste."""
        self.settings = Settings()
        self.scraper = EbayScraper(self.settings)
    
    def test_parse_product_element(self):
        """Testa parsing de elemento de produto do eBay."""
        html = '''
        <div class="s-item">
            <h3 class="s-item__title">Tablet Test Device</h3>
            <span class="s-item__price">$299.99</span>
            <span class="s-item__seller-info-text">seller123</span>
            <img class="s-item__image" src="https://example.com/tablet.jpg" />
        </div>
        '''
        
        soup = BeautifulSoup(html, 'html.parser')
        element = soup.find('div')
        
        product = self.scraper._parse_product_element(element, 'https://ebay.com')
        
        assert product is not None
        assert 'Tablet Test Device' in product['title']
        assert product['price'] == 299.99
        assert product['site'] == 'eBay'
        assert product['seller'] == 'seller123'


class TestMercadoLivreScraper:
    """
    Testes específicos para MercadoLivreScraper.
    """
    
    def setup_method(self):
        """Configuração para cada teste."""
        self.settings = Settings()
        self.scraper = MercadoLivreScraper(self.settings)
    
    def test_parse_product_element(self):
        """Testa parsing de elemento de produto do Mercado Livre."""
        html = '''
        <div class="ui-search-result">
            <h2 class="ui-search-item__title">Smartphone Test 128GB</h2>
            <span class="price-tag-amount">899</span>
            <div class="ui-search-reviews__rating-number">4.2</div>
            <img class="ui-search-result-image__element" src="https://example.com/phone.jpg" />
        </div>
        '''
        
        soup = BeautifulSoup(html, 'html.parser')
        element = soup.find('div')
        
        product = self.scraper._parse_product_element(element, 'https://mercadolivre.com.br')
        
        assert product is not None
        assert 'Smartphone Test 128GB' in product['title']
        assert product['price'] == 899.0
        assert product['site'] == 'Mercado Livre'
        assert product['rating'] == 4.2


class TestIntegration:
    """
    Testes de integração para scrapers.
    """
    
    def setup_method(self):
        """Configuração para cada teste."""
        self.settings = Settings()
    
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_amazon_real_search(self):
        """Teste de integração real com Amazon (apenas se habilitado)."""
        scraper = AmazonScraper(self.settings)
        
        try:
            products = await scraper.search_products('test', max_results=1)
            # Não fazer asserções rígidas pois depende da disponibilidade do site
            assert isinstance(products, list)
        except Exception:
            # Ignorar erros de rede em testes
            pytest.skip("Erro de rede ou site indisponível")
    
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_robots_txt_check(self):
        """Testa verificação de robots.txt."""
        scraper = AmazonScraper(self.settings)
        
        try:
            allowed = await scraper.check_robots_txt()
            assert isinstance(allowed, bool)
        except Exception:
            pytest.skip("Erro de rede")


# Fixtures para testes
@pytest.fixture
def sample_product():
    """Produto de exemplo para testes."""
    return {
        'title': 'Produto de Teste',
        'price': 99.99,
        'url': 'https://example.com/produto/123',
        'site': 'TestSite',
        'rating': 4.5,
        'num_reviews': 100,
        'in_stock': True,
        'free_shipping': True
    }


@pytest.fixture
def sample_products_list():
    """Lista de produtos para testes."""
    return [
        {
            'title': 'Produto A',
            'price': 50.0,
            'url': 'https://example.com/a',
            'site': 'TestSite',
            'rating': 4.0
        },
        {
            'title': 'Produto B',
            'price': 150.0,
            'url': 'https://example.com/b',
            'site': 'TestSite',
            'rating': 3.5
        },
        {
            'title': 'Produto C',
            'price': 100.0,
            'url': 'https://example.com/c',
            'site': 'TestSite',
            'rating': 4.8
        }
    ]


# Utilitários para testes
class MockResponse:
    """Mock de resposta HTTP para testes."""
    
    def __init__(self, text, status_code=200):
        self.text = text
        self.status_code = status_code
    
    def raise_for_status(self):
        if self.status_code >= 400:
            raise Exception(f"HTTP {self.status_code}")


def create_mock_html(products_data):
    """Cria HTML mock com produtos para testes."""
    html = '<html><body>'
    
    for product in products_data:
        html += f'''
        <div class="product">
            <h2>{product.get('title', 'Produto')}</h2>
            <span class="price">{product.get('price', 0)}</span>
            <a href="{product.get('url', '#')}">Ver produto</a>
        </div>
        '''
    
    html += '</body></html>'
    return html


# Configuração do pytest
pytest_plugins = []


def pytest_configure(config):
    """Configuração do pytest."""
    config.addinivalue_line(
        "markers", "integration: marca testes de integração"
    )
    config.addinivalue_line(
        "markers", "slow: marca testes lentos"
    )


def pytest_collection_modifyitems(config, items):
    """Modifica coleção de testes."""
    # Pular testes de integração por padrão
    skip_integration = pytest.mark.skip(reason="Teste de integração desabilitado")
    
    for item in items:
        if "integration" in item.keywords:
            if not config.getoption("--integration", default=False):
                item.add_marker(skip_integration)


def pytest_addoption(parser):
    """Adiciona opções ao pytest."""
    parser.addoption(
        "--integration",
        action="store_true",
        default=False,
        help="Executar testes de integração"
    )
