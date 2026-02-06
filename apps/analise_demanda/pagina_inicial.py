# app.py
import streamlit as st
from projeto_2 import run_Projeto_2
from reativo import run_Reativo
from controle import run_Controle

st.set_page_config(page_title="Página Inicial", page_icon="icon.png",layout="wide",initial_sidebar_state="expanded")

st.image("logo.png", width=250)

# Título e menu
st.title("Departamento de Gestão de Clientes")
opcao = st.sidebar.selectbox("Escolha o aplicativo:", ["🏠 Página Inicial","🏠 Controle", "🔧 Demanda e Modalidade Tatifária", "📊 Energia Reativa"])

if opcao == "🏠 Página Inicial":
    st.markdown("### Sistema para o cálculo da Análise de Demandas")
    st.write("Escolha uma das opções no menu lateral para continuar.")

elif opcao == "🏠 Controle":
    run_Controle()  # roda o app de otimização

elif opcao == "🔧 Demanda e Modalidade Tatifária":
    run_Projeto_2()  # roda o app de otimização

elif opcao == "📊 Energia Reativa":
    run_Reativo()  # roda o app de energia reativa
