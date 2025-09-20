#!/usr/bin/env python3
"""
Web Scraper Automatizado - Script Principal

Script principal para execução de scraping com diferentes parâmetros.
"""

import argparse
import asyncio
import sys
from pathlib import Path
from typing import List, Optional

sys.path.append(str(Path(__file__).parent))

from config.settings import Settings
from scrapers import ScraperFactory
from database.database import DatabaseManager
from email_service.email_sender import EmailService
from utils.logger import setup_logger

logger = setup_logger(__name__)


def parse_arguments() -> argparse.Namespace:
    """Parse argumentos da linha de comando."""
    parser = argparse.ArgumentParser(
        description="Web Scraper Automatizado com Envio de E-mails",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Exemplos de uso:
  python main.py --site amazon --search "notebook gamer" --max-price 3000
  python main.py --site ebay --search "smartphone" --min-price 500 --max-price 1500
  python main.py --site mercadolivre --search "tablet" --send-email
        """
    )
    
    parser.add_argument(
        "--site",
        choices=["amazon", "ebay", "mercadolivre"],
        required=True,
        help="Site para fazer scraping"
    )
    
    parser.add_argument(
        "--search",
        required=True,
        help="Termo de busca para produtos"
    )
    
    parser.add_argument(
        "--max-price",
        type=float,
        help="Preço máximo dos produtos"
    )
    
    parser.add_argument(
        "--min-price",
        type=float,
        default=0,
        help="Preço mínimo dos produtos (padrão: 0)"
    )
    
    parser.add_argument(
        "--max-results",
        type=int,
        default=50,
        help="Número máximo de resultados (padrão: 50)"
    )
    
    parser.add_argument(
        "--send-email",
        action="store_true",
        help="Enviar resultados por e-mail"
    )
    
    parser.add_argument(
        "--email-recipients",
        nargs="+",
        help="Lista de destinatários de e-mail"
    )
    
    parser.add_argument(
        "--save-to-db",
        action="store_true",
        default=True,
        help="Salvar resultados no banco de dados (padrão: True)"
    )
    
    parser.add_argument(
        "--output-format",
        choices=["json", "csv", "excel"],
        default="json",
        help="Formato de saída dos dados (padrão: json)"
    )
    
    parser.add_argument(
        "--output-file",
        help="Arquivo de saída para os dados"
    )
    
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Modo verboso (mais logs)"
    )
    
    return parser.parse_args()


async def main():
    """Função principal."""
    args = parse_arguments()
    
    if args.verbose:
        logger.info("Modo verboso ativado")
    
    # Carregar configurações
    settings = Settings()
    logger.info(f"Configurações carregadas: {settings.app_name}")
    
    # Inicializar banco de dados
    db_manager = DatabaseManager(settings.database_url)
    await db_manager.initialize()
    logger.info("Banco de dados inicializado")
    
    # Criar scraper
    scraper = ScraperFactory.create_scraper(args.site, settings)
    logger.info(f"Scraper criado para: {args.site}")
    
    # Preparar filtros
    filters = {
        "min_price": args.min_price,
        "max_results": args.max_results
    }
    
    if args.max_price:
        filters["max_price"] = args.max_price
    
    logger.info(f"Iniciando scraping: {args.search}")
    logger.info(f"Filtros: {filters}")
    
    try:
        # Executar scraping
        products = await scraper.search_products(
            search_term=args.search,
            **filters
        )
        
        logger.info(f"Encontrados {len(products)} produtos")
        
        if not products:
            print("\n" + "="*60)
            print(f"📊 RESUMO DO SCRAPING: {args.search}")
            print("="*60)
            print("❌ Nenhum produto encontrado")
            return
        
        # Salvar no banco de dados
        if args.save_to_db:
            session_data = {
                "session_name": f"CLI - {args.search}",
                "site": args.site,
                "search_term": args.search,
                "filters_applied": filters
            }
            
            session = await db_manager.create_scraping_session(session_data)
            saved_products = await db_manager.save_products(products, session.id)
            
            await db_manager.update_scraping_session(session.id, {
                "products_found": len(products),
                "products_saved": len(saved_products),
                "success": True
            })
            
            logger.info(f"Dados salvos no banco: {len(saved_products)} produtos")
        
        # Enviar por e-mail
        if args.send_email:
            email_service = EmailService(settings)
            
            recipients = args.email_recipients or settings.email_recipients
            if not recipients:
                logger.warning("Nenhum destinatário de e-mail configurado")
            else:
                success = await email_service.send_product_report(
                    products=products,
                    search_term=args.search,
                    recipients=recipients
                )
                
                if success:
                    logger.info("Relatório enviado por e-mail com sucesso")
                else:
                    logger.error("Falha ao enviar e-mail")
        
        # Salvar em arquivo
        if args.output_file:
            await save_to_file(products, args.output_file, args.output_format)
            logger.info(f"Dados salvos em: {args.output_file}")
        
        # Exibir resumo
        display_summary(products, args.search)
        
    except Exception as e:
        logger.error(f"Erro durante execução: {e}")
        print(f"❌ Erro: {e}")
        sys.exit(1)


async def save_to_file(products: List[dict], filename: str, format_type: str):
    """Salva produtos em arquivo."""
    import json
    import pandas as pd
    
    if format_type == "json":
        with open(filename, "w", encoding="utf-8") as f:
            json.dump(products, f, ensure_ascii=False, indent=2)
    
    elif format_type == "csv":
        df = pd.DataFrame(products)
        df.to_csv(filename, index=False, encoding="utf-8")
    
    elif format_type == "excel":
        df = pd.DataFrame(products)
        df.to_excel(filename, index=False)


def display_summary(products: List[dict], search_term: str):
    """Exibe resumo dos resultados."""
    print("\n" + "="*60)
    print(f"📊 RESUMO DO SCRAPING: {search_term}")
    print("="*60)
    
    if not products:
        print("❌ Nenhum produto encontrado")
        return
    
    # Estatísticas básicas
    total_products = len(products)
    prices = [p.get("price", 0) for p in products if p.get("price", 0) > 0]
    
    print(f"📦 Total de produtos: {total_products}")
    
    if prices:
        min_price = min(prices)
        max_price = max(prices)
        avg_price = sum(prices) / len(prices)
        
        print(f"💰 Menor preço: R$ {min_price:.2f}")
        print(f"💰 Maior preço: R$ {max_price:.2f}")
        print(f"💰 Preço médio: R$ {avg_price:.2f}")
    
    # Resumo por site
    sites = {}
    for product in products:
        site = product.get("site", "Desconhecido")
        sites[site] = sites.get(site, 0) + 1
    
    print("\n🌐 Produtos por site:")
    for site, count in sites.items():
        print(f"  • {site}: {count} produtos")
    
    # Mostrar alguns produtos
    print("\n🛒 Primeiros produtos encontrados:")
    for i, product in enumerate(products[:5], 1):
        title = product.get("title", "Sem título")[:50]
        price = product.get("price", 0)
        site = product.get("site", "N/A")
        
        print(f"  {i}. {title}...")
        print(f"     💰 R$ {price:.2f} | 🌐 {site}")
    
    if total_products > 5:
        print(f"  ... e mais {total_products - 5} produtos")
    
    print("\n✅ Scraping concluído com sucesso!")


if __name__ == "__main__":
    asyncio.run(main())
