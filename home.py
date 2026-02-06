import streamlit as st
import pandas as pd
import os
from PIL import Image

# ==========================
# CONFIGURAÇÃO DE CAMINHOS
# ==========================
current_dir = os.path.dirname(os.path.abspath(__file__))
caminho_logo = os.path.join(current_dir, "assets", "logo.png")
caminho_icone = os.path.join(current_dir, "assets", "icon.png")

icon_image = None
if os.path.exists(caminho_icone):
    try:
        icon_image = Image.open(caminho_icone)
    except Exception:
        pass

# ==========================
# CONFIGURAÇÃO DAS APLICAÇÕES
# ==========================
APLICACOES_DGCA = [
    {
        "nome": "Relatórios CCEE",
        "page": "pages/01_Relatorios_CCEE.py",
        "icon": "📧",
        "desc": "Automação de envio de e-mails."
    },
    {
        "nome": "Análise de Demandas",
        "page": "pages/02_Analise_Demandas.py",
        "icon": "📊",
        "desc": "Dashboard de acompanhamento."
    },
    {
        "nome": "Resumo de Operações",
        "page": "pages/03_Resumo_Operacoes.py",
        "icon": "📈",
        "desc": "Visão geral operacional."
    },
]

# ==========================
# INTERFACE PRINCIPAL (HOME)
# ==========================
def show_home():
    """Função que renderiza o conteúdo da página inicial."""
    if os.path.exists(caminho_logo):
        st.logo(caminho_logo)

    st.title("Portal DGCA")
    st.write("Hub central de aplicações para a DGCA.")
    st.divider()

    st.subheader("🚀 Aplicações DGCA")
    
    colunas = st.columns(len(APLICACOES_DGCA))
    for col, app in zip(colunas, APLICACOES_DGCA):
        with col:
            with st.container(border=True):
                st.markdown(f"### {app['icon']} {app['nome']}")
                st.write(app['desc'])
                st.page_link(app["page"], label="Acessar Sistema", use_container_width=True)

# ==========================
# ESTRUTURA DE NAVEGAÇÃO
# ==========================
# Definimos as páginas. A primeira da lista é a padrão (Home).
pg = st.navigation([
    st.Page(show_home, title="Portal DGCA", icon="🏠", default=True),
    st.Page("pages/01_Relatorios_CCEE.py", title="Relatórios CCEE", icon="📧"),
    st.Page("pages/02_Analise_Demandas.py", title="Análise de Demandas", icon="📊"),
    st.Page("pages/03_Resumo_Operacoes.py", title="Resumo de Operações", icon="📈"),
])

# Configurações globais (aba do navegador e ícone)
st.set_page_config(
    page_title="Portal DGCA",
    page_icon=icon_image if icon_image else "⚡",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Executa o roteamento das páginas
pg.run()