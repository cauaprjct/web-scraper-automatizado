#!/usr/bin/env python3
"""
Exemplos de Uso do Web Scraper
==============================

Este arquivo contém exemplos práticos de como usar
o sistema de web scraping automatizado.

Autor: Seu Nome
Data: 2025-09-20
"""

import asyncio
import json
from datetime import datetime
from pathlib import Path

from config.settings import Settings
from scrapers import ScraperFactory
from database.database import DatabaseManager
from email_service.email_sender import EmailService
from utils.logger import setup_logger

logger = setup_logger(__name__)


async def exemplo_scraping_basico():
    """
    Exemplo básico de scraping.
    """
    print("🕷️ Exemplo 1: Scraping Básico")
    print("="*50)
    
    # Carregar configurações
    settings = Settings()
    
    # Criar scraper para Amazon
    scraper = ScraperFactory.create_scraper('amazon', settings)
    
    try:
        # Buscar produtos
        produtos = await scraper.search_products(
            search_term="notebook",
            max_results=5,
            max_price=3000
        )
        
        print(f"Encontrados {len(produtos)} produtos:")
        
        for i, produto in enumerate(produtos, 1):
            print(f"{i}. {produto['title'][:50]}...")
            print(f"   Preço: R$ {produto['price']:.2f}")
            print(f"   Site: {produto['site']}")
            print(f"   URL: {produto['url'][:50]}...")
            print()
    
    except Exception as e:
        print(f"Erro: {e}")


async def exemplo_multiplos_sites():
    """
    Exemplo de scraping em múltiplos sites.
    """
    print("🌐 Exemplo 2: Múltiplos Sites")
    print("="*50)
    
    settings = Settings()
    sites = ['amazon', 'mercadolivre', 'ebay']
    termo_busca = "smartphone"
    
    todos_produtos = []
    
    for site in sites:
        try:
            print(f"Buscando em {site}...")
            
            scraper = ScraperFactory.create_scraper(site, settings)
            produtos = await scraper.search_products(
                search_term=termo_busca,
                max_results=3
            )
            
            todos_produtos.extend(produtos)
            print(f"  {len(produtos)} produtos encontrados")
        
        except Exception as e:
            print(f"  Erro em {site}: {e}")
    
    print(f"\nTotal: {len(todos_produtos)} produtos de todos os sites")
    
    # Agrupar por site
    por_site = {}
    for produto in todos_produtos:
        site = produto['site']
        if site not in por_site:
            por_site[site] = []
        por_site[site].append(produto)
    
    print("\nResumo por site:")
    for site, produtos in por_site.items():
        precos = [p['price'] for p in produtos if p['price'] > 0]
        if precos:
            preco_medio = sum(precos) / len(precos)
            print(f"  {site}: {len(produtos)} produtos, preço médio: R$ {preco_medio:.2f}")


async def exemplo_com_banco_dados():
    """
    Exemplo usando banco de dados.
    """
    print("🗄️ Exemplo 3: Com Banco de Dados")
    print("="*50)
    
    settings = Settings()
    
    # Inicializar banco
    db_manager = DatabaseManager(settings.database_url)
    await db_manager.initialize()
    
    # Criar scraper
    scraper = ScraperFactory.create_scraper('amazon', settings)
    
    try:
        # Buscar produtos
        produtos = await scraper.search_products(
            search_term="tablet",
            max_results=5
        )
        
        if produtos:
            # Criar sessão de scraping
            session_data = {
                'session_name': 'Exemplo - Tablets',
                'site': 'amazon',
                'search_term': 'tablet',
                'filters_applied': {'max_results': 5}
            }
            
            session = await db_manager.create_scraping_session(session_data)
            print(f"Sessão criada: ID {session.id}")
            
            # Salvar produtos
            produtos_salvos = await db_manager.save_products(produtos, session.id)
            print(f"Salvos {len(produtos_salvos)} produtos no banco")
            
            # Atualizar sessão
            await db_manager.update_scraping_session(
                session.id,
                {
                    'products_found': len(produtos),
                    'products_saved': len(produtos_salvos),
                    'success': True,
                    'completed_at': datetime.utcnow()
                }
            )
            
            # Obter estatísticas
            stats = await db_manager.get_statistics()
            print(f"\nEstatísticas do banco:")
            print(f"  Total de produtos: {stats['total_products']}")
            print(f"  Total de sessões: {stats['total_sessions']}")
    
    except Exception as e:
        print(f"Erro: {e}")


async def exemplo_com_email():
    """
    Exemplo com envio de e-mail.
    """
    print("📧 Exemplo 4: Com E-mail")
    print("="*50)
    
    settings = Settings()
    
    # Verificar se e-mail está configurado
    if not settings.email_user or not settings.email_recipients:
        print("E-mail não configurado. Configure as variáveis:")
        print("  EMAIL_USER=seu-email@gmail.com")
        print("  EMAIL_PASSWORD=sua-senha")
        print("  EMAIL_RECIPIENTS=destinatario@email.com")
        return
    
    # Criar serviço de e-mail
    email_service = EmailService(settings)
    
    # Testar conexão
    if not email_service.test_connection():
        print("Falha na conexão com servidor de e-mail")
        return
    
    print("Conexão de e-mail OK")
    
    # Buscar produtos
    scraper = ScraperFactory.create_scraper('mercadolivre', settings)
    
    try:
        produtos = await scraper.search_products(
            search_term="mouse gamer",
            max_results=10,
            max_price=200
        )
        
        if produtos:
            # Enviar relatório
            sucesso = await email_service.send_product_report(
                products=produtos,
                search_term="mouse gamer",
                recipients=settings.email_recipients
            )
            
            if sucesso:
                print(f"E-mail enviado com {len(produtos)} produtos!")
            else:
                print("Falha ao enviar e-mail")
        else:
            print("Nenhum produto encontrado")
    
    except Exception as e:
        print(f"Erro: {e}")


async def exemplo_filtros_avancados():
    """
    Exemplo com filtros avançados.
    """
    print("🔍 Exemplo 5: Filtros Avançados")
    print("="*50)
    
    settings = Settings()
    scraper = ScraperFactory.create_scraper('amazon', settings)
    
    # Diferentes combinações de filtros
    filtros_exemplos = [
        {
            'nome': 'Notebooks baratos',
            'filtros': {
                'search_term': 'notebook',
                'max_price': 2000,
                'max_results': 5
            }
        },
        {
            'nome': 'Smartphones premium',
            'filtros': {
                'search_term': 'smartphone',
                'min_price': 1000,
                'max_price': 3000,
                'max_results': 5
            }
        },
        {
            'nome': 'Tablets com boa avaliação',
            'filtros': {
                'search_term': 'tablet',
                'min_rating': 4.0,
                'max_results': 5
            }
        }
    ]
    
    for exemplo in filtros_exemplos:
        print(f"\n{exemplo['nome']}:")
        
        try:
            filtros = exemplo['filtros'].copy()
            search_term = filtros.pop('search_term')
            
            produtos = await scraper.search_products(search_term, **filtros)
            
            if produtos:
                precos = [p['price'] for p in produtos if p['price'] > 0]
                if precos:
                    print(f"  {len(produtos)} produtos encontrados")
                    print(f"  Preço mínimo: R$ {min(precos):.2f}")
                    print(f"  Preço máximo: R$ {max(precos):.2f}")
                    print(f"  Preço médio: R$ {sum(precos)/len(precos):.2f}")
            else:
                print("  Nenhum produto encontrado")
        
        except Exception as e:
            print(f"  Erro: {e}")


async def exemplo_monitoramento_precos():
    """
    Exemplo de monitoramento de preços.
    """
    print("💰 Exemplo 6: Monitoramento de Preços")
    print("="*50)
    
    settings = Settings()
    db_manager = DatabaseManager(settings.database_url)
    await db_manager.initialize()
    
    # Simular duas execuções de scraping para o mesmo produto
    scraper = ScraperFactory.create_scraper('amazon', settings)
    
    try:
        # Primeira execução
        print("Primeira execução de scraping...")
        produtos1 = await scraper.search_products(
            search_term="mouse",
            max_results=3
        )
        
        if produtos1:
            session1 = await db_manager.create_scraping_session({
                'session_name': 'Monitoramento - Execução 1',
                'site': 'amazon',
                'search_term': 'mouse'
            })
            
            await db_manager.save_products(produtos1, session1.id)
            print(f"  Salvos {len(produtos1)} produtos")
            
            # Aguardar um pouco (simular tempo)
            await asyncio.sleep(2)
            
            # Segunda execução
            print("\nSegunda execução de scraping...")
            produtos2 = await scraper.search_products(
                search_term="mouse",
                max_results=3
            )
            
            if produtos2:
                session2 = await db_manager.create_scraping_session({
                    'session_name': 'Monitoramento - Execução 2',
                    'site': 'amazon',
                    'search_term': 'mouse'
                })
                
                await db_manager.save_products(produtos2, session2.id)
                print(f"  Salvos {len(produtos2)} produtos")
                
                # Verificar mudanças de preço
                print("\nVerificando mudanças de preço...")
                mudancas = await db_manager.get_price_changes(hours=1)
                
                if mudancas:
                    print(f"Encontradas {len(mudancas)} mudanças de preço:")
                    for produto, preco_anterior, preco_atual in mudancas:
                        variacao = preco_atual.price - preco_anterior.price
                        print(f"  {produto.title[:40]}...")
                        print(f"    {preco_anterior.price:.2f} -> {preco_atual.price:.2f} (R$ {variacao:+.2f})")
                else:
                    print("Nenhuma mudança de preço detectada")
    
    except Exception as e:
        print(f"Erro: {e}")


def exemplo_configuracoes():
    """
    Exemplo de uso de configurações.
    """
    print("⚙️ Exemplo 7: Configurações")
    print("="*50)
    
    # Carregar configurações
    settings = Settings()
    
    print("Configurações atuais:")
    print(f"  App: {settings.app_name} v{settings.app_version}")
    print(f"  Debug: {settings.debug}")
    print(f"  Banco: {settings.database_url}")
    print(f"  Delay de scraping: {settings.scraping_delay}s")
    print(f"  Máx tentativas: {settings.max_retries}")
    print(f"  Timeout: {settings.request_timeout}s")
    
    print("\nConfigurações de e-mail:")
    print(f"  Host: {settings.email_host}:{settings.email_port}")
    print(f"  TLS: {settings.email_use_tls}")
    print(f"  Usuário: {settings.email_user}")
    print(f"  Destinatários: {len(settings.email_recipients)}")
    
    print("\nSites suportados:")
    sites = ScraperFactory.get_supported_sites()
    for site in sites:
        if site not in ['mercado_livre', 'ml']:  # Evitar aliases
            config = settings.get_site_config(site)
            print(f"  {site}: {config.get('base_url', 'N/A')}")
    
    # Validar configurações
    print("\nValidação:")
    missing = settings.validate_required_settings()
    if missing:
        print(f"  Configurações faltando: {', '.join(missing)}")
    else:
        print("  Todas as configurações obrigatórias estão presentes")


async def exemplo_exportar_dados():
    """
    Exemplo de exportação de dados.
    """
    print("💾 Exemplo 8: Exportar Dados")
    print("="*50)
    
    settings = Settings()
    scraper = ScraperFactory.create_scraper('mercadolivre', settings)
    
    try:
        # Buscar produtos
        produtos = await scraper.search_products(
            search_term="headset",
            max_results=10
        )
        
        if produtos:
            # Exportar para JSON
            json_file = Path('produtos_headset.json')
            with open(json_file, 'w', encoding='utf-8') as f:
                json.dump(produtos, f, ensure_ascii=False, indent=2)
            print(f"Dados exportados para {json_file}")
            
            # Exportar para CSV
            import csv
            csv_file = Path('produtos_headset.csv')
            
            with open(csv_file, 'w', newline='', encoding='utf-8') as f:
                if produtos:
                    fieldnames = ['title', 'price', 'site', 'rating', 'url']
                    writer = csv.DictWriter(f, fieldnames=fieldnames)
                    writer.writeheader()
                    
                    for produto in produtos:
                        row = {field: produto.get(field, '') for field in fieldnames}
                        writer.writerow(row)
            
            print(f"Dados exportados para {csv_file}")
            
            # Estatísticas rápidas
            precos = [p['price'] for p in produtos if p['price'] > 0]
            if precos:
                print(f"\nEstatísticas:")
                print(f"  Total de produtos: {len(produtos)}")
                print(f"  Preço médio: R$ {sum(precos)/len(precos):.2f}")
                print(f"  Preço mínimo: R$ {min(precos):.2f}")
                print(f"  Preço máximo: R$ {max(precos):.2f}")
    
    except Exception as e:
        print(f"Erro: {e}")


async def main():
    """
    Função principal que executa todos os exemplos.
    """
    print("🕷️ Web Scraper Automatizado - Exemplos")
    print("="*60)
    print("Este arquivo demonstra diferentes formas de usar o sistema.")
    print("Alguns exemplos podem falhar se as configurações não estiverem completas.")
    print("="*60)
    
    exemplos = [
        ("1", "Scraping Básico", exemplo_scraping_basico),
        ("2", "Múltiplos Sites", exemplo_multiplos_sites),
        ("3", "Com Banco de Dados", exemplo_com_banco_dados),
        ("4", "Com E-mail", exemplo_com_email),
        ("5", "Filtros Avançados", exemplo_filtros_avancados),
        ("6", "Monitoramento de Preços", exemplo_monitoramento_precos),
        ("7", "Configurações", exemplo_configuracoes),
        ("8", "Exportar Dados", exemplo_exportar_dados)
    ]
    
    print("\nExemplos disponíveis:")
    for num, nome, _ in exemplos:
        print(f"  {num}. {nome}")
    
    print("\nDigite o número do exemplo (ou 'todos' para executar todos):")
    escolha = input("> ").strip().lower()
    
    if escolha == 'todos':
        for num, nome, func in exemplos:
            print(f"\n{'='*60}")
            print(f"Executando exemplo {num}: {nome}")
            print(f"{'='*60}")
            
            try:
                if asyncio.iscoroutinefunction(func):
                    await func()
                else:
                    func()
            except Exception as e:
                print(f"Erro no exemplo {num}: {e}")
            
            print("\nPressione Enter para continuar...")
            input()
    
    else:
        # Executar exemplo específico
        for num, nome, func in exemplos:
            if escolha == num:
                print(f"\nExecutando: {nome}")
                try:
                    if asyncio.iscoroutinefunction(func):
                        await func()
                    else:
                        func()
                except Exception as e:
                    print(f"Erro: {e}")
                return
        
        print("Exemplo não encontrado!")


if __name__ == "__main__":
    asyncio.run(main())
