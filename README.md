# DGCA Relatórios CCEE

Aplicacao Streamlit utilizada para geracao e envio de relatorios CCEE via Microsoft Graph API. O sistema processa dados de Excel, renderiza relatorios em PDF e cria rascunhos de e-mail na conta do usuario autenticado.

## 📁 Estrutura

- `apps/relatorios_ccee/`
  - `controller/` - logica de autenticacao (MSAL) e servicos Graph
  - `view/` - paginas Streamlit (login, relatorios, etc.)
  - `model/` - utilidades, leitura de arquivos, seguranca, etc.
- `pages/` - entradas do Streamlit para o menu de relatorios
- `logs/` - arquivos de log da aplicao
- `gerar_certificados.py`, `home.py`, etc. utilitrios adicionais

## 🚀 Como executar

1. Clone o repositorio e acesse a pasta:
   ```powershell
   cd c:\DGCA
   ```
2. Crie um ambiente Python e instale dependencias:
   ```powershell
   python -m venv .venv
   .\.venv\Scripts\Activate.ps1
   pip install -r apps/analise_demanda/requirements.txt
   pip install -r requirements.txt  # se existir
   ```
3. Configure variaveis de ambiente no arquivo `.env` dentro de `apps/relatorios_ccee/view` (ou na raiz se preferir):
   ```ini
   AZURE_CLIENT_ID=...
   AZURE_CLIENT_SECRET=...
   AZURE_TENANT_ID=...
   AZURE_REDIRECT_URI=http://localhost:8501
   ```
4. Execute a aplicao:
   ```powershell
   streamlit run pages/01_Relatorios_CCEE.py
   ```

## 🔐 Autenticacao Microsoft (MSAL)

A aplicao utiliza `msal` para obter tokens via fluxo de indice de autorizacao. Os escopos requeridos so:

- `User.Read`
- `Mail.Send`
- `Mail.ReadWrite` (necessita consentimento de administrador do tenant)

O arquivo `auth_controller.py` encapsula toda a config e operacao MSAL.

### Consentimento
O tenant pode exigir que um administrador conceda permicoes. Faa login como admin no Azure portal e clique em "Grant admin consent" em **App registrations -> [sua app] -> API permissions**.

## 🧠 Lgica de negcio

- Processamento de dados Excel ocorre em `apps/relatorios_ccee/model/relatorios.py` e outros utilitrios.
- Cria PDFs e anexa nos rascunhos via `criar_rascunho_graph` em `servicos.py`.
- Logs detalhados gravados em `logs/app.log`.

## 🛠 Desenvolvimento

- Use Python 3.11+.
- Rode `pre-commit` se configurado.
- Logs podem ser analisados para depurao de erros de permissao ou conexo.

## 📄 Outros utilitarios

- `gerar_certificados.py` - gera certificados genericos.
- `home.py` - possivel pagina inicial.
- etc.

## 📚 Mais informaes

Leia o cdigo em `apps/relatorios_ccee/` para detalhes de implementao. Cada modulo  documentado.

---

*Criado automaticamente por GitHub Copilot.*