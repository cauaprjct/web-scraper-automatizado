"""
Gerenciador de Banco de Dados
============================

Este módulo fornece o gerenciador principal para todas as operações
de banco de dados, incluindo conexão, CRUD e consultas especializadas.

Autor: Seu Nome
Data: 2025-09-20
"""

import asyncio
import json
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Any, Tuple
from sqlalchemy import create_engine, and_, or_, desc, func
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.exc import SQLAlchemyError

from .models import Base, Product, PriceHistory, ScrapingSession, EmailLog, create_product_from_dict
from utils.logger import setup_logger, log_database_operation

logger = setup_logger(__name__)


class DatabaseManager:
    """
    Gerenciador principal do banco de dados.
    
    Fornece interface de alto nível para todas as operações
    de banco de dados do sistema.
    """
    
    def __init__(self, database_url: str):
        """
        Inicializa o gerenciador de banco de dados.
        
        Args:
            database_url: URL de conexão com o banco
        """
        self.database_url = database_url
        self.engine = None
        self.SessionLocal = None
        
        logger.info(f"DatabaseManager inicializado: {database_url}")
    
    async def initialize(self):
        """
        Inicializa conexão e cria tabelas se necessário.
        """
        try:
            # Criar engine
            self.engine = create_engine(
                self.database_url,
                echo=False,  # Set to True for SQL debugging
                pool_pre_ping=True,
                pool_recycle=3600
            )
            
            # Criar session factory
            self.SessionLocal = sessionmaker(
                autocommit=False,
                autoflush=False,
                bind=self.engine
            )
            
            # Criar tabelas
            Base.metadata.create_all(bind=self.engine)
            
            logger.info("Banco de dados inicializado com sucesso")
            
        except Exception as e:
            logger.error(f"Erro ao inicializar banco de dados: {e}")
            raise
    
    def get_session(self) -> Session:
        """
        Cria uma nova sessão de banco de dados.
        
        Returns:
            Sessão do SQLAlchemy
        """
        if not self.SessionLocal:
            raise RuntimeError("Banco de dados não inicializado")
        
        return self.SessionLocal()
    
    # ==========================================
    # Operações com Produtos
    # ==========================================
    
    async def save_products(self, products_data: List[Dict], session_id: Optional[int] = None) -> List[Product]:
        """
        Salva lista de produtos no banco de dados.
        
        Args:
            products_data: Lista de dicionários com dados dos produtos
            session_id: ID da sessão de scraping
            
        Returns:
            Lista de produtos salvos
        """
        saved_products = []
        
        with self.get_session() as db:
            try:
                for product_data in products_data:
                    # Verificar se produto já existe
                    existing_product = self._find_existing_product(db, product_data)
                    
                    if existing_product:
                        # Atualizar produto existente
                        updated_product = await self._update_existing_product(
                            db, existing_product, product_data, session_id
                        )
                        saved_products.append(updated_product)
                    else:
                        # Criar novo produto
                        new_product = create_product_from_dict(product_data)
                        db.add(new_product)
                        db.flush()  # Para obter o ID
                        
                        # Criar histórico de preço inicial
                        price_history = PriceHistory(
                            product_id=new_product.id,
                            price=new_product.current_price,
                            original_price=new_product.original_price,
                            session_id=session_id
                        )
                        db.add(price_history)
                        
                        saved_products.append(new_product)
                
                db.commit()
                
                log_database_operation(
                    "INSERT/UPDATE", "products", len(saved_products), True
                )
                
                logger.info(f"Salvos {len(saved_products)} produtos no banco")
                
            except SQLAlchemyError as e:
                db.rollback()
                log_database_operation(
                    "INSERT/UPDATE", "products", 0, False
                )
                logger.error(f"Erro ao salvar produtos: {e}")
                raise
        
        return saved_products
    
    def _find_existing_product(self, db: Session, product_data: Dict) -> Optional[Product]:
        """
        Encontra produto existente baseado em URL ou ID externo.
        
        Args:
            db: Sessão do banco
            product_data: Dados do produto
            
        Returns:
            Produto existente ou None
        """
        url = product_data.get('url')
        external_id = product_data.get('external_id') or product_data.get('asin')
        site = product_data.get('site')
        
        # Buscar por URL primeiro
        if url:
            product = db.query(Product).filter(Product.url == url).first()
            if product:
                return product
        
        # Buscar por ID externo e site
        if external_id and site:
            product = db.query(Product).filter(
                and_(
                    Product.external_id == external_id,
                    Product.site == site
                )
            ).first()
            if product:
                return product
        
        return None
    
    async def _update_existing_product(self, db: Session, product: Product, 
                                     product_data: Dict, session_id: Optional[int]) -> Product:
        """
        Atualiza produto existente com novos dados.
        
        Args:
            db: Sessão do banco
            product: Produto existente
            product_data: Novos dados
            session_id: ID da sessão
            
        Returns:
            Produto atualizado
        """
        old_price = product.current_price
        new_price = product_data.get('price', 0.0)
        
        # Atualizar campos
        product.title = product_data.get('title', product.title)
        product.current_price = new_price
        product.original_price = product_data.get('original_price')
        product.image_url = product_data.get('image_url', product.image_url)
        product.rating = product_data.get('rating', product.rating)
        product.num_reviews = product_data.get('num_reviews', product.num_reviews)
        product.in_stock = product_data.get('in_stock', product.in_stock)
        product.free_shipping = product_data.get('free_shipping', product.free_shipping)
        product.last_updated = datetime.utcnow()
        
        # Se preço mudou, criar registro no histórico
        if abs(old_price - new_price) > 0.01:  # Diferença mínima para evitar ruído
            price_history = PriceHistory(
                product_id=product.id,
                price=new_price,
                original_price=product_data.get('original_price'),
                session_id=session_id
            )
            db.add(price_history)
            
            logger.info(f"Mudança de preço detectada: {product.title[:50]} - {old_price} -> {new_price}")
        
        return product
    
    async def get_products(self, filters: Optional[Dict] = None, 
                          limit: int = 100, offset: int = 0) -> List[Product]:
        """
        Busca produtos com filtros opcionais.
        
        Args:
            filters: Filtros a aplicar
            limit: Limite de resultados
            offset: Offset para paginação
            
        Returns:
            Lista de produtos
        """
        with self.get_session() as db:
            query = db.query(Product)
            
            if filters:
                if 'site' in filters:
                    query = query.filter(Product.site == filters['site'])
                
                if 'min_price' in filters:
                    query = query.filter(Product.current_price >= filters['min_price'])
                
                if 'max_price' in filters:
                    query = query.filter(Product.current_price <= filters['max_price'])
                
                if 'in_stock' in filters:
                    query = query.filter(Product.in_stock == filters['in_stock'])
                
                if 'search' in filters:
                    search_term = f"%{filters['search']}%"
                    query = query.filter(Product.title.ilike(search_term))
            
            products = query.order_by(desc(Product.last_updated)).offset(offset).limit(limit).all()
            
            log_database_operation("SELECT", "products", len(products), True)
            
            return products
    
    async def get_product_by_id(self, product_id: int) -> Optional[Product]:
        """
        Busca produto por ID.
        
        Args:
            product_id: ID do produto
            
        Returns:
            Produto ou None
        """
        with self.get_session() as db:
            return db.query(Product).filter(Product.id == product_id).first()
    
    # ==========================================
    # Operações com Histórico de Preços
    # ==========================================
    
    async def get_price_history(self, product_id: int, days: int = 30) -> List[PriceHistory]:
        """
        Obtém histórico de preços de um produto.
        
        Args:
            product_id: ID do produto
            days: Número de dias para buscar
            
        Returns:
            Lista de registros de histórico
        """
        with self.get_session() as db:
            cutoff_date = datetime.utcnow() - timedelta(days=days)
            
            history = db.query(PriceHistory).filter(
                and_(
                    PriceHistory.product_id == product_id,
                    PriceHistory.recorded_at >= cutoff_date
                )
            ).order_by(PriceHistory.recorded_at).all()
            
            return history
    
    async def get_price_changes(self, hours: int = 24) -> List[Tuple[Product, PriceHistory, PriceHistory]]:
        """
        Obtém produtos com mudanças de preço recentes.
        
        Args:
            hours: Número de horas para buscar
            
        Returns:
            Lista de tuplas (produto, preço_anterior, preço_atual)
        """
        with self.get_session() as db:
            cutoff_date = datetime.utcnow() - timedelta(hours=hours)
            
            # Query complexa para encontrar mudanças de preço
            recent_changes = db.query(PriceHistory).filter(
                PriceHistory.recorded_at >= cutoff_date
            ).all()
            
            changes = []
            for change in recent_changes:
                # Buscar preço anterior
                previous = db.query(PriceHistory).filter(
                    and_(
                        PriceHistory.product_id == change.product_id,
                        PriceHistory.recorded_at < change.recorded_at
                    )
                ).order_by(desc(PriceHistory.recorded_at)).first()
                
                if previous and abs(previous.price - change.price) > 0.01:
                    product = db.query(Product).filter(Product.id == change.product_id).first()
                    if product:
                        changes.append((product, previous, change))
            
            return changes
    
    # ==========================================
    # Operações com Sessões de Scraping
    # ==========================================
    
    async def create_scraping_session(self, session_data: Dict) -> ScrapingSession:
        """
        Cria nova sessão de scraping.
        
        Args:
            session_data: Dados da sessão
            
        Returns:
            Sessão criada
        """
        with self.get_session() as db:
            try:
                session = ScrapingSession(
                    session_name=session_data.get('session_name'),
                    site=session_data.get('site'),
                    search_term=session_data.get('search_term'),
                    filters_applied=json.dumps(session_data.get('filters_applied', {}))
                )
                
                db.add(session)
                db.commit()
                db.refresh(session)
                
                log_database_operation("INSERT", "scraping_sessions", 1, True)
                
                return session
                
            except SQLAlchemyError as e:
                db.rollback()
                log_database_operation("INSERT", "scraping_sessions", 0, False)
                logger.error(f"Erro ao criar sessão: {e}")
                raise
    
    async def update_scraping_session(self, session_id: int, updates: Dict) -> Optional[ScrapingSession]:
        """
        Atualiza sessão de scraping.
        
        Args:
            session_id: ID da sessão
            updates: Dados para atualizar
            
        Returns:
            Sessão atualizada ou None
        """
        with self.get_session() as db:
            try:
                session = db.query(ScrapingSession).filter(ScrapingSession.id == session_id).first()
                
                if not session:
                    return None
                
                # Atualizar campos
                for key, value in updates.items():
                    if hasattr(session, key):
                        setattr(session, key, value)
                
                # Calcular duração se completada
                if 'completed_at' in updates and session.started_at:
                    duration = (updates['completed_at'] - session.started_at).total_seconds()
                    session.duration_seconds = duration
                
                db.commit()
                db.refresh(session)
                
                log_database_operation("UPDATE", "scraping_sessions", 1, True)
                
                return session
                
            except SQLAlchemyError as e:
                db.rollback()
                log_database_operation("UPDATE", "scraping_sessions", 0, False)
                logger.error(f"Erro ao atualizar sessão: {e}")
                raise
    
    async def get_recent_sessions(self, limit: int = 10) -> List[ScrapingSession]:
        """
        Obtém sessões recentes.
        
        Args:
            limit: Limite de resultados
            
        Returns:
            Lista de sessões
        """
        with self.get_session() as db:
            sessions = db.query(ScrapingSession).order_by(
                desc(ScrapingSession.started_at)
            ).limit(limit).all()
            
            return sessions
    
    # ==========================================
    # Operações com Logs de E-mail
    # ==========================================
    
    async def log_email_sent(self, email_data: Dict) -> EmailLog:
        """
        Registra envio de e-mail.
        
        Args:
            email_data: Dados do e-mail
            
        Returns:
            Log criado
        """
        with self.get_session() as db:
            try:
                email_log = EmailLog(
                    recipients=json.dumps(email_data.get('recipients', [])),
                    subject=email_data.get('subject', ''),
                    email_type=email_data.get('email_type', 'unknown'),
                    products_count=email_data.get('products_count', 0),
                    has_attachments=email_data.get('has_attachments', False),
                    sent_successfully=email_data.get('sent_successfully', False),
                    error_message=email_data.get('error_message'),
                    session_id=email_data.get('session_id')
                )
                
                db.add(email_log)
                db.commit()
                db.refresh(email_log)
                
                log_database_operation("INSERT", "email_logs", 1, True)
                
                return email_log
                
            except SQLAlchemyError as e:
                db.rollback()
                log_database_operation("INSERT", "email_logs", 0, False)
                logger.error(f"Erro ao registrar e-mail: {e}")
                raise
    
    # ==========================================
    # Estatísticas e Relatórios
    # ==========================================
    
    async def get_statistics(self) -> Dict[str, Any]:
        """
        Obtém estatísticas gerais do sistema.
        
        Returns:
            Dicionário com estatísticas
        """
        with self.get_session() as db:
            stats = {
                'total_products': db.query(Product).count(),
                'products_in_stock': db.query(Product).filter(Product.in_stock == True).count(),
                'total_sessions': db.query(ScrapingSession).count(),
                'successful_sessions': db.query(ScrapingSession).filter(ScrapingSession.success == True).count(),
                'total_emails': db.query(EmailLog).count(),
                'successful_emails': db.query(EmailLog).filter(EmailLog.sent_successfully == True).count(),
                'price_records': db.query(PriceHistory).count()
            }
            
            # Estatísticas por site
            site_stats = db.query(
                Product.site,
                func.count(Product.id).label('count'),
                func.avg(Product.current_price).label('avg_price')
            ).group_by(Product.site).all()
            
            stats['by_site'] = {
                site: {'count': count, 'avg_price': float(avg_price or 0)}
                for site, count, avg_price in site_stats
            }
            
            return stats
    
    async def cleanup_old_data(self, days: int = 90):
        """
        Remove dados antigos do banco.
        
        Args:
            days: Número de dias para manter
        """
        with self.get_session() as db:
            try:
                cutoff_date = datetime.utcnow() - timedelta(days=days)
                
                # Remover histórico de preços antigo
                old_history = db.query(PriceHistory).filter(
                    PriceHistory.recorded_at < cutoff_date
                ).delete()
                
                # Remover sessões antigas
                old_sessions = db.query(ScrapingSession).filter(
                    ScrapingSession.started_at < cutoff_date
                ).delete()
                
                # Remover logs de e-mail antigos
                old_emails = db.query(EmailLog).filter(
                    EmailLog.sent_at < cutoff_date
                ).delete()
                
                db.commit()
                
                logger.info(f"Limpeza concluída: {old_history} históricos, {old_sessions} sessões, {old_emails} e-mails removidos")
                
            except SQLAlchemyError as e:
                db.rollback()
                logger.error(f"Erro na limpeza: {e}")
                raise
