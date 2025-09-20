"""
Dashboard Streamlit
==================

Interface web para visualização de dados, configuração e monitoramento
do sistema de web scraping automatizado.

Autor: Seu Nome
Data: 2025-09-20
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import asyncio
import sys
from pathlib import Path

# Adicionar o diretório raiz ao path
sys.path.append(str(Path(__file__).parent.parent))

from config.settings import Settings
from database.database import DatabaseManager
from scrapers import ScraperFactory
from email_service.email_sender import EmailService

# Configuração da página
st.set_page_config(
    page_title="Web Scraper Dashboard",
    page_icon="🕷️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# CSS customizado
st.markdown("""
<style>
    .main-header {
        background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
        padding: 1rem;
        border-radius: 10px;
        color: white;
        text-align: center;
        margin-bottom: 2rem;
    }
    
    .metric-card {
        background: white;
        padding: 1rem;
        border-radius: 8px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        border-left: 4px solid #667eea;
    }
    
    .success-box {
        background-color: #d4edda;
        border: 1px solid #c3e6cb;
        color: #155724;
        padding: 1rem;
        border-radius: 5px;
        margin: 1rem 0;
    }
    
    .error-box {
        background-color: #f8d7da;
        border: 1px solid #f5c6cb;
        color: #721c24;
        padding: 1rem;
        border-radius: 5px;
        margin: 1rem 0;
    }
</style>
""", unsafe_allow_html=True)

# Inicializar sessão
if 'settings' not in st.session_state:
    st.session_state.settings = Settings()
    st.session_state.db_manager = DatabaseManager(st.session_state.settings.database_url)
    
    # Inicializar banco de dados
    try:
        asyncio.run(st.session_state.db_manager.initialize())
    except Exception as e:
        st.error(f"Erro ao inicializar banco de dados: {e}")

# Header principal
st.markdown("""
<div class="main-header">
    <h1>🕷️ Web Scraper Automatizado</h1>
    <p>Dashboard de Monitoramento e Controle</p>
</div>
""", unsafe_allow_html=True)

# Sidebar para navegação
st.sidebar.title("📊 Navegação")
page = st.sidebar.selectbox(
    "Escolha uma página:",
    [
        "🏠 Início",
        "🔍 Scraping Manual",
        "📈 Estatísticas",
        "📧 E-mails",
        "⚙️ Configurações"
    ]
)

# Página Inicial
if page == "🏠 Início":
    st.header("🏠 Visão Geral do Sistema")
    
    # Obter estatísticas
    try:
        stats = asyncio.run(st.session_state.db_manager.get_statistics())
        
        # Métricas principais
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric(
                label="📦 Total de Produtos",
                value=stats.get('total_products', 0)
            )
        
        with col2:
            st.metric(
                label="✅ Produtos em Estoque",
                value=stats.get('products_in_stock', 0)
            )
        
        with col3:
            st.metric(
                label="🔄 Sessões de Scraping",
                value=stats.get('total_sessions', 0)
            )
        
        with col4:
            st.metric(
                label="📧 E-mails Enviados",
                value=stats.get('total_emails', 0)
            )
        
        # Gráfico de produtos por site
        if stats.get('by_site'):
            st.subheader("🌐 Produtos por Site")
            
            site_data = stats['by_site']
            df_sites = pd.DataFrame([
                {'Site': site, 'Produtos': data['count'], 'Preço Médio': data['avg_price']}
                for site, data in site_data.items()
            ])
            
            col1, col2 = st.columns(2)
            
            with col1:
                fig_pie = px.pie(
                    df_sites, 
                    values='Produtos', 
                    names='Site',
                    title="Distribuição de Produtos"
                )
                st.plotly_chart(fig_pie, use_container_width=True)
            
            with col2:
                fig_bar = px.bar(
                    df_sites,
                    x='Site',
                    y='Preço Médio',
                    title="Preço Médio por Site"
                )
                st.plotly_chart(fig_bar, use_container_width=True)
        
        # Sessões recentes
        st.subheader("🔄 Sessões Recentes")
        recent_sessions = asyncio.run(st.session_state.db_manager.get_recent_sessions(10))
        
        if recent_sessions:
            sessions_data = []
            for session in recent_sessions:
                sessions_data.append({
                    'ID': session.id,
                    'Site': session.site,
                    'Busca': session.search_term,
                    'Produtos': session.products_found,
                    'Sucesso': '✅' if session.success else '❌',
                    'Data': session.started_at.strftime('%d/%m/%Y %H:%M') if session.started_at else 'N/A'
                })
            
            df_sessions = pd.DataFrame(sessions_data)
            st.dataframe(df_sessions, use_container_width=True)
        else:
            st.info("Nenhuma sessão encontrada")
    
    except Exception as e:
        st.error(f"Erro ao carregar estatísticas: {e}")

# Página de Scraping Manual
elif page == "🔍 Scraping Manual":
    st.header("🔍 Executar Scraping Manual")
    
    with st.form("scraping_form"):
        col1, col2 = st.columns(2)
        
        with col1:
            site = st.selectbox(
                "Site:",
                ["amazon", "ebay", "mercadolivre"]
            )
            
            search_term = st.text_input(
                "Termo de busca:",
                placeholder="Ex: notebook gamer"
            )
        
        with col2:
            max_results = st.number_input(
                "Máximo de resultados:",
                min_value=1,
                max_value=100,
                value=20
            )
            
            max_price = st.number_input(
                "Preço máximo (opcional):",
                min_value=0.0,
                value=0.0,
                step=10.0
            )
        
        send_email = st.checkbox("Enviar resultados por e-mail")
        
        submitted = st.form_submit_button("🚀 Executar Scraping")
        
        if submitted:
            if not search_term:
                st.error("Por favor, insira um termo de busca")
            else:
                with st.spinner(f"Executando scraping no {site}..."):
                    try:
                        # Criar scraper
                        scraper = ScraperFactory.create_scraper(site, st.session_state.settings)
                        
                        # Preparar filtros
                        filters = {
                            'max_results': max_results
                        }
                        
                        if max_price > 0:
                            filters['max_price'] = max_price
                        
                        # Executar scraping
                        products = asyncio.run(
                            scraper.search_products(search_term, **filters)
                        )
                        
                        if products:
                            st.success(f"✅ Encontrados {len(products)} produtos!")
                            
                            # Salvar no banco
                            session_data = {
                                'session_name': f'Dashboard - {search_term}',
                                'site': site,
                                'search_term': search_term,
                                'filters_applied': filters
                            }
                            
                            session = asyncio.run(
                                st.session_state.db_manager.create_scraping_session(session_data)
                            )
                            
                            saved_products = asyncio.run(
                                st.session_state.db_manager.save_products(products, session.id)
                            )
                            
                            asyncio.run(
                                st.session_state.db_manager.update_scraping_session(
                                    session.id,
                                    {
                                        'products_found': len(products),
                                        'products_saved': len(saved_products),
                                        'success': True,
                                        'completed_at': datetime.utcnow()
                                    }
                                )
                            )
                            
                            # Exibir resultados
                            st.subheader("📦 Produtos Encontrados")
                            
                            products_data = []
                            for product in products[:10]:  # Mostrar apenas os primeiros 10
                                products_data.append({
                                    'Título': product.get('title', '')[:50] + '...',
                                    'Preço': f"R$ {product.get('price', 0):.2f}",
                                    'Site': product.get('site', ''),
                                    'Avaliação': product.get('rating', 0),
                                    'URL': product.get('url', '')
                                })
                            
                            df_products = pd.DataFrame(products_data)
                            st.dataframe(df_products, use_container_width=True)
                            
                            # Enviar e-mail se solicitado
                            if send_email and st.session_state.settings.email_recipients:
                                email_service = EmailService(st.session_state.settings)
                                
                                email_success = asyncio.run(
                                    email_service.send_product_report(
                                        products=products,
                                        search_term=search_term,
                                        recipients=st.session_state.settings.email_recipients,
                                        session_id=session.id
                                    )
                                )
                                
                                if email_success:
                                    st.success("📧 E-mail enviado com sucesso!")
                                else:
                                    st.error("❌ Falha ao enviar e-mail")
                        
                        else:
                            st.warning("⚠️ Nenhum produto encontrado")
                    
                    except Exception as e:
                        st.error(f"❌ Erro durante scraping: {e}")

# Página de Estatísticas
elif page == "📈 Estatísticas":
    st.header("📈 Estatísticas Detalhadas")
    
    # Filtros
    col1, col2 = st.columns(2)
    
    with col1:
        days_filter = st.selectbox(
            "Período:",
            [7, 15, 30, 60, 90],
            index=2,
            format_func=lambda x: f"Últimos {x} dias"
        )
    
    with col2:
        site_filter = st.selectbox(
            "Site:",
            ["Todos", "amazon", "ebay", "mercadolivre"]
        )
    
    try:
        # Obter produtos com filtros
        filters = {}
        if site_filter != "Todos":
            filters['site'] = site_filter
        
        products = asyncio.run(
            st.session_state.db_manager.get_products(filters, limit=1000)
        )
        
        if products:
            # Filtrar por data
            cutoff_date = datetime.utcnow() - timedelta(days=days_filter)
            recent_products = [
                p for p in products 
                if p.last_updated and p.last_updated >= cutoff_date
            ]
            
            if recent_products:
                # Converter para DataFrame
                products_data = []
                for product in recent_products:
                    products_data.append({
                        'Título': product.title,
                        'Preço': product.current_price,
                        'Site': product.site,
                        'Avaliação': product.rating,
                        'Reviews': product.num_reviews,
                        'Estoque': product.in_stock,
                        'Frete Grátis': product.free_shipping,
                        'Data': product.last_updated
                    })
                
                df = pd.DataFrame(products_data)
                
                # Métricas
                col1, col2, col3, col4 = st.columns(4)
                
                with col1:
                    st.metric(
                        "Total de Produtos",
                        len(recent_products)
                    )
                
                with col2:
                    avg_price = df['Preço'].mean()
                    st.metric(
                        "Preço Médio",
                        f"R$ {avg_price:.2f}"
                    )
                
                with col3:
                    in_stock_count = df['Estoque'].sum()
                    st.metric(
                        "Em Estoque",
                        in_stock_count
                    )
                
                with col4:
                    free_shipping_count = df['Frete Grátis'].sum()
                    st.metric(
                        "Frete Grátis",
                        free_shipping_count
                    )
                
                # Gráficos
                col1, col2 = st.columns(2)
                
                with col1:
                    # Distribuição de preços
                    fig_hist = px.histogram(
                        df,
                        x='Preço',
                        nbins=20,
                        title="Distribuição de Preços"
                    )
                    st.plotly_chart(fig_hist, use_container_width=True)
                
                with col2:
                    # Preços por site
                    fig_box = px.box(
                        df,
                        x='Site',
                        y='Preço',
                        title="Preços por Site"
                    )
                    st.plotly_chart(fig_box, use_container_width=True)
                
                # Tabela de produtos
                st.subheader("📦 Lista de Produtos")
                st.dataframe(
                    df.sort_values('Data', ascending=False),
                    use_container_width=True
                )
            
            else:
                st.info(f"Nenhum produto encontrado nos últimos {days_filter} dias")
        
        else:
            st.info("Nenhum produto encontrado no banco de dados")
    
    except Exception as e:
        st.error(f"Erro ao carregar estatísticas: {e}")

# Página de E-mails
elif page == "📧 E-mails":
    st.header("📧 Gerenciamento de E-mails")
    
    # Teste de conexão
    st.subheader("🔌 Teste de Conexão")
    
    if st.button("🧪 Testar Conexão SMTP"):
        try:
            email_service = EmailService(st.session_state.settings)
            
            if email_service.test_connection():
                st.success("✅ Conexão SMTP bem-sucedida!")
            else:
                st.error("❌ Falha na conexão SMTP")
        
        except Exception as e:
            st.error(f"❌ Erro no teste: {e}")
    
    # Configurações de e-mail
    st.subheader("⚙️ Configurações Atuais")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.info(f"📧 **Host:** {st.session_state.settings.email_host}")
        st.info(f"🔌 **Porta:** {st.session_state.settings.email_port}")
        st.info(f"🔒 **TLS:** {'Sim' if st.session_state.settings.email_use_tls else 'Não'}")
    
    with col2:
        st.info(f"👤 **Usuário:** {st.session_state.settings.email_user}")
        st.info(f"📝 **Nome:** {st.session_state.settings.email_from_name}")
        st.info(f"📨 **Destinatários:** {len(st.session_state.settings.email_recipients)}")
    
    # Envio de teste
    st.subheader("📤 Enviar E-mail de Teste")
    
    with st.form("test_email_form"):
        test_recipients = st.text_input(
            "Destinatários (separados por vírgula):",
            value=",".join(st.session_state.settings.email_recipients)
        )
        
        test_subject = st.text_input(
            "Assunto:",
            value="Teste do Web Scraper"
        )
        
        submitted = st.form_submit_button("🚀 Enviar Teste")
        
        if submitted:
            if test_recipients:
                recipients_list = [email.strip() for email in test_recipients.split(',')]
                
                try:
                    email_service = EmailService(st.session_state.settings)
                    
                    # Criar dados de teste
                    test_data = {
                        'type': 'Teste do Sistema',
                        'message': 'Este é um e-mail de teste do Web Scraper Automatizado.',
                        'timestamp': datetime.now().isoformat()
                    }
                    
                    success = asyncio.run(
                        email_service.send_error_notification(
                            error_details=test_data,
                            recipients=recipients_list
                        )
                    )
                    
                    if success:
                        st.success("✅ E-mail de teste enviado com sucesso!")
                    else:
                        st.error("❌ Falha ao enviar e-mail de teste")
                
                except Exception as e:
                    st.error(f"❌ Erro: {e}")
            
            else:
                st.error("Por favor, insira pelo menos um destinatário")

# Página de Configurações
elif page == "⚙️ Configurações":
    st.header("⚙️ Configurações do Sistema")
    
    # Informações do sistema
    st.subheader("📊 Informações do Sistema")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.info(f"📝 **Nome:** {st.session_state.settings.app_name}")
        st.info(f"🏷️ **Versão:** {st.session_state.settings.app_version}")
        st.info(f"🔍 **Debug:** {'Ativo' if st.session_state.settings.debug else 'Inativo'}")
    
    with col2:
        st.info(f"🗄️ **Banco:** {st.session_state.settings.database_url}")
        st.info(f"⏱️ **Delay:** {st.session_state.settings.scraping_delay}s")
        st.info(f"🔄 **Tentativas:** {st.session_state.settings.max_retries}")
    
    # Sites suportados
    st.subheader("🌐 Sites Suportados")
    
    supported_sites = ScraperFactory.get_supported_sites()
    
    for site in supported_sites:
        if site not in ['mercado_livre', 'ml']:  # Evitar aliases
            st.success(f"✅ {site.title()}")
    
    # Limpeza de dados
    st.subheader("🧹 Manutenção")
    
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("🗄️ Limpar Dados Antigos (90+ dias)"):
            try:
                asyncio.run(st.session_state.db_manager.cleanup_old_data(90))
                st.success("✅ Limpeza concluída!")
            except Exception as e:
                st.error(f"❌ Erro na limpeza: {e}")
    
    with col2:
        if st.button("📊 Atualizar Estatísticas"):
            st.rerun()

# Footer
st.markdown("---")
st.markdown("""
<div style='text-align: center; color: #666; font-size: 12px;'>
    🕷️ Web Scraper Automatizado | Desenvolvido com Streamlit
</div>
""", unsafe_allow_html=True)
