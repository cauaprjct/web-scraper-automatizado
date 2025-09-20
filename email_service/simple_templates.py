"""
Templates Simples de E-mail
==========================

Este módulo fornece templates HTML simples para e-mails,
sem dependência do Jinja2.

Autor: Seu Nome
Data: 2025-09-20
"""

from datetime import datetime
from typing import List, Dict, Any


class SimpleEmailTemplates:
    """
    Gerador de templates HTML simples para e-mails.
    
    Usa string formatting ao invés de engines de template
    para evitar dependências complexas.
    """
    
    def __init__(self):
        """Inicializa o gerador de templates."""
        self.base_style = """
        <style>
            body { font-family: Arial, sans-serif; margin: 0; padding: 20px; background-color: #f5f5f5; }
            .container { max-width: 800px; margin: 0 auto; background-color: white; padding: 20px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
            .header { background-color: #2c3e50; color: white; padding: 20px; border-radius: 8px 8px 0 0; margin: -20px -20px 20px -20px; }
            .header h1 { margin: 0; font-size: 24px; }
            .summary { background-color: #ecf0f1; padding: 15px; border-radius: 5px; margin: 20px 0; }
            .product { border: 1px solid #ddd; margin: 10px 0; padding: 15px; border-radius: 5px; }
            .product-title { font-weight: bold; color: #2c3e50; margin-bottom: 5px; }
            .product-price { font-size: 18px; color: #27ae60; font-weight: bold; }
            .product-site { color: #7f8c8d; font-size: 12px; }
            .footer { margin-top: 30px; padding-top: 20px; border-top: 1px solid #ddd; color: #7f8c8d; font-size: 12px; }
            .alert { background-color: #e74c3c; color: white; padding: 10px; border-radius: 5px; margin: 10px 0; }
            .success { background-color: #27ae60; color: white; padding: 10px; border-radius: 5px; margin: 10px 0; }
            .warning { background-color: #f39c12; color: white; padding: 10px; border-radius: 5px; margin: 10px 0; }
            table { width: 100%; border-collapse: collapse; margin: 20px 0; }
            th, td { padding: 10px; text-align: left; border-bottom: 1px solid #ddd; }
            th { background-color: #f8f9fa; }
        </style>
        """
    
    def generate_product_report(self, products: List[Dict], search_term: str, total_found: int) -> str:
        """
        Gera relatório HTML de produtos.
        
        Args:
            products: Lista de produtos
            search_term: Termo de busca
            total_found: Total de produtos encontrados
            
        Returns:
            HTML do relatório
        """
        # Calcular estatísticas
        if products:
            prices = [p.get('price', 0) for p in products if p.get('price', 0) > 0]
            min_price = min(prices) if prices else 0
            max_price = max(prices) if prices else 0
            avg_price = sum(prices) / len(prices) if prices else 0
        else:
            min_price = max_price = avg_price = 0
        
        # Contar por site
        sites = {}
        for product in products:
            site = product.get('site', 'Desconhecido')
            sites[site] = sites.get(site, 0) + 1
        
        # Gerar HTML dos produtos
        products_html = ""
        for i, product in enumerate(products[:20], 1):  # Limitar a 20 produtos no e-mail
            title = product.get('title', 'Sem título')[:100]
            price = product.get('price', 0)
            original_price = product.get('original_price')
            url = product.get('url', '#')
            site = product.get('site', 'N/A')
            rating = product.get('rating', 0)
            
            price_html = f"R$ {price:.2f}"
            if original_price and original_price > price:
                discount = ((original_price - price) / original_price) * 100
                price_html += f" <span style='text-decoration: line-through; color: #7f8c8d;'>R$ {original_price:.2f}</span>"
                price_html += f" <span style='color: #e74c3c;'>(-{discount:.0f}%)</span>"
            
            rating_html = ""
            if rating > 0:
                stars = "★" * int(rating) + "☆" * (5 - int(rating))
                rating_html = f"<div style='color: #f39c12;'>{stars} ({rating:.1f})</div>"
            
            products_html += f"""
            <div class="product">
                <div class="product-title">{i}. {title}</div>
                <div class="product-price">{price_html}</div>
                {rating_html}
                <div class="product-site">{site} | <a href="{url}" target="_blank">Ver produto</a></div>
            </div>
            """
        
        # Gerar HTML dos sites
        sites_html = ""
        for site, count in sites.items():
            sites_html += f"<li>{site}: {count} produtos</li>"
        
        # Template principal
        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <title>Relatório de Produtos</title>
            {self.base_style}
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>🛒 Relatório de Produtos</h1>
                    <p>Busca: <strong>{search_term}</strong></p>
                    <p>Data: {datetime.now().strftime('%d/%m/%Y às %H:%M')}</p>
                </div>
                
                <div class="summary">
                    <h2>📊 Resumo</h2>
                    <ul>
                        <li><strong>Total encontrado:</strong> {total_found} produtos</li>
                        <li><strong>Exibindo:</strong> {min(len(products), 20)} produtos</li>
                        <li><strong>Menor preço:</strong> R$ {min_price:.2f}</li>
                        <li><strong>Maior preço:</strong> R$ {max_price:.2f}</li>
                        <li><strong>Preço médio:</strong> R$ {avg_price:.2f}</li>
                    </ul>
                    
                    <h3>🌐 Produtos por site:</h3>
                    <ul>{sites_html}</ul>
                </div>
                
                <h2>🛒 Produtos Encontrados</h2>
                {products_html}
                
                {self._get_footer()}
            </div>
        </body>
        </html>
        """
        
        return html
    
    def generate_price_alert(self, price_changes: List[Dict]) -> str:
        """
        Gera alerta HTML de mudanças de preço.
        
        Args:
            price_changes: Lista de mudanças de preço
            
        Returns:
            HTML do alerta
        """
        changes_html = ""
        for change in price_changes:
            product = change.get('product', {})
            old_price = change.get('old_price', 0)
            new_price = change.get('new_price', 0)
            
            title = product.get('title', 'Produto')[:80]
            url = product.get('url', '#')
            site = product.get('site', 'N/A')
            
            if new_price < old_price:
                change_type = "success"
                change_icon = "🔽"
                change_text = "DESCONTO"
            else:
                change_type = "alert"
                change_icon = "🔼"
                change_text = "AUMENTO"
            
            percent_change = abs(((new_price - old_price) / old_price) * 100)
            
            changes_html += f"""
            <div class="{change_type}">
                <h3>{change_icon} {change_text}</h3>
                <div><strong>{title}</strong></div>
                <div>Preço anterior: R$ {old_price:.2f}</div>
                <div>Preço atual: R$ {new_price:.2f}</div>
                <div>Variação: {percent_change:.1f}%</div>
                <div>Site: {site} | <a href="{url}" target="_blank" style="color: white;">Ver produto</a></div>
            </div>
            """
        
        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <title>Alerta de Preços</title>
            {self.base_style}
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>🚨 Alerta de Mudanças de Preço</h1>
                    <p>Data: {datetime.now().strftime('%d/%m/%Y às %H:%M')}</p>
                </div>
                
                <p>Detectamos {len(price_changes)} mudança(s) de preço nos produtos monitorados:</p>
                
                {changes_html}
                
                {self._get_footer()}
            </div>
        </body>
        </html>
        """
        
        return html
    
    def generate_daily_summary(self, summary_data: Dict) -> str:
        """
        Gera resumo HTML diário.
        
        Args:
            summary_data: Dados do resumo
            
        Returns:
            HTML do resumo
        """
        stats = summary_data.get('statistics', {})
        sessions = summary_data.get('recent_sessions', [])
        
        # Estatísticas
        stats_html = f"""
        <table>
            <tr><th>Métrica</th><th>Valor</th></tr>
            <tr><td>Total de produtos</td><td>{stats.get('total_products', 0)}</td></tr>
            <tr><td>Produtos em estoque</td><td>{stats.get('products_in_stock', 0)}</td></tr>
            <tr><td>Sessões de scraping</td><td>{stats.get('total_sessions', 0)}</td></tr>
            <tr><td>Sessões bem-sucedidas</td><td>{stats.get('successful_sessions', 0)}</td></tr>
            <tr><td>E-mails enviados</td><td>{stats.get('total_emails', 0)}</td></tr>
        </table>
        """
        
        # Sessões recentes
        sessions_html = ""
        for session in sessions[:5]:
            status = "✅" if session.get('success') else "❌"
            sessions_html += f"""
            <tr>
                <td>{status}</td>
                <td>{session.get('site', 'N/A')}</td>
                <td>{session.get('search_term', 'N/A')}</td>
                <td>{session.get('products_found', 0)}</td>
                <td>{session.get('started_at', 'N/A')}</td>
            </tr>
            """
        
        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <title>Resumo Diário</title>
            {self.base_style}
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>📈 Resumo Diário</h1>
                    <p>Data: {datetime.now().strftime('%d/%m/%Y')}</p>
                </div>
                
                <h2>📊 Estatísticas Gerais</h2>
                {stats_html}
                
                <h2>🔄 Sessões Recentes</h2>
                <table>
                    <tr>
                        <th>Status</th>
                        <th>Site</th>
                        <th>Busca</th>
                        <th>Produtos</th>
                        <th>Data</th>
                    </tr>
                    {sessions_html}
                </table>
                
                {self._get_footer()}
            </div>
        </body>
        </html>
        """
        
        return html
    
    def generate_error_notification(self, error_details: Dict) -> str:
        """
        Gera notificação HTML de erro.
        
        Args:
            error_details: Detalhes do erro
            
        Returns:
            HTML da notificação
        """
        error_type = error_details.get('type', 'Erro desconhecido')
        error_message = error_details.get('message', 'Nenhuma mensagem disponível')
        error_time = error_details.get('timestamp', datetime.now().isoformat())
        context = error_details.get('context', {})
        
        context_html = ""
        if context:
            context_html = "<h3>Contexto:</h3><ul>"
            for key, value in context.items():
                context_html += f"<li><strong>{key}:</strong> {value}</li>"
            context_html += "</ul>"
        
        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <title>Erro no Sistema</title>
            {self.base_style}
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>⚠️ Erro no Sistema</h1>
                    <p>Data: {datetime.now().strftime('%d/%m/%Y às %H:%M')}</p>
                </div>
                
                <div class="alert">
                    <h2>Tipo do Erro</h2>
                    <p>{error_type}</p>
                    
                    <h2>Mensagem</h2>
                    <p>{error_message}</p>
                    
                    <h2>Horário</h2>
                    <p>{error_time}</p>
                </div>
                
                {context_html}
                
                <p>Por favor, verifique os logs do sistema para mais detalhes.</p>
                
                {self._get_footer()}
            </div>
        </body>
        </html>
        """
        
        return html
    
    def _get_footer(self) -> str:
        """
        Retorna rodapé padrão para e-mails.
        
        Returns:
            HTML do rodapé
        """
        return f"""
        <div class="footer">
            <p>🕷️ Este e-mail foi gerado automaticamente pelo Web Scraper Automatizado.</p>
            <p>Data de geração: {datetime.now().strftime('%d/%m/%Y às %H:%M:%S')}</p>
            <p>Para parar de receber estes e-mails, entre em contato com o administrador do sistema.</p>
        </div>
        """
