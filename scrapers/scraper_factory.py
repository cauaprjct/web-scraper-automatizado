"""
Factory para criação de scrapers específicos por site.
"""

from typing import Optional
from config.settings import Settings
from .base_scraper import BaseScraper
from .amazon_scraper import AmazonScraper
from .ebay_scraper import EbayScraper
from .mercadolivre_scraper import MercadoLivreScraper
from utils.logger import setup_logger

logger = setup_logger(__name__)


class ScraperFactory:
    """
    Factory para criar scrapers específicos baseado no site.
    
    Permite adicionar novos scrapers facilmente sem modificar
    o código cliente.
    """
    
    # Mapeamento de sites para classes de scraper
    _scrapers = {
        'amazon': AmazonScraper,
        'ebay': EbayScraper,
        'mercadolivre': MercadoLivreScraper,
        'mercado_livre': MercadoLivreScraper,  # Alias
        'ml': MercadoLivreScraper,  # Alias
    }
    
    @classmethod
    def create_scraper(cls, site: str, settings: Settings) -> Optional[BaseScraper]:
        """
        Cria um scraper para o site especificado.
        
        Args:
            site: Nome do site (amazon, ebay, mercadolivre)
            settings: Configurações do sistema
            
        Returns:
            Instância do scraper ou None se site não suportado
            
        Raises:
            ValueError: Se o site não for suportado
        """
        site_lower = site.lower().strip()
        
        if site_lower not in cls._scrapers:
            available_sites = ', '.join(cls._scrapers.keys())
            raise ValueError(
                f"Site '{site}' não suportado. Sites disponíveis: {available_sites}"
            )
        
        scraper_class = cls._scrapers[site_lower]
        
        try:
            scraper = scraper_class(settings)
            logger.info(f"Scraper criado com sucesso: {scraper_class.__name__}")
            return scraper
            
        except Exception as e:
            logger.error(f"Erro ao criar scraper para {site}: {e}")
            raise
    
    @classmethod
    def get_supported_sites(cls) -> list:
        """
        Retorna lista de sites suportados.
        
        Returns:
            Lista de nomes de sites suportados
        """
        return list(cls._scrapers.keys())
    
    @classmethod
    def register_scraper(cls, site: str, scraper_class: type):
        """
        Registra um novo scraper.
        
        Args:
            site: Nome do site
            scraper_class: Classe do scraper (deve herdar de BaseScraper)
            
        Raises:
            TypeError: Se scraper_class não herda de BaseScraper
        """
        if not issubclass(scraper_class, BaseScraper):
            raise TypeError("Scraper deve herdar de BaseScraper")
        
        cls._scrapers[site.lower()] = scraper_class
        logger.info(f"Scraper registrado: {site} -> {scraper_class.__name__}")
    
    @classmethod
    def is_site_supported(cls, site: str) -> bool:
        """
        Verifica se um site é suportado.
        
        Args:
            site: Nome do site
            
        Returns:
            True se suportado
        """
        return site.lower().strip() in cls._scrapers
    
    @classmethod
    def get_scraper_info(cls) -> dict:
        """
        Retorna informações sobre todos os scrapers disponíveis.
        
        Returns:
            Dicionário com informações dos scrapers
        """
        info = {}
        
        for site, scraper_class in cls._scrapers.items():
            try:
                # Criar instância temporária para obter informações
                from config.settings import Settings
                temp_settings = Settings()
                temp_scraper = scraper_class(temp_settings)
                
                info[site] = {
                    'class_name': scraper_class.__name__,
                    'base_url': temp_scraper.get_base_url(),
                    'search_url': temp_scraper.get_search_url(),
                    'site_name': temp_scraper.get_site_name()
                }
                
            except Exception as e:
                info[site] = {
                    'class_name': scraper_class.__name__,
                    'error': str(e)
                }
        
        return info


# Função de conveniência para criar scraper
def create_scraper(site: str, settings: Settings) -> BaseScraper:
    """
    Função de conveniência para criar um scraper.
    
    Args:
        site: Nome do site
        settings: Configurações
        
    Returns:
        Instância do scraper
    """
    return ScraperFactory.create_scraper(site, settings)


# Função para listar sites suportados
def get_supported_sites() -> list:
    """
    Função de conveniência para obter sites suportados.
    
    Returns:
        Lista de sites suportados
    """
    return ScraperFactory.get_supported_sites()
