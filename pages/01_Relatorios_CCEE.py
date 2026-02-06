import streamlit as st
from apps.relatorios_ccee.app import main 

# Configuração da página deve ser a primeira chamada Streamlit
st.set_page_config(page_title="Relatórios CCEE", layout="wide")

# Executa o app
main()