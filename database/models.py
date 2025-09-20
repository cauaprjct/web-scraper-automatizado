"""
Modelos de Banco de Dados
========================

Este módulo define todos os modelos SQLAlchemy para o sistema.
Inclui tabelas para produtos, histórico de preços, sessões e logs.

Autor: Seu Nome
Data: 2025-09-20
"""

from datetime import datetime
from typing import Optional, List
from sqlalchemy import Column, Integer, String, Float, DateTime, Boolean, Text, ForeignKey, Index
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

Base = declarative_base()


class Product(Base):
    """
    Modelo para produtos encontrados durante o scraping.
    
    Armazena informações básicas do produto e relaciona com
    histórico de preços e sessões de scraping.
    """
    
    __tablename__ = 'products'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    
    # Informações básicas
    title = Column(String(500), nullable=False)
    url = Column(String(1000), nullable=False)
    site = Column(String(50), nullable=False)
    external_id = Column(String(100))  # ID do produto no site (ASIN, etc.)
    
    # Preço atual
    current_price = Column(Float, nullable=False)
    original_price = Column(Float)  # Preço original se em promoção
    currency = Column(String(10), default='BRL')
    
    # Informações adicionais
    image_url = Column(String(1000))
    rating = Column(Float, default=0.0)
    num_reviews = Column(Integer, default=0)
    
    # Status
    in_stock = Column(Boolean, default=True)
    free_shipping = Column(Boolean, default=False)
    
    # Metadados
    first_seen = Column(DateTime, default=func.now())
    last_updated = Column(DateTime, default=func.now(), onupdate=func.now())
    
    # Relacionamentos
    price_history = relationship("PriceHistory", back_populates="product", cascade="all, delete-orphan")
    
    # Índices
    __table_args__ = (
        Index('idx_product_site_external_id', 'site', 'external_id'),
        Index('idx_product_url', 'url'),
        Index('idx_product_title', 'title'),
        Index('idx_product_last_updated', 'last_updated'),
    )
    
    def __repr__(self):
        return f"<Product(id={self.id}, title='{self.title[:50]}...', price={self.current_price})>"
    
    def to_dict(self) -> dict:
        """Converte o produto para dicionário."""
        return {
            'id': self.id,
            'title': self.title,
            'url': self.url,
            'site': self.site,
            'external_id': self.external_id,
            'current_price': self.current_price,
            'original_price': self.original_price,
            'currency': self.currency,
            'image_url': self.image_url,
            'rating': self.rating,
            'num_reviews': self.num_reviews,
            'in_stock': self.in_stock,
            'free_shipping': self.free_shipping,
            'first_seen': self.first_seen.isoformat() if self.first_seen else None,
            'last_updated': self.last_updated.isoformat() if self.last_updated else None
        }


class PriceHistory(Base):
    """
    Modelo para histórico de preços dos produtos.
    
    Permite rastrear mudanças de preço ao longo do tempo
    e identificar tendências e ofertas.
    """
    
    __tablename__ = 'price_history'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    product_id = Column(Integer, ForeignKey('products.id'), nullable=False)
    
    # Preços
    price = Column(Float, nullable=False)
    original_price = Column(Float)  # Preço original se em promoção
    discount_percent = Column(Float, default=0.0)
    
    # Metadados
    recorded_at = Column(DateTime, default=func.now())
    session_id = Column(Integer, ForeignKey('scraping_sessions.id'))
    
    # Relacionamentos
    product = relationship("Product", back_populates="price_history")
    session = relationship("ScrapingSession", back_populates="price_records")
    
    # Índices
    __table_args__ = (
        Index('idx_price_history_product_id', 'product_id'),
        Index('idx_price_history_recorded_at', 'recorded_at'),
        Index('idx_price_history_session_id', 'session_id'),
    )
    
    def __repr__(self):
        return f"<PriceHistory(product_id={self.product_id}, price={self.price}, recorded_at={self.recorded_at})>"
    
    def to_dict(self) -> dict:
        """Converte o histórico para dicionário."""
        return {
            'id': self.id,
            'product_id': self.product_id,
            'price': self.price,
            'original_price': self.original_price,
            'discount_percent': self.discount_percent,
            'recorded_at': self.recorded_at.isoformat() if self.recorded_at else None,
            'session_id': self.session_id
        }


class ScrapingSession(Base):
    """
    Modelo para sessões de scraping.
    
    Rastreia cada execução do scraper, incluindo parâmetros,
    resultados e estatísticas de performance.
    """
    
    __tablename__ = 'scraping_sessions'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    
    # Informações da sessão
    session_name = Column(String(200))
    site = Column(String(50), nullable=False)
    search_term = Column(String(200))
    
    # Parâmetros
    filters_applied = Column(Text)  # JSON com filtros aplicados
    
    # Resultados
    products_found = Column(Integer, default=0)
    products_saved = Column(Integer, default=0)
    new_products = Column(Integer, default=0)
    price_changes = Column(Integer, default=0)
    
    # Status
    success = Column(Boolean, default=False)
    error_message = Column(Text)
    
    # Timing
    started_at = Column(DateTime, default=func.now())
    completed_at = Column(DateTime)
    duration_seconds = Column(Float)
    
    # Relacionamentos
    price_records = relationship("PriceHistory", back_populates="session")
    email_logs = relationship("EmailLog", back_populates="session")
    
    # Índices
    __table_args__ = (
        Index('idx_session_site', 'site'),
        Index('idx_session_started_at', 'started_at'),
        Index('idx_session_success', 'success'),
    )
    
    def __repr__(self):
        return f"<ScrapingSession(id={self.id}, site='{self.site}', search='{self.search_term}', success={self.success})>"
    
    def to_dict(self) -> dict:
        """Converte a sessão para dicionário."""
        return {
            'id': self.id,
            'session_name': self.session_name,
            'site': self.site,
            'search_term': self.search_term,
            'filters_applied': self.filters_applied,
            'products_found': self.products_found,
            'products_saved': self.products_saved,
            'new_products': self.new_products,
            'price_changes': self.price_changes,
            'success': self.success,
            'error_message': self.error_message,
            'started_at': self.started_at.isoformat() if self.started_at else None,
            'completed_at': self.completed_at.isoformat() if self.completed_at else None,
            'duration_seconds': self.duration_seconds
        }


class EmailLog(Base):
    """
    Modelo para log de e-mails enviados.
    
    Rastreia todos os e-mails enviados pelo sistema,
    incluindo destinatários, conteúdo e status de entrega.
    """
    
    __tablename__ = 'email_logs'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    
    # Informações do e-mail
    recipients = Column(Text, nullable=False)  # JSON com lista de destinatários
    subject = Column(String(500), nullable=False)
    email_type = Column(String(50))  # 'product_report', 'price_alert', 'daily_summary'
    
    # Conteúdo
    products_count = Column(Integer, default=0)
    has_attachments = Column(Boolean, default=False)
    
    # Status
    sent_successfully = Column(Boolean, default=False)
    error_message = Column(Text)
    
    # Timing
    sent_at = Column(DateTime, default=func.now())
    
    # Relacionamentos
    session_id = Column(Integer, ForeignKey('scraping_sessions.id'))
    session = relationship("ScrapingSession", back_populates="email_logs")
    
    # Índices
    __table_args__ = (
        Index('idx_email_log_sent_at', 'sent_at'),
        Index('idx_email_log_email_type', 'email_type'),
        Index('idx_email_log_success', 'sent_successfully'),
    )
    
    def __repr__(self):
        return f"<EmailLog(id={self.id}, subject='{self.subject}', success={self.sent_successfully})>"
    
    def to_dict(self) -> dict:
        """Converte o log para dicionário."""
        return {
            'id': self.id,
            'recipients': self.recipients,
            'subject': self.subject,
            'email_type': self.email_type,
            'products_count': self.products_count,
            'has_attachments': self.has_attachments,
            'sent_successfully': self.sent_successfully,
            'error_message': self.error_message,
            'sent_at': self.sent_at.isoformat() if self.sent_at else None,
            'session_id': self.session_id
        }


# Funções utilitárias para trabalhar com modelos

def create_product_from_dict(product_data: dict) -> Product:
    """
    Cria um objeto Product a partir de um dicionário.
    
    Args:
        product_data: Dicionário com dados do produto
        
    Returns:
        Instância de Product
    """
    return Product(
        title=product_data.get('title', ''),
        url=product_data.get('url', ''),
        site=product_data.get('site', ''),
        external_id=product_data.get('external_id') or product_data.get('asin'),
        current_price=product_data.get('price', 0.0),
        original_price=product_data.get('original_price'),
        currency=product_data.get('currency', 'BRL'),
        image_url=product_data.get('image_url', ''),
        rating=product_data.get('rating', 0.0),
        num_reviews=product_data.get('num_reviews', 0),
        in_stock=product_data.get('in_stock', True),
        free_shipping=product_data.get('free_shipping', False)
    )


def create_price_history_from_product(product: Product, session_id: Optional[int] = None) -> PriceHistory:
    """
    Cria um registro de histórico de preço a partir de um produto.
    
    Args:
        product: Instância de Product
        session_id: ID da sessão de scraping
        
    Returns:
        Instância de PriceHistory
    """
    discount_percent = 0.0
    if product.original_price and product.original_price > product.current_price:
        discount_percent = ((product.original_price - product.current_price) / product.original_price) * 100
    
    return PriceHistory(
        product_id=product.id,
        price=product.current_price,
        original_price=product.original_price,
        discount_percent=discount_percent,
        session_id=session_id
    )
