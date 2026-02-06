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
# CONFIGURAÇÃO DA PÁGINA
# ==========================
st.set_page_config(
    page_title="Portal DGCA",
    page_icon=icon_image if icon_image else "⚡",
    layout="wide",
    initial_sidebar_state="collapsed"
)

st.sidebar.title("Portal DGCA")

if os.path.exists(caminho_logo):
    st.image(caminho_logo, width=250)
else:
    st.warning(f"Logo não encontrada em: {caminho_logo}")

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
# CARGA DE DADOS
# ==========================
@st.cache_data(ttl=3600)
def carregar_dados_contatos():
    home_dir = os.path.expanduser("~")
    caminho_relativo = os.path.join(
        "ELECTRA COMERCIALIZADORA DE ENERGIA S.A",
        "GE - DGCA",
        "DGC",
        "Macro",
        "Contatos de E-mail para Macros.xlsx"
    )
    caminho_completo = os.path.join(home_dir, caminho_relativo)

    if os.path.exists(caminho_completo):
        return pd.read_excel(caminho_completo, engine="openpyxl"), caminho_completo

    return None, caminho_completo

# ==========================
# INTERFACE PRINCIPAL
# ==========================
def main():
    if os.path.exists(caminho_logo):
        st.logo(caminho_logo)

    st.title("Portal DGCA")
    st.write("Hub central de aplicações para a DGCA.")

    st.divider()

    st.subheader("🚀 Aplicações DGCA")
    
    if APLICACOES_DGCA:
        colunas = st.columns(len(APLICACOES_DGCA))

        for col, app in zip(colunas, APLICACOES_DGCA):
            with col:
                with st.container(border=True):
                    st.markdown(f"### {app['icon']} {app['nome']}")
                    st.write(app['desc'])
                    
                    if "page" in app:
                        st.page_link(
                            app["page"],
                            label="Acessar Sistema",
                            use_container_width=True
                        )
                    else:
                        st.button("Em Breve", disabled=True, use_container_width=True, key=app["nome"])

if __name__ == "__main__":
    main()