import streamlit as st
import pandas as pd
import os
from PIL import Image

# ==========================
# CONFIGURAÇÃO DE CAMINHOS
# ==========================
current_dir = os.path.dirname(os.path.abspath(__file__))
caminho_logo = os.path.join(current_dir, "assets", "logo_branca.png")
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
        "page": "/Relatorios_CCEE",
        "icon": "📧",
        "desc": "Automação de envio de e-mails."
    },
    {
        "nome": "Análise de Demandas",
        "page": "/Analise_Demandas",
        "icon": "📊",
        "desc": "Dashboard de acompanhamento."
    },
    {
        "nome": "Resumo de Operações",
        "page": "/Resumo_Operacoes",
        "icon": "📈",
        "desc": "Visão geral operacional."
    },
]

# ==========================
# INTERFACE PRINCIPAL (HOME)
# ==========================
def show_home():
        """Função que renderiza o conteúdo da página inicial com HTML/CSS."""
        # Logo
        if os.path.exists(caminho_logo):
            st.logo(caminho_logo)

        # CSS com variáveis de cor extraídas da logo
        css = f"""<style>
        :root {{
            --dgca-1: #24ace4;
            --dgca-2: #1c749c;
            --dgca-3: #20b0d4;
            --dgca-4: #2094ac;
            --dgca-5: #2074b0;
        }}
        .dgca-header {{
            background: linear-gradient(90deg,var(--dgca-1),var(--dgca-3));
            padding:18px 22px;
            border-radius:12px;
            color:#fff;
            margin-bottom:14px;
        }}
        .dgca-title {{font-size:30px; font-weight:600; margin:0;}}
        .dgca-sub {{opacity:0.95; margin-top:6px;}}
        .dgca-cards {{display:flex; gap:14px; flex-wrap:wrap;}}
        .dgca-card {{
            background:#fff; border-radius:12px; padding:20px; box-shadow:0 10px 24px rgba(16,24,40,0.06);
            width:100%; max-width:380px; transition: transform .12s ease, box-shadow .12s ease; border-top:6px solid var(--dgca-2);
        }}
        .dgca-card:hover {{transform:translateY(-6px); box-shadow:0 22px 44px rgba(16,24,40,0.10);}}
        .dgca-card h3 {{margin:0 0 8px 0; color:#1c749c !important; font-weight:600; white-space: nowrap; overflow: hidden; text-overflow: ellipsis;}}
        .dgca-card p {{margin:0 0 12px 0; color:#475569}}
        .dgca-button {{
            display:inline-block; background:linear-gradient(90deg,var(--dgca-5),var(--dgca-4)); color:#fff !important; padding:8px 12px; border-radius:8px; text-decoration:none !important;
        }}
        .dgca-button, .dgca-button:link, .dgca-button:visited, .dgca-button:hover, .dgca-button:active {{
            color: #ffffff !important;
            text-decoration: none !important;
        }}
        @media (max-width:760px){{ .dgca-cards {{flex-direction:column;}} }}
        </style>"""

        st.markdown(css, unsafe_allow_html=True)

        header_html = """
        <div class="dgca-header">
            <div class="dgca-title">Portal DGCA</div>
            <div class="dgca-sub">Hub central de aplicações para a DGCA.</div>
        </div>
        """
        st.markdown(header_html, unsafe_allow_html=True)

        st.subheader("🚀 Aplicações DGCA")

        # Cards das aplicações (HTML para melhor controle visual)
        cards = []
        cards.append('<div class="dgca-cards">')
        for app in APLICACOES_DGCA:
            link = app.get('page', '#')
            card = (
                '<div class="dgca-card">'
                f'<h3>{app["icon"]} {app["nome"]}</h3>'
                f'<p>{app["desc"]}</p>'
                f'<a class="dgca-button" href="{link}">Acessar Sistema</a>'
                '</div>'
            )
            cards.append(card)
        cards.append('</div>')
        cards_html = ''.join(cards)
        st.markdown(cards_html, unsafe_allow_html=True)

# ==========================
# SIDEBAR - INFORMAÇÕES
# ==========================
st.sidebar.markdown("<div style='text-align: center; padding: 10px;'><small>© 2026 Desenvolvido pelo DGCA <br> Malik, Artur e Eduardo</small></div>", unsafe_allow_html=True)
st.sidebar.markdown("---")
# ==========================
# ESTRUTURA DE NAVEGAÇÃO
# ==========================
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