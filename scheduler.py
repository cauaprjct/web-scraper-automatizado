#!/usr/bin/env python3
"""
Agendador de Scraping
====================

Sistema de agendamento automático para execução de scraping
em horários pré-definidos usando APScheduler.

Autor: Seu Nome
Data: 2025-09-20
"""

import asyncio
import signal
import sys
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Dict, Any

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger
from apscheduler.events import EVENT_JOB_EXECUTED, EVENT_JOB_ERROR

sys.path.append(str(Path(__file__).parent))

from config.settings import Settings
from database.database import DatabaseManager
from scrapers import ScraperFactory
from email_service.email_sender import EmailService
from utils.logger import setup_logger, log_scheduler_job

logger = setup_logger(__name__)


class ScrapingScheduler:
    """
    Agendador principal para execução automática de scraping.
    
    Gerencia jobs de scraping, envio de e-mails e manutenção
    do sistema usando APScheduler.
    """
    
    def __init__(self):
        """
        Inicializa o agendador.
        """
        self.settings = Settings()
        self.scheduler = AsyncIOScheduler()
        self.db_manager = None
        self.email_service = None
        self.running = False
        
        # Configurar listeners de eventos
        self.scheduler.add_listener(
            self._job_executed_listener,
            EVENT_JOB_EXECUTED
        )
        
        self.scheduler.add_listener(
            self._job_error_listener,
            EVENT_JOB_ERROR
        )
        
        logger.info("ScrapingScheduler inicializado")
    
    async def initialize(self):
        """
        Inicializa dependências e configura jobs.
        """
        try:
            # Inicializar banco de dados
            self.db_manager = DatabaseManager(self.settings.database_url)
            await self.db_manager.initialize()
            
            # Inicializar serviço de e-mail
            self.email_service = EmailService(self.settings)
            
            # Configurar jobs padrão
            await self._setup_default_jobs()
            
            logger.info("Agendador inicializado com sucesso")
            
        except Exception as e:
            logger.error(f"Erro ao inicializar agendador: {e}")
            raise
    
    async def _setup_default_jobs(self):
        """
        Configura jobs padrão do sistema.
        """
        # Job de scraping diário (se habilitado)
        if self.settings.enable_scheduling:
            hour, minute = map(int, self.settings.daily_execution_time.split(':'))
            
            self.scheduler.add_job(
                self._daily_scraping_job,
                CronTrigger(hour=hour, minute=minute),
                id='daily_scraping',
                name='Scraping Diário Automático',
                replace_existing=True
            )
            
            log_scheduler_job(
                'daily_scraping',
                'SCHEDULED',
                f'{hour:02d}:{minute:02d} diário'
            )
        
        # Job de limpeza semanal
        self.scheduler.add_job(
            self._weekly_cleanup_job,
            CronTrigger(day_of_week=0, hour=2, minute=0),  # Domingo às 2h
            id='weekly_cleanup',
            name='Limpeza Semanal',
            replace_existing=True
        )
        
        # Job de resumo diário
        if self.settings.send_daily_summary:
            self.scheduler.add_job(
                self._daily_summary_job,
                CronTrigger(hour=18, minute=0),  # 18h todos os dias
                id='daily_summary',
                name='Resumo Diário',
                replace_existing=True
            )
        
        # Job de monitoramento de preços (a cada 4 horas)
        self.scheduler.add_job(
            self._price_monitoring_job,
            IntervalTrigger(hours=4),
            id='price_monitoring',
            name='Monitoramento de Preços',
            replace_existing=True
        )
        
        logger.info("Jobs padrão configurados")
    
    async def _daily_scraping_job(self):
        """
        Job de scraping diário automático.
        """
        logger.info("Iniciando scraping diário automático")
        
        try:
            # Lista de buscas padrão
            default_searches = [
                {'site': 'amazon', 'search': 'notebook', 'max_results': 30},
                {'site': 'mercadolivre', 'search': 'smartphone', 'max_results': 30},
                {'site': 'ebay', 'search': 'tablet', 'max_results': 20}
            ]
            
            all_products = []
            
            for search_config in default_searches:
                try:
                    # Criar scraper
                    scraper = ScraperFactory.create_scraper(
                        search_config['site'],
                        self.settings
                    )
                    
                    # Executar scraping
                    products = await scraper.search_products(
                        search_config['search'],
                        max_results=search_config['max_results']
                    )
                    
                    if products:
                        # Criar sessão
                        session_data = {
                            'session_name': f'Agendado - {search_config["search"]}',
                            'site': search_config['site'],
                            'search_term': search_config['search'],
                            'filters_applied': {'max_results': search_config['max_results']}
                        }
                        
                        session = await self.db_manager.create_scraping_session(session_data)
                        
                        # Salvar produtos
                        saved_products = await self.db_manager.save_products(
                            products, session.id
                        )
                        
                        # Atualizar sessão
                        await self.db_manager.update_scraping_session(
                            session.id,
                            {
                                'products_found': len(products),
                                'products_saved': len(saved_products),
                                'success': True,
                                'completed_at': datetime.utcnow()
                            }
                        )
                        
                        all_products.extend(products)
                        
                        logger.info(
                            f"Scraping {search_config['site']} - {search_config['search']}: "
                            f"{len(products)} produtos"
                        )
                
                except Exception as e:
                    logger.error(f"Erro no scraping {search_config}: {e}")
                    continue
            
            # Enviar relatório por e-mail
            if all_products and self.settings.email_recipients:
                await self.email_service.send_product_report(
                    products=all_products,
                    search_term="Scraping Diário Automático",
                    recipients=self.settings.email_recipients
                )
            
            log_scheduler_job('daily_scraping', 'COMPLETED')
            logger.info(f"Scraping diário concluído: {len(all_products)} produtos")
            
        except Exception as e:
            log_scheduler_job('daily_scraping', 'FAILED')
            logger.error(f"Erro no scraping diário: {e}")
    
    async def _weekly_cleanup_job(self):
        """
        Job de limpeza semanal de dados antigos.
        """
        logger.info("Iniciando limpeza semanal")
        
        try:
            await self.db_manager.cleanup_old_data(days=90)
            
            log_scheduler_job('weekly_cleanup', 'COMPLETED')
            logger.info("Limpeza semanal concluída")
            
        except Exception as e:
            log_scheduler_job('weekly_cleanup', 'FAILED')
            logger.error(f"Erro na limpeza semanal: {e}")
    
    async def _daily_summary_job(self):
        """
        Job de envio de resumo diário.
        """
        logger.info("Gerando resumo diário")
        
        try:
            # Obter estatísticas
            stats = await self.db_manager.get_statistics()
            recent_sessions = await self.db_manager.get_recent_sessions(5)
            
            summary_data = {
                'statistics': stats,
                'recent_sessions': [session.to_dict() for session in recent_sessions]
            }
            
            # Enviar resumo
            if self.settings.email_recipients:
                await self.email_service.send_daily_summary(
                    summary_data=summary_data,
                    recipients=self.settings.email_recipients
                )
            
            log_scheduler_job('daily_summary', 'COMPLETED')
            logger.info("Resumo diário enviado")
            
        except Exception as e:
            log_scheduler_job('daily_summary', 'FAILED')
            logger.error(f"Erro no resumo diário: {e}")
    
    async def _price_monitoring_job(self):
        """
        Job de monitoramento de mudanças de preço.
        """
        logger.info("Verificando mudanças de preço")
        
        try:
            # Obter mudanças de preço das últimas 4 horas
            price_changes = await self.db_manager.get_price_changes(hours=4)
            
            if price_changes:
                # Preparar dados para e-mail
                changes_data = []
                for product, old_price, new_price in price_changes:
                    changes_data.append({
                        'product': product.to_dict(),
                        'old_price': old_price.price,
                        'new_price': new_price.price
                    })
                
                # Enviar alerta
                if self.settings.email_recipients:
                    await self.email_service.send_price_alert(
                        price_changes=changes_data,
                        recipients=self.settings.email_recipients
                    )
                
                logger.info(f"Alerta de preços enviado: {len(price_changes)} mudanças")
            
            log_scheduler_job('price_monitoring', 'COMPLETED')
            
        except Exception as e:
            log_scheduler_job('price_monitoring', 'FAILED')
            logger.error(f"Erro no monitoramento de preços: {e}")
    
    def _job_executed_listener(self, event):
        """
        Listener para jobs executados com sucesso.
        
        Args:
            event: Evento do job
        """
        job_id = event.job_id
        logger.info(f"Job '{job_id}' executado com sucesso")
    
    def _job_error_listener(self, event):
        """
        Listener para jobs com erro.
        
        Args:
            event: Evento do job
        """
        job_id = event.job_id
        exception = event.exception
        logger.error(f"Job '{job_id}' falhou: {exception}")
    
    def add_custom_job(self, job_config: Dict[str, Any]) -> str:
        """
        Adiciona job customizado.
        
        Args:
            job_config: Configuração do job
            
        Returns:
            ID do job criado
        """
        try:
            job = self.scheduler.add_job(**job_config)
            logger.info(f"Job customizado adicionado: {job.id}")
            return job.id
            
        except Exception as e:
            logger.error(f"Erro ao adicionar job customizado: {e}")
            raise
    
    def remove_job(self, job_id: str) -> bool:
        """
        Remove job do agendador.
        
        Args:
            job_id: ID do job
            
        Returns:
            True se removido com sucesso
        """
        try:
            self.scheduler.remove_job(job_id)
            logger.info(f"Job removido: {job_id}")
            return True
            
        except Exception as e:
            logger.error(f"Erro ao remover job {job_id}: {e}")
            return False
    
    def get_jobs(self) -> List[Dict[str, Any]]:
        """
        Retorna lista de jobs ativos.
        
        Returns:
            Lista de jobs
        """
        jobs = []
        
        for job in self.scheduler.get_jobs():
            jobs.append({
                'id': job.id,
                'name': job.name,
                'next_run': job.next_run_time.isoformat() if job.next_run_time else None,
                'trigger': str(job.trigger)
            })
        
        return jobs
    
    async def start(self):
        """
        Inicia o agendador.
        """
        try:
            await self.initialize()
            
            self.scheduler.start()
            self.running = True
            
            logger.info("Agendador iniciado")
            logger.info(f"Jobs ativos: {len(self.scheduler.get_jobs())}")
            
            # Listar jobs
            for job in self.scheduler.get_jobs():
                next_run = job.next_run_time.strftime('%d/%m/%Y %H:%M:%S') if job.next_run_time else 'N/A'
                logger.info(f"  - {job.name} (ID: {job.id}) - Próxima execução: {next_run}")
            
        except Exception as e:
            logger.error(f"Erro ao iniciar agendador: {e}")
            raise
    
    async def stop(self):
        """
        Para o agendador.
        """
        if self.running:
            self.scheduler.shutdown(wait=True)
            self.running = False
            logger.info("Agendador parado")
    
    async def run_forever(self):
        """
        Executa o agendador indefinidamente.
        """
        await self.start()
        
        try:
            # Aguardar sinal de interrupção
            while self.running:
                await asyncio.sleep(1)
                
        except KeyboardInterrupt:
            logger.info("Interrupção recebida")
        
        finally:
            await self.stop()


def signal_handler(signum, frame):
    """
    Handler para sinais do sistema.
    
    Args:
        signum: Número do sinal
        frame: Frame atual
    """
    logger.info(f"Sinal {signum} recebido, parando agendador...")
    sys.exit(0)


async def main():
    """
    Função principal do agendador.
    """
    # Configurar handlers de sinal
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # Criar e executar agendador
    scheduler = ScrapingScheduler()
    
    try:
        await scheduler.run_forever()
    except Exception as e:
        logger.error(f"Erro fatal no agendador: {e}")
        sys.exit(1)


if __name__ == "__main__":
    print("🕷️ Web Scraper Automatizado - Agendador")
    print("="*50)
    print("Iniciando sistema de agendamento...")
    print("Pressione Ctrl+C para parar")
    print("="*50)
    
    asyncio.run(main())
