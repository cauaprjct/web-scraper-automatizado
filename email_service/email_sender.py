"""
Serviço de Envio de E-mails
===========================

Este módulo implementa o serviço principal para envio de e-mails,
incluindo templates HTML, anexos e logging.

Autor: Seu Nome
Data: 2025-09-20
"""

import asyncio
import smtplib
import ssl
from datetime import datetime
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
from pathlib import Path
from typing import List, Dict, Optional, Any
import json
import csv
import io

from .simple_templates import SimpleEmailTemplates
from utils.logger import setup_logger, log_email_sent

logger = setup_logger(__name__)


class EmailService:
    """
    Serviço principal para envio de e-mails.
    
    Gerencia conexão SMTP, templates, anexos e logging
    de todos os e-mails enviados pelo sistema.
    """
    
    def __init__(self, settings):
        """
        Inicializa o serviço de e-mail.
        
        Args:
            settings: Configurações do sistema
        """
        self.settings = settings
        self.templates = SimpleEmailTemplates()
        
        # Configurações SMTP
        self.smtp_host = settings.email_host
        self.smtp_port = settings.email_port
        self.use_tls = settings.email_use_tls
        self.username = settings.email_user
        self.password = settings.email_password
        self.from_name = settings.email_from_name
        self.subject_prefix = settings.email_subject_prefix
        
        logger.info("EmailService inicializado")
    
    async def send_product_report(self, products: List[Dict], search_term: str, 
                                recipients: List[str], session_id: Optional[int] = None) -> bool:
        """
        Envia relatório de produtos por e-mail.
        
        Args:
            products: Lista de produtos encontrados
            search_term: Termo de busca usado
            recipients: Lista de destinatários
            session_id: ID da sessão de scraping
            
        Returns:
            True se enviado com sucesso
        """
        try:
            if not products:
                logger.warning("Nenhum produto para enviar por e-mail")
                return False
            
            # Gerar conteúdo do e-mail
            subject = f"{self.subject_prefix} Relatório de Produtos - {search_term}"
            html_content = self.templates.generate_product_report(
                products=products,
                search_term=search_term,
                total_found=len(products)
            )
            
            # Criar anexos
            attachments = []
            
            # Anexo CSV
            csv_data = self._create_csv_attachment(products)
            if csv_data:
                attachments.append({
                    'filename': f'produtos_{search_term}_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv',
                    'content': csv_data,
                    'content_type': 'text/csv'
                })
            
            # Anexo JSON
            json_data = self._create_json_attachment(products)
            if json_data:
                attachments.append({
                    'filename': f'produtos_{search_term}_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json',
                    'content': json_data,
                    'content_type': 'application/json'
                })
            
            # Enviar e-mail
            success = await self._send_email(
                recipients=recipients,
                subject=subject,
                html_content=html_content,
                attachments=attachments
            )
            
            # Log do envio
            log_email_sent(
                recipients=recipients,
                subject=subject,
                success=success
            )
            
            return success
            
        except Exception as e:
            logger.error(f"Erro ao enviar relatório de produtos: {e}")
            return False
    
    async def send_price_alert(self, price_changes: List[Dict], 
                             recipients: List[str]) -> bool:
        """
        Envia alerta de mudanças de preço.
        
        Args:
            price_changes: Lista de mudanças de preço
            recipients: Lista de destinatários
            
        Returns:
            True se enviado com sucesso
        """
        try:
            if not price_changes:
                return False
            
            subject = f"{self.subject_prefix} Alerta de Mudanças de Preço"
            html_content = self.templates.generate_price_alert(
                price_changes=price_changes
            )
            
            success = await self._send_email(
                recipients=recipients,
                subject=subject,
                html_content=html_content
            )
            
            log_email_sent(
                recipients=recipients,
                subject=subject,
                success=success
            )
            
            return success
            
        except Exception as e:
            logger.error(f"Erro ao enviar alerta de preços: {e}")
            return False
    
    async def send_daily_summary(self, summary_data: Dict, 
                               recipients: List[str]) -> bool:
        """
        Envia resumo diário das atividades.
        
        Args:
            summary_data: Dados do resumo
            recipients: Lista de destinatários
            
        Returns:
            True se enviado com sucesso
        """
        try:
            subject = f"{self.subject_prefix} Resumo Diário - {datetime.now().strftime('%d/%m/%Y')}"
            html_content = self.templates.generate_daily_summary(
                summary_data=summary_data
            )
            
            success = await self._send_email(
                recipients=recipients,
                subject=subject,
                html_content=html_content
            )
            
            log_email_sent(
                recipients=recipients,
                subject=subject,
                success=success
            )
            
            return success
            
        except Exception as e:
            logger.error(f"Erro ao enviar resumo diário: {e}")
            return False
    
    async def send_error_notification(self, error_details: Dict, 
                                    recipients: List[str]) -> bool:
        """
        Envia notificação de erro.
        
        Args:
            error_details: Detalhes do erro
            recipients: Lista de destinatários
            
        Returns:
            True se enviado com sucesso
        """
        try:
            subject = f"{self.subject_prefix} Erro no Sistema"
            html_content = self.templates.generate_error_notification(
                error_details=error_details
            )
            
            success = await self._send_email(
                recipients=recipients,
                subject=subject,
                html_content=html_content
            )
            
            log_email_sent(
                recipients=recipients,
                subject=subject,
                success=success
            )
            
            return success
            
        except Exception as e:
            logger.error(f"Erro ao enviar notificação de erro: {e}")
            return False
    
    async def _send_email(self, recipients: List[str], subject: str, 
                         html_content: str, attachments: Optional[List[Dict]] = None) -> bool:
        """
        Envia e-mail usando SMTP.
        
        Args:
            recipients: Lista de destinatários
            subject: Assunto do e-mail
            html_content: Conteúdo HTML
            attachments: Lista de anexos
            
        Returns:
            True se enviado com sucesso
        """
        try:
            # Validar configurações
            if not self.username or not self.password:
                logger.error("Credenciais de e-mail não configuradas")
                return False
            
            if not recipients:
                logger.error("Nenhum destinatário especificado")
                return False
            
            # Criar mensagem
            msg = MIMEMultipart('alternative')
            msg['From'] = f"{self.from_name} <{self.username}>"
            msg['To'] = ', '.join(recipients)
            msg['Subject'] = subject
            
            # Adicionar conteúdo HTML
            html_part = MIMEText(html_content, 'html', 'utf-8')
            msg.attach(html_part)
            
            # Adicionar anexos
            if attachments:
                for attachment in attachments:
                    self._add_attachment(msg, attachment)
            
            # Conectar e enviar
            context = ssl.create_default_context()
            
            with smtplib.SMTP(self.smtp_host, self.smtp_port) as server:
                if self.use_tls:
                    server.starttls(context=context)
                
                server.login(self.username, self.password)
                
                # Enviar para cada destinatário
                for recipient in recipients:
                    server.send_message(msg, to_addrs=[recipient])
            
            logger.info(f"E-mail enviado com sucesso para {len(recipients)} destinatários")
            return True
            
        except smtplib.SMTPException as e:
            logger.error(f"Erro SMTP ao enviar e-mail: {e}")
            return False
        except Exception as e:
            logger.error(f"Erro geral ao enviar e-mail: {e}")
            return False
    
    def _add_attachment(self, msg: MIMEMultipart, attachment: Dict):
        """
        Adiciona anexo ao e-mail.
        
        Args:
            msg: Mensagem de e-mail
            attachment: Dados do anexo
        """
        try:
            part = MIMEBase('application', 'octet-stream')
            
            if isinstance(attachment['content'], str):
                part.set_payload(attachment['content'].encode('utf-8'))
            else:
                part.set_payload(attachment['content'])
            
            encoders.encode_base64(part)
            
            part.add_header(
                'Content-Disposition',
                f'attachment; filename= {attachment["filename"]}'
            )
            
            msg.attach(part)
            
        except Exception as e:
            logger.error(f"Erro ao adicionar anexo: {e}")
    
    def _create_csv_attachment(self, products: List[Dict]) -> Optional[str]:
        """
        Cria anexo CSV com dados dos produtos.
        
        Args:
            products: Lista de produtos
            
        Returns:
            Conteúdo CSV como string
        """
        try:
            if not products:
                return None
            
            output = io.StringIO()
            
            # Definir campos para CSV
            fieldnames = [
                'title', 'price', 'original_price', 'url', 'site',
                'rating', 'num_reviews', 'free_shipping', 'in_stock'
            ]
            
            writer = csv.DictWriter(output, fieldnames=fieldnames)
            writer.writeheader()
            
            for product in products:
                # Filtrar apenas campos relevantes
                row = {field: product.get(field, '') for field in fieldnames}
                writer.writerow(row)
            
            return output.getvalue()
            
        except Exception as e:
            logger.error(f"Erro ao criar CSV: {e}")
            return None
    
    def _create_json_attachment(self, products: List[Dict]) -> Optional[str]:
        """
        Cria anexo JSON com dados dos produtos.
        
        Args:
            products: Lista de produtos
            
        Returns:
            Conteúdo JSON como string
        """
        try:
            if not products:
                return None
            
            # Limpar dados para JSON
            clean_products = []
            for product in products:
                clean_product = {}
                for key, value in product.items():
                    # Converter tipos não serializáveis
                    if isinstance(value, datetime):
                        clean_product[key] = value.isoformat()
                    else:
                        clean_product[key] = value
                clean_products.append(clean_product)
            
            return json.dumps(clean_products, ensure_ascii=False, indent=2)
            
        except Exception as e:
            logger.error(f"Erro ao criar JSON: {e}")
            return None
    
    def test_connection(self) -> bool:
        """
        Testa conexão SMTP.
        
        Returns:
            True se conexão bem-sucedida
        """
        try:
            context = ssl.create_default_context()
            
            with smtplib.SMTP(self.smtp_host, self.smtp_port) as server:
                if self.use_tls:
                    server.starttls(context=context)
                
                server.login(self.username, self.password)
            
            logger.info("Teste de conexão SMTP bem-sucedido")
            return True
            
        except Exception as e:
            logger.error(f"Falha no teste de conexão SMTP: {e}")
            return False
    
    def validate_settings(self) -> List[str]:
        """
        Valida configurações de e-mail.
        
        Returns:
            Lista de erros encontrados
        """
        errors = []
        
        if not self.smtp_host:
            errors.append("Host SMTP não configurado")
        
        if not self.smtp_port:
            errors.append("Porta SMTP não configurada")
        
        if not self.username:
            errors.append("Usuário de e-mail não configurado")
        
        if not self.password:
            errors.append("Senha de e-mail não configurada")
        
        return errors
