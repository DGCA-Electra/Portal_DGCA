import base64
import pandas as pd
import streamlit as st

# --- Funções auxiliares ---
# Função para converter imagem em texto (Base64)
def convert_img_base64(caminho_imagem):
    try:
        with open(caminho_imagem, "rb") as image_file:
            encoded_string = base64.b64encode(image_file.read()).decode('utf-8')
        # Retorna o formato pronto para o HTML
        return f"data:image/png;base64,{encoded_string}" 
    except FileNotFoundError:
        print(f"ERRO: Não achei a imagem '{caminho_imagem}'. O PDF vai ficar sem logo.")
        return ""



def formatar_brl(df: pd.DataFrame, colunas: list, casas_decimais: list) -> pd.DataFrame:
    """
    Formata colunas numéricas para padrão brasileiro.
    - Substitui valores inválidos ou vazios por 0
    - Converte para string
    """
    df_formatado = df.copy()

    for col, decimais in zip(colunas, casas_decimais):
        if col not in df_formatado.columns:
            # Se a coluna não existir, cria preenchendo com 0
            df_formatado[col] = 0

        # Tenta converter para float, valores inválidos viram 0
        df_formatado[col] = pd.to_numeric(df_formatado[col], errors='coerce').fillna(0)

        # Formata para padrão brasileiro
        df_formatado[col] = df_formatado[col].apply(
            lambda x: f"{x:,.{decimais}f}".replace(",", "X").replace(".", ",").replace("X", ".")
        )

    return df_formatado


def format_brl_str(msg: str) -> str:
    """
    Formata uma string numérica para padrão brasileiro.
    Exemplo: "12345.67" -> "12.345,67"
    """
    try:
        return msg.replace(",", "!").replace(".", ",").replace("!", ".")
    except:
        return msg 
    

def sync_t1():
    st.session_state.t2 = st.session_state.t1
    st.session_state.t3 = st.session_state.t1

def sync_t2():
    st.session_state.t1 = st.session_state.t2
    st.session_state.t3 = st.session_state.t2

def sync_t3():
    st.session_state.t1 = st.session_state.t3
    st.session_state.t2 = st.session_state.t3