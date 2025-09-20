# Contribuindo para o Web Scraper Automatizado

Obrigado por considerar contribuir para este projeto! Este documento fornece diretrizes para contribuições.

## 🤝 Como Contribuir

### 1. Reportando Bugs

Antes de reportar um bug:
- Verifique se o bug já foi reportado nas [Issues](https://github.com/cauaprjct/web-scraper-automatizado/issues)
- Use a versão mais recente do projeto
- Inclua informações detalhadas sobre o ambiente

**Template para Bug Report:**
```markdown
**Descrição do Bug**
Descrição clara e concisa do problema.

**Passos para Reproduzir**
1. Vá para '...'
2. Clique em '...'
3. Execute '...'
4. Veja o erro

**Comportamento Esperado**
O que deveria acontecer.

**Screenshots**
Se aplicável, adicione screenshots.

**Ambiente:**
- OS: [ex: Windows 10]
- Python: [ex: 3.9.0]
- Versão do projeto: [ex: 1.0.0]

**Informações Adicionais**
Qualquer contexto adicional sobre o problema.
```

### 2. Sugerindo Melhorias

Para sugerir uma nova funcionalidade:
- Abra uma Issue com o label "enhancement"
- Descreva detalhadamente a funcionalidade
- Explique por que seria útil
- Considere implementações alternativas

### 3. Contribuindo com Código

#### Configuração do Ambiente de Desenvolvimento

1. **Fork o repositório**
```bash
git clone https://github.com/SEU-USERNAME/web-scraper-automatizado.git
cd web-scraper-automatizado
```

2. **Criar ambiente virtual**
```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
# ou
venv\Scripts\activate  # Windows
```

3. **Instalar dependências**
```bash
pip install -r requirements.txt
pip install -r requirements-dev.txt  # Se existir
```

4. **Configurar pré-commit hooks**
```bash
pre-commit install
```

#### Fluxo de Desenvolvimento

1. **Criar branch para sua feature**
```bash
git checkout -b feature/nome-da-feature
```

2. **Fazer suas alterações**
- Siga as convenções de código
- Adicione testes para novas funcionalidades
- Atualize a documentação se necessário

3. **Executar testes**
```bash
python -m pytest tests/
```

4. **Verificar qualidade do código**
```bash
flake8 .
black .
isort .
```

5. **Commit suas alterações**
```bash
git add .
git commit -m "feat: adiciona nova funcionalidade X"
```

6. **Push para seu fork**
```bash
git push origin feature/nome-da-feature
```

7. **Abrir Pull Request**

## 📝 Convenções de Código

### Estilo de Código
- Use **Black** para formatação automática
- Use **isort** para organizar imports
- Siga **PEP 8** para convenções Python
- Use **type hints** sempre que possível

### Convenções de Commit
Use [Conventional Commits](https://www.conventionalcommits.org/):

- `feat:` nova funcionalidade
- `fix:` correção de bug
- `docs:` mudanças na documentação
- `style:` formatação, ponto e vírgula, etc
- `refactor:` refatoração de código
- `test:` adição ou correção de testes
- `chore:` tarefas de manutenção

Exemplos:
```
feat: adiciona scraper para Shopee
fix: corrige parsing de preços na Amazon
docs: atualiza README com novos exemplos
test: adiciona testes para EmailService
```

### Estrutura de Arquivos
```
web-scraper-automatizado/
├── config/              # Configurações
├── scrapers/            # Scrapers específicos
│   ├── __init__.py
│   ├── base_scraper.py  # Classe base
│   └── site_scraper.py  # Scraper específico
├── database/            # Modelos e BD
├── email_service/       # Sistema de e-mail
├── dashboard/           # Interface Streamlit
├── utils/               # Utilitários
├── tests/               # Testes
└── docs/                # Documentação
```

## 🧪 Testes

### Executando Testes
```bash
# Todos os testes
python -m pytest

# Testes específicos
python -m pytest tests/test_scrapers.py

# Com coverage
python -m pytest --cov=scrapers

# Testes de integração
python -m pytest --integration
```

### Escrevendo Testes
- Use **pytest** como framework
- Crie mocks para requisições HTTP
- Teste casos de sucesso e falha
- Mantenha cobertura > 80%

Exemplo de teste:
```python
import pytest
from unittest.mock import Mock, patch
from scrapers.amazon_scraper import AmazonScraper

class TestAmazonScraper:
    def setup_method(self):
        self.scraper = AmazonScraper(Mock())
    
    @patch('scrapers.base_scraper.BaseScraper._make_request')
    @pytest.mark.asyncio
    async def test_search_products(self, mock_request):
        # Configurar mock
        mock_response = Mock()
        mock_response.text = "<html>...</html>"
        mock_request.return_value = mock_response
        
        # Executar teste
        products = await self.scraper.search_products("test")
        
        # Verificar resultado
        assert isinstance(products, list)
        mock_request.assert_called_once()
```

## 📚 Documentação

### Docstrings
Use formato Google/NumPy:
```python
def search_products(self, search_term: str, **filters) -> List[Dict]:
    """
    Busca produtos no site.
    
    Args:
        search_term: Termo de busca
        **filters: Filtros adicionais
        
    Returns:
        Lista de produtos encontrados
        
    Raises:
        ValueError: Se search_term estiver vazio
        RequestException: Se houver erro na requisição
    """
```

### README
- Mantenha atualizado
- Inclua exemplos práticos
- Documente novas funcionalidades

## 🔧 Adicionando Novo Scraper

Para adicionar suporte a um novo site:

1. **Criar arquivo do scraper**
```python
# scrapers/novosite_scraper.py
from .base_scraper import BaseScraper

class NovoSiteScraper(BaseScraper):
    def __init__(self, settings):
        super().__init__(settings)
        self.base_url = "https://novosite.com"
    
    def get_base_url(self) -> str:
        return self.base_url
    
    def get_search_url(self) -> str:
        return f"{self.base_url}/search"
    
    async def search_products(self, search_term: str, **filters):
        # Implementar lógica específica
        pass
    
    def _parse_product_element(self, element, base_url: str):
        # Implementar parsing específico
        pass
```

2. **Registrar no factory**
```python
# scrapers/scraper_factory.py
from .novosite_scraper import NovoSiteScraper

class ScraperFactory:
    _scrapers = {
        # ... outros scrapers
        'novosite': NovoSiteScraper,
    }
```

3. **Adicionar configurações**
```python
# config/settings.py
class Settings(BaseSettings):
    # ... outras configurações
    novosite_base_url: str = "https://novosite.com"
    novosite_search_url: str = "https://novosite.com/search"
```

4. **Criar testes**
```python
# tests/test_novosite_scraper.py
class TestNovoSiteScraper:
    def test_parse_product_element(self):
        # Implementar testes
        pass
```

5. **Atualizar documentação**
- Adicionar ao README
- Documentar peculiaridades do site
- Incluir exemplos de uso

## 🐛 Debugging

### Logs
```python
from utils.logger import setup_logger

logger = setup_logger(__name__)
logger.debug("Mensagem de debug")
logger.info("Informação")
logger.error("Erro")
```

### Configuração de Debug
```bash
# .env
DEBUG=true
LOG_LEVEL=DEBUG
```

## 📋 Checklist para Pull Request

Antes de submeter um PR, verifique:

- [ ] Código segue as convenções estabelecidas
- [ ] Testes passam (`pytest`)
- [ ] Cobertura de testes mantida
- [ ] Documentação atualizada
- [ ] Commit messages seguem convenção
- [ ] Não há conflitos com branch main
- [ ] Funcionalidade testada manualmente
- [ ] Logs apropriados adicionados
- [ ] Tratamento de erros implementado

## 🎯 Áreas que Precisam de Contribuição

### Alta Prioridade
- [ ] Novos scrapers (Shopee, AliExpress, etc.)
- [ ] Melhorias na detecção de mudanças de layout
- [ ] Otimização de performance
- [ ] Testes de integração

### Média Prioridade
- [ ] Interface web mais avançada
- [ ] Integração com APIs de notificação
- [ ] Análise de dados com ML
- [ ] Suporte a proxies

### Baixa Prioridade
- [ ] Dockerização
- [ ] CI/CD pipeline
- [ ] Métricas e monitoramento
- [ ] Internacionalização

## 🆘 Obtendo Ajuda

- **Issues**: Para bugs e sugestões
- **Discussions**: Para perguntas gerais
- **Email**: Para questões sensíveis

## 📜 Código de Conduta

### Nosso Compromisso
Nós, como membros, contribuidores e líderes, nos comprometemos a fazer da participação em nossa comunidade uma experiência livre de assédio para todos.

### Nossos Padrões
Exemplos de comportamento que contribuem para um ambiente positivo:
- Usar linguagem acolhedora e inclusiva
- Respeitar diferentes pontos de vista
- Aceitar críticas construtivas
- Focar no que é melhor para a comunidade
- Mostrar empatia com outros membros

### Comportamentos Inaceitáveis
- Uso de linguagem ou imagens sexualizadas
- Trolling, comentários insultuosos
- Assédio público ou privado
- Publicar informações privadas de outros
- Outras condutas inadequadas

### Aplicação
Instâncias de comportamento abusivo podem ser reportadas entrando em contato com a equipe do projeto. Todas as reclamações serão revisadas e investigadas.

## 🙏 Reconhecimentos

Contribuições são reconhecidas:
- Lista de contribuidores no README
- Menção em releases
- Badges especiais para contribuições significativas

---

**Obrigado por contribuir! Juntos podemos tornar este projeto ainda melhor! 🚀**
