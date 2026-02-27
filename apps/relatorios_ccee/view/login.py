import streamlit as st
import logging
from apps.relatorios_ccee.model.arquivos import obtem_asset_path
from apps.relatorios_ccee.controller import auth_controller

diagnostic_msgs = auth_controller.verificar_config()
for msg in diagnostic_msgs:
    st.warning(msg)

def show_login_page():
    st.image(obtem_asset_path("logo.png"), width=250)
    st.title("Login - Envio de Relatórios CCEE")
    st.write("Por favor, autentique-se com sua conta Microsoft para continuar.")
    
    # o controller fornece a URL de autenticação

    params = st.query_params
    codigo = params.get("code")

    if codigo:
        try:
            auth_controller.processar_callback(codigo)
        except Exception as e:
            st.error(f"Falha ao validar login: {e}")
            logging.exception("Erro durante callback de autenticação:")
            # Limpa o parâmetro 'code' da URL para evitar reuso de código expirado
            try:
                st.experimental_set_query_params()
            except Exception:
                logging.debug("Não foi possível limpar query params no ambiente Streamlit")
            # Gera nova URL de autenticação e exibe botão de login para tentar novamente
            url_auth = auth_controller.obter_url_autenticacao()
            if url_auth:
                st.markdown(f'<a href="{url_auth}" target="_self" class="button">Tentar Novamente</a>', unsafe_allow_html=True)
            else:
                st.error("Erro ao gerar link de login. Atualize a página ou contate o administrador.")
    else:
        url_auth = auth_controller.obter_url_autenticacao()
        if url_auth:
            st.markdown("""
            <style>
            .button {
                display: inline-block;
                padding: 0.5em 1em;
                background-color: #0078D4;
                color: white !important;
                border-radius: 4px;
                text-decoration: none;
                font-size: 16px;
                cursor: pointer;
            }
            .button:hover { background-color: #005A9E; }
            </style>
            """, unsafe_allow_html=True)
            st.markdown(f'<a href="{url_auth}" target="_self" class="button">Entrar com Microsoft</a>', unsafe_allow_html=True)
        else:
            st.error("Erro ao gerar link de login.")
    st.stop()