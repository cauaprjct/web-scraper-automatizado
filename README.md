# 🕷️ Web Scraper Automatizado com E-mail

Um sistema completo de web scraping automatizado que coleta dados de produtos, monitora preços e envia relatórios por e-mail. Ideal para monitoramento de ofertas, análise de mercado e automação de tarefas de coleta de dados.

## 🚀 Funcionalidades

- **Web Scraping Inteligente**: Coleta dados de múltiplos sites (Amazon, eBay, etc.)
- **Monitoramento de Preços**: Detecta mudanças de preços e ofertas especiais
- **Envio Automático de E-mails**: Relatórios HTML personalizados
- **Dashboard Web**: Interface Streamlit para visualização e configuração
- **Banco de Dados**: Armazenamento persistente com SQLAlchemy
- **Agendamento**: Execução automática com APScheduler
- **Logging Avançado**: Monitoramento completo das operações
- **Práticas Éticas**: Respeita robots.txt e implementa rate limiting

## 📋 Pré-requisitos

- Python 3.8+
- Conta de e-mail para envio de relatórios
- Conexão com internet

## 🛠️ Instalação

1. Clone o repositório:
```bash
git clone https://github.com/cauaprjct/web-scraper-automatizado.git
cd web-scraper-automatizado
```

2. Crie um ambiente virtual:
```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
# ou
venv\Scripts\activate  # Windows
```

3. Instale as dependências:
```bash
pip install -r requirements.txt
```

4. Configure as variáveis de ambiente:
```bash
cp .env.example .env
# Edite o arquivo .env com suas configurações
```

## ⚙️ Configuração

Edite o arquivo `.env` com suas configurações:

```env
# Configurações de E-mail
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USER=seu-email@gmail.com
EMAIL_PASSWORD=sua-senha-de-app
EMAIL_RECIPIENTS=destinatario@email.com

# Configurações de Scraping
SCRAPING_DELAY=2.0
MAX_RETRIES=3
REQUEST_TIMEOUT=30

# Banco de Dados
DATABASE_URL=sqlite:///data/scraper_data.db
```

## 🚀 Uso

### Linha de Comando

```bash
# Scraping básico
python main.py --site amazon --search "notebook gamer" --max-price 3000

# Com envio de e-mail
python main.py --site amazon --search "smartphone" --send-email

# Múltiplos filtros
python main.py --site ebay --search "tablet" --min-price 500 --max-price 1500 --max-results 20
```

### Dashboard Web

```bash
# Iniciar dashboard
python run_dashboard.py

# Acessar: http://localhost:8501
```

### Agendamento Automático

```bash
# Executar agendador
python scheduler.py
```

## 📊 Sites Suportados

- **Amazon** (amazon.com.br)
- **eBay** (ebay.com)
- **Mercado Livre** (mercadolivre.com.br)

## 🎯 Exemplos de Uso

### Monitoramento de Preços
```bash
python main.py --site amazon --search "iphone 13" --max-price 4000 --send-email
```

### Análise de Mercado
```bash
python main.py --site mercadolivre --search "notebook" --min-price 2000 --max-price 5000 --max-results 50
```

### Relatório Diário
```bash
python main.py --site ebay --search "smartwatch" --send-email --save-to-db
```

## 📁 Estrutura do Projeto

```
web-scraper-automatizado/
├── config/              # Configurações
├── scrapers/            # Módulos de scraping
├── database/            # Modelos e gerenciamento de BD
├── email_service/       # Sistema de e-mail
├── dashboard/           # Interface Streamlit
├── utils/               # Utilitários
├── tests/               # Testes unitários
├── main.py              # Script principal
├── scheduler.py         # Agendador
└── requirements.txt     # Dependências
```

## 🔧 Desenvolvimento

### Executar Testes
```bash
python -m pytest tests/
```

### Adicionar Novo Site
1. Crie um novo scraper em `scrapers/`
2. Herde de `BaseScraper`
3. Implemente `search_products()` e `_parse_product_element()`
4. Registre no `ScraperFactory`

### Exemplo de Novo Scraper
```python
from .base_scraper import BaseScraper

class NovoSiteScraper(BaseScraper):
    def __init__(self, settings):
        super().__init__(settings)
        self.base_url = "https://novosite.com"
    
    async def search_products(self, search_term, **filters):
        # Implementar lógica de scraping
        pass
```

## 📧 Sistema de E-mail

O sistema envia relatórios HTML com:
- Resumo de produtos encontrados
- Estatísticas de preços
- Gráficos e visualizações
- Anexos CSV/JSON com dados completos

## 🗄️ Banco de Dados

Armazena:
- Histórico de produtos
- Mudanças de preços
- Sessões de scraping
- Logs de e-mail

## ⚡ Performance

- Rate limiting configurável
- Retry automático em falhas
- Cache de requisições
- Processamento assíncrono

## 🛡️ Práticas Éticas

- Respeita robots.txt
- Implementa delays entre requisições
- User-Agent apropriado
- Não sobrecarrega servidores

## 🤝 Contribuição

1. Fork o projeto
2. Crie uma branch para sua feature
3. Commit suas mudanças
4. Push para a branch
5. Abra um Pull Request

## 📄 Licença

Este projeto está sob a licença MIT. Veja o arquivo [LICENSE](LICENSE) para detalhes.

## 🆘 Suporte

Se encontrar problemas:
1. Verifique a documentação
2. Consulte as [Issues](https://github.com/cauaprjct/web-scraper-automatizado/issues)
3. Abra uma nova issue se necessário

## 🎯 Roadmap

- [ ] Suporte a mais sites de e-commerce
- [ ] Integração com APIs de notificação (Telegram, Slack)
- [ ] Machine Learning para análise de tendências
- [ ] Interface web mais avançada
- [ ] Suporte a proxies rotativos
- [ ] Análise de sentimentos em reviews

---

**Desenvolvido com ❤️ para automação de coleta de dados**