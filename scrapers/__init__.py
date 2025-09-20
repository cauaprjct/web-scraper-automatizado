"""
Módulo de Web Scrapers
======================

Este módulo contém todos os scrapers para diferentes sites.
Cada scraper herda da classe BaseScraper e implementa
funcionalidades específicas para seu site.

Scrapers disponíveis:
- AmazonScraper: Para Amazon.com.br
- EbayScraper: Para eBay.com
- MercadoLivreScraper: Para MercadoLivre.com.br

Uso:
    from scrapers import ScraperFactory
    scraper = ScraperFactory.create_scraper('amazon', settings)
"""

from .base_scraper import BaseScraper
from .amazon_scraper import AmazonScraper
from .ebay_scraper import EbayScraper
from .mercadolivre_scraper import MercadoLivreScraper
from .scraper_factory import ScraperFactory

__all__ = [
    "BaseScraper",
    "AmazonScraper",
    "EbayScraper", 
    "MercadoLivreScraper",
    "ScraperFactory"
]

__version__ = "1.0.0"
__author__ = "Seu Nome"
