import streamlit as st
from scipy.optimize import minimize
import pandas as pd
import plotly.express as px
from io import BytesIO
import tempfile
import os
from io import BytesIO
from html2image import Html2Image
import math

def run_Projeto_2():

    st.title("Otimização de Demanda e Modalidade Tarifária")

    ##========================================= 1 DADOS====================================================##

    file_path = r"C:\DGCA\apps\Análise Demanda\dados.xlsx"
    df_cadastro = pd.read_excel(file_path, sheet_name="Dados_Cadastro")
    df_historico = pd.read_excel(file_path, sheet_name="Dados_Históricos")

    cliente = df_cadastro["Apelido"].dropna().unique().tolist()

    cliente_selecionado = st.selectbox("Escolha um cliente:", cliente)

    dados_historico = df_historico[df_historico["Apelido"] == cliente_selecionado]

    dados_cadastro = df_cadastro[df_cadastro["Apelido"] == cliente_selecionado].iloc[0]

    # 1. Converte os nomes de meses de pt para en na coluna 'Competência'
    meses_pt_en = {
        "jan": "jan", "fev": "feb", "mar": "mar", "abr": "apr",
        "mai": "may", "jun": "jun", "jul": "jul", "ago": "aug",
        "set": "sep", "out": "oct", "nov": "nov", "dez": "dec"
    }

    # Aplica substituição apenas uma vez (de forma robusta)
    dados_historico["Competência_en"] = dados_historico["Competência"].str.lower()
    for pt, en in meses_pt_en.items():
        dados_historico["Competência_en"] = dados_historico["Competência_en"].str.replace(f"^{pt}", en, regex=True)

    # 2. Converte corretamente com a coluna 'Competência_en'
    dados_historico["Data"] = pd.to_datetime(dados_historico["Competência_en"], format="%b/%Y")

    # 3. Cria coluna 'Mes_Ano' no formato desejado
    dados_historico["Mes_Ano"] = dados_historico["Data"].dt.strftime("%b/%Y").str.lower()


    # Dicionário de tradução de meses EN → PT
    meses_en_pt = {
        "jan": "jan", "feb": "fev", "mar": "mar", "apr": "abr",
        "may": "mai", "jun": "jun", "jul": "jul", "aug": "ago",
        "sep": "set", "oct": "out", "nov": "nov", "dec": "dez"
    }

    # Cria coluna 'Mes_Ano' com mês em inglês
    dados_historico["Mes_Ano"] = dados_historico["Data"].dt.strftime("%b/%Y").str.lower()

    # Traduz os meses para português
    for en, pt in meses_en_pt.items():
        dados_historico["Mes_Ano"] = dados_historico["Mes_Ano"].str.replace(f"^{en}", pt, regex=True)

    # Extrai e ordena os meses/anos únicos
    meses_ano_unicos = dados_historico["Mes_Ano"].unique()

    # Cria df_editavel com a coluna 'Mes_Ano'
    df_editavel = pd.DataFrame(
        {
            "Mes_Ano": [0.0] * len(meses_ano_unicos),
            "Consumo ponta (MWh)": [0.0] * len(meses_ano_unicos),
            "Consumo fora ponta (MWh)": [0.0] * len(meses_ano_unicos),
            "Demanda Lida Ponta (kW)": [0.0] * len(meses_ano_unicos),
            "Demanda Lida Fora Ponta (kW)": [0.0] * len(meses_ano_unicos),
        }
    )

    # Preenche df_editavel por mês/ano

    for i, mes_ano in enumerate(meses_ano_unicos):
        filtro_mes_ano = dados_historico[dados_historico["Mes_Ano"] == mes_ano]
        if not filtro_mes_ano.empty:
            df_editavel.loc[i, "Mes_Ano"] = filtro_mes_ano["Competência"].sum()
            df_editavel.loc[i, "Consumo ponta (MWh)"] = filtro_mes_ano["Consumo_ponta (MWh)"].sum()
            df_editavel.loc[i, "Consumo fora ponta (MWh)"] = filtro_mes_ano["Consumo_fora_ponta (MWh)"].sum()
            df_editavel.loc[i, "Demanda Lida Ponta (kW)"] = filtro_mes_ano["Demanda_registrada_ponta"].sum()
            df_editavel.loc[i, "Demanda Lida Fora Ponta (kW)"] = filtro_mes_ano["Demanda_registrada_fora_ponta"].sum()


    subgrupo = dados_cadastro["subgrupo"]
    modalidade = dados_cadastro["modalidade"]
    distribuidora = dados_cadastro["distribuidora"]
    icms = dados_cadastro ["ICMS"]


    tarifa_ponta_verde = dados_cadastro["tarifa_ponta_verde"]
    tarifa_fora_ponta_verde = dados_cadastro["tarifa_fora_ponta_verde"]
    tarifa_demanda_verde = dados_cadastro["tarifa_demanda_verde"]


    tarifa_ponta_azul = dados_cadastro["tarifa_ponta_azul"]
    tarifa_fora_ponta_azul = dados_cadastro["tarifa_fora_ponta_azul"]
    tarifa_demanda_ponta_azul = dados_cadastro["tarifa_demanda_ponta_azul"]
    tarifa_demanda_fora_ponta_azul = dados_cadastro["tarifa_demanda_fora_ponta_azul"]


    ##========================================= 1.1 INPUTS==================================================##
    with st.sidebar:
        
        st.selectbox("Subgrupo:", [subgrupo], disabled=True)

        st.selectbox("Modalidade:", [modalidade], disabled=True)
        
        st.selectbox("Distribuidora:", [distribuidora], disabled=True)

        desconto_tusd = st.number_input("Desconto TUSD", value=dados_cadastro["desconto_tusd"])

        icms = st.number_input("ICMS", value=dados_cadastro["ICMS"])
        
        piscofins = st.number_input("PISCOFINS", 0.05)
        
        varejo_comunhao = st.selectbox("Varejo ou Comunhão?", ["Não", "Sim"])

    col2_1, col2_2 = st.columns([2, 2])

    with col2_1:
            demanda_contratada_atual_ponta = st.number_input("Demanda Contratada Ponta:", value=dados_cadastro["demanda_ponta"])

    with col2_2:
            demanda_contratada_atual_fora_ponta = st.number_input("Demanda Contratada Fora Ponta:", value=dados_cadastro["demanda_fora_ponta"])


    if demanda_contratada_atual_ponta == 0:
        demanda_contratada_atual_ponta = demanda_contratada_atual_fora_ponta


    ##========================================= 1.1 EXIBIÇÃO DATAFRAME ==================================================##


    st.write ("Dados históricos:")

    df_editado = st.data_editor(df_editavel.copy(), num_rows="dynamic")

    dados_historico = df_editado
    ##========================================= 2 CÁLCULO ==================================================##

    # Solicitar valores de demanda contratada de acordo com a escolha
    if modalidade == "Verde":
        demanda_contratada_atual_verde = max(demanda_contratada_atual_fora_ponta, demanda_contratada_atual_ponta)
        demanda_contratada_atual_azul = [demanda_contratada_atual_verde, demanda_contratada_atual_verde]  # Preenchido automaticamente

    elif modalidade == "Azul":
        demanda_contratada_atual_azul_ponta = demanda_contratada_atual_ponta
        demanda_contratada_atual_azul_fora_ponta = demanda_contratada_atual_fora_ponta
        demanda_contratada_atual_azul = [demanda_contratada_atual_ponta, demanda_contratada_atual_fora_ponta]
        demanda_contratada_atual_verde = max(demanda_contratada_atual_ponta, demanda_contratada_atual_fora_ponta) 
        
    def calcular_custo_verde(demanda_contratada, dados_presentes):
        custos_mensais = []
        for _, linha in dados_presentes.iterrows():
            consumo_ponta = linha["Consumo ponta (MWh)"]
            consumo_fora_ponta = linha["Consumo fora ponta (MWh)"]
            demanda_ponta = linha["Demanda Lida Ponta (kW)"]
            demanda_fora_ponta = linha["Demanda Lida Fora Ponta (kW)"]
            # Calculando o custo de consumo
            custo_consumo = (consumo_ponta * ((tarifa_ponta_verde-tarifa_fora_ponta_verde)*(1-desconto_tusd)+tarifa_fora_ponta_verde)) + (consumo_fora_ponta * tarifa_fora_ponta_verde)
            custo_icms_consumo = ((consumo_ponta * tarifa_ponta_verde + consumo_fora_ponta * tarifa_fora_ponta_verde) /(1-piscofins)/(1-icms))*icms
            custo_piscofins_consumo = ((consumo_ponta * tarifa_ponta_verde + consumo_fora_ponta * tarifa_fora_ponta_verde)/(1-piscofins))*piscofins

            maior_demanda = max(demanda_ponta, demanda_fora_ponta)

            if maior_demanda > 1.05 * demanda_contratada:
                custo_demanda =  maior_demanda * tarifa_demanda_verde *(1-desconto_tusd)
                custo_ultrapassagem = (maior_demanda - demanda_contratada) * (tarifa_demanda_verde * 2)
                custo_icms_demanda = (((maior_demanda - demanda_contratada) * (tarifa_demanda_verde * 2) + maior_demanda * tarifa_demanda_verde) /(1-piscofins)/(1-icms))*icms
                custo_piscofins_demanda = ((maior_demanda * tarifa_demanda_verde + custo_ultrapassagem)/(1-piscofins))*piscofins
            else:
                custo_demanda = demanda_contratada * (tarifa_demanda_verde*(1-desconto_tusd))  
                custo_ultrapassagem = 0
                custo_icms_demanda = ((maior_demanda * tarifa_demanda_verde) /(1-piscofins)/(1-icms))*icms
                custo_piscofins_demanda = ((demanda_contratada * tarifa_demanda_verde)/(1-piscofins))*piscofins
            
            custo_piscofins = custo_piscofins_consumo + custo_piscofins_demanda
            custo_icms = custo_icms_consumo + custo_icms_demanda

            custos_mensais.append(custo_consumo + custo_demanda + custo_ultrapassagem + custo_icms + custo_piscofins)
        
        return sum(custos_mensais), custos_mensais

    def calcular_custo_azul(demanda_contratada, dados_presentes):
        demanda_contratada_ponta, demanda_contratada_fora_ponta = demanda_contratada
        custos_mensais = []
        for _, linha in dados_presentes.iterrows():
            consumo_ponta = linha["Consumo ponta (MWh)"]
            consumo_fora_ponta = linha["Consumo fora ponta (MWh)"]
            demanda_ponta = linha["Demanda Lida Ponta (kW)"]
            demanda_fora_ponta = linha["Demanda Lida Fora Ponta (kW)"]

            # Cálculo custo consumo

            custo_consumo = (consumo_ponta * tarifa_ponta_azul) + (consumo_fora_ponta * tarifa_fora_ponta_azul)
            custo_icms_consumo = ((custo_consumo) /(1-piscofins)/(1-icms))*icms
            custo_piscofins_consumo = custo_consumo / (1-piscofins) * piscofins
            
            # Cálculo custo demanda ponta

            if demanda_ponta > 1.05 * demanda_contratada_ponta:
                custo_demanda_ponta =  demanda_ponta * (tarifa_demanda_ponta_azul * (1-desconto_tusd))
                custo_ultrapasagem_ponta = (demanda_ponta - demanda_contratada_ponta) * (tarifa_demanda_ponta_azul * 2)
                custo_icms_demanda_ponta = (((demanda_ponta - demanda_contratada_ponta) * (tarifa_demanda_ponta_azul * 2) + (demanda_ponta * tarifa_demanda_ponta_azul)) /(1-piscofins)/(1-icms))*icms
                custo_piscofins_demanda_ponta = ((demanda_ponta * tarifa_demanda_ponta_azul + custo_ultrapasagem_ponta)/(1-piscofins))*piscofins
            else:
                custo_demanda_ponta = demanda_contratada_ponta * tarifa_demanda_ponta_azul * (1-desconto_tusd)
                custo_ultrapasagem_ponta = 0          
                custo_icms_demanda_ponta = ((demanda_ponta * tarifa_demanda_ponta_azul) /(1-piscofins)/(1-icms))*icms
                custo_piscofins_demanda_ponta = ((demanda_contratada_ponta * tarifa_demanda_ponta_azul)/(1-piscofins))*piscofins
        
        # Cálculo custo demanda fora ponta

            if demanda_fora_ponta > 1.05 * demanda_contratada_fora_ponta:
                custo_demanda_fora_ponta = demanda_fora_ponta * tarifa_demanda_fora_ponta_azul * (1-desconto_tusd)
                custo_ultrapasagem_fora_ponta = (demanda_fora_ponta - demanda_contratada_fora_ponta) * (tarifa_demanda_fora_ponta_azul * 2)
                custo_icms_demanda_fora_ponta = (((demanda_fora_ponta - demanda_contratada_fora_ponta) * (tarifa_demanda_fora_ponta_azul * 2) + (demanda_fora_ponta * tarifa_demanda_fora_ponta_azul)) /(1-piscofins)/(1-icms))*icms
                custo_piscofins_demanda_fora_ponta = ((demanda_fora_ponta * tarifa_demanda_fora_ponta_azul + custo_ultrapasagem_fora_ponta)/(1-piscofins))*piscofins
            else:
                custo_demanda_fora_ponta = demanda_contratada_fora_ponta * tarifa_demanda_fora_ponta_azul * (1-desconto_tusd) # Tarifa normal    
                custo_ultrapasagem_fora_ponta = 0 
                custo_icms_demanda_fora_ponta = ((demanda_fora_ponta * tarifa_demanda_fora_ponta_azul) /(1-piscofins)/(1-icms))*icms
                custo_piscofins_demanda_fora_ponta = ((demanda_contratada_fora_ponta * tarifa_demanda_fora_ponta_azul)/(1-piscofins))*piscofins
            
            custo_icms = custo_icms_consumo + custo_icms_demanda_ponta + custo_icms_demanda_fora_ponta
            custo_piscofins = custo_piscofins_consumo + custo_piscofins_demanda_ponta + custo_piscofins_demanda_fora_ponta
            custo_total = custo_consumo + custo_demanda_ponta + custo_ultrapasagem_ponta + custo_ultrapasagem_fora_ponta + custo_demanda_fora_ponta + custo_icms + custo_piscofins
            custos_mensais.append(custo_total)
        
        return sum(custos_mensais), custos_mensais

    def funcao_otimizacao_verde(demanda_contratada, dados_presentes):
        custo_anual, _ = calcular_custo_verde(demanda_contratada, dados_historico)
        return custo_anual

    def funcao_otimizacao_azul(demanda_contratada, dados_presentes):
        custo_anual, _ = calcular_custo_azul(demanda_contratada, dados_historico)
        return custo_anual

    ##========================================= 2.1 OTIMIZAÇÃO MODALIDADE VERDE ==================================================##
    demanda_contratada_atual_verde = max(demanda_contratada_atual_fora_ponta, demanda_contratada_atual_ponta)
    resultado_verde = minimize(lambda x: funcao_otimizacao_verde(x, dados_historico), demanda_contratada_atual_verde, bounds=[(0, 20000)], method='Powell')
    nova_demanda_contratada_verde = math.ceil(resultado_verde.x[0])
    novo_custo_total_verde, novo_custos_mensais_verde = calcular_custo_verde(nova_demanda_contratada_verde, dados_historico)

    ##========================================= 2.2 OTIMIZAÇÃO MODALIDADE AZUL ==================================================##
    resultado_azul = minimize(    lambda x: funcao_otimizacao_azul(x, dados_historico), demanda_contratada_atual_azul, bounds=[(0, 20000), (0, 20000)], method='Powell')
    nova_demanda_contratada_azul = [math.ceil(x) for x in resultado_azul.x]
    novo_custo_total_azul, novo_custos_mensais_azul = calcular_custo_azul(nova_demanda_contratada_azul, dados_historico)
    ##========================================= 2.3 CUSTO ATUAL ================================================================##

    if modalidade == "Verde":
        custo_atual, custo_mensal_atual = calcular_custo_verde (demanda_contratada_atual_verde, dados_historico)
    else:
        custo_atual, custo_mensal_atual = calcular_custo_azul (demanda_contratada_atual_azul, dados_historico)

    ##========================================= 3.1 ECONOMIA COM NOVOS VALORES ==================================================##

    st.markdown("---")

    st.markdown("#### Simular Cenários")

    if novo_custo_total_verde < novo_custo_total_azul:
        melhor_modalidade = "Verde"
        menor_custo_total,_ = calcular_custo_verde(nova_demanda_contratada_verde, dados_historico)
        custos_mensais_melhor = novo_custos_mensais_verde
        if subgrupo == "A2" or subgrupo == "A3":
            melhor_modalidade = "Azul"
            menor_custo_total,_ = calcular_custo_azul(nova_demanda_contratada_azul, dados_historico)
            custos_mensais_melhor = novo_custos_mensais_azul
            novo_custos_mensais_verde = [0] * len(dados_historico)

    else:
        melhor_modalidade = "Azul"
        menor_custo_total,_ = calcular_custo_azul(nova_demanda_contratada_azul, dados_historico)
        custos_mensais_melhor = novo_custos_mensais_azul

    economia = custo_atual - menor_custo_total
    economia_percentual = economia / custo_atual if custo_atual != 0 else 0


    with st.expander ("Novos Parâmetros"):
        melhor_modalidade = st.selectbox("Escolha a modalidade tarifária:", [melhor_modalidade, "Verde", "Azul"])

        if melhor_modalidade == "Verde":
            nova_demanda_contratada_verde = st.number_input(
                "Nova Demanda Contratada (kW) - Verde", value=nova_demanda_contratada_verde, step=1)
            nova_demanda_contratada_azul[0] = st.number_input(
                "Nova Demanda Ponta (kW) - (Apenas Comparação Modalidade)", value=nova_demanda_contratada_azul[0], step=1)
            nova_demanda_contratada_azul[1] = nova_demanda_contratada_verde

        else:
            nova_demanda_contratada_azul[0] = st.number_input(
                "Nova Demanda Ponta (kW) - Azul", value=nova_demanda_contratada_azul[0], step=1)
            nova_demanda_contratada_azul[1] = st.number_input(
                "Nova Demanda Fora Ponta (kW) - Azul", value=nova_demanda_contratada_azul[1], step=1)
            nova_demanda_contratada_verde = max(nova_demanda_contratada_azul[0], nova_demanda_contratada_azul[1])

    novo_custo_total_azul, novo_custos_mensais_azul = calcular_custo_azul(nova_demanda_contratada_azul, dados_historico)
    novo_custo_total_verde, novo_custos_mensais_verde = calcular_custo_verde(nova_demanda_contratada_verde, dados_historico)

    if melhor_modalidade == "Verde":
        menor_custo_total,_ = calcular_custo_verde(nova_demanda_contratada_verde, dados_historico)
        custos_mensais_melhor = novo_custos_mensais_verde
    else:
        menor_custo_total,_ = calcular_custo_azul(nova_demanda_contratada_azul, dados_historico)
        custos_mensais_melhor = novo_custos_mensais_azul

    economia = custo_atual - menor_custo_total
    economia_percentual = economia / custo_atual if custo_atual != 0 else 0



    # Resultado base centralizado



    ##========================================= 3 APRESENTAÇÃO DE RESULTADOS ==================================================##
    def format_currency(valor):
        return f"R$ {valor:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

    def format_kw(valor):
        return f"{valor:,.0f}".replace(",", ".")

    # Layout em colunas com cards personalizados
    col_antes, col_depois = st.columns(2)

    with col_antes:
        st.markdown("####  Cenário Atual")
        with st.container():
            if modalidade == "Verde":
                st.markdown(f"""
            <div style="border:1px solid #ccc;padding:10px;border-radius:8px;">
                <b>Demanda Ponta (kW):</b> {format_kw(0)}<br>
                <b>Demanda Fora Ponta (kW):</b> {format_kw(demanda_contratada_atual_fora_ponta)}<br>
                <b>Modalidade:</b> {modalidade}<br>
                <b>Custo Total:</b> {format_currency(custo_atual)}
            </div>
            """, unsafe_allow_html=True)
            else:
                st.markdown(f"""
            <div style="border:1px solid #ccc;padding:10px;border-radius:8px;">
                <b>Demanda Ponta (kW):</b> {format_kw(demanda_contratada_atual_ponta)}<br>
                <b>Demanda Fora Ponta (kW):</b> {format_kw(demanda_contratada_atual_fora_ponta)}<br>
                <b>Modalidade:</b> {modalidade}<br>
                <b>Custo Total:</b> {format_currency(custo_atual)}
                </div>
            """, unsafe_allow_html=True)


    with col_depois:
        st.markdown("####  Cenário Sugerido")
        with st.container():
            if melhor_modalidade == "Verde":
                nova_demanda_texto =f""" <b>Demanda Sugerida Ponta (kW):</b> {0}<br>
                <b>Demanda Sugerida Fora Ponta (kW):</b> {nova_demanda_contratada_verde}"""
            else:
                nova_demanda_texto = f"""<b>Demanda Sugerida Ponta (kW)</b> {nova_demanda_contratada_azul[0]}<br>
                <b>Demanda Sugerida Fora Ponta (kW)</b> {nova_demanda_contratada_azul[1]}
                """
            st.markdown(f"""
            <div style="border:1px solid #ccc;padding:10px;border-radius:8px;">
                {nova_demanda_texto}<br>
                <b>Modalidade Sugerida:</b> {melhor_modalidade}<br>
                <b>Novo Custo Total:</b> {format_currency(menor_custo_total)}
            </div>
            """, unsafe_allow_html=True)

    st.markdown("---")
    st.markdown("####  Economia Estimada")

    col1, col2, col3 = st.columns([0.5, 2, 0.5])
    with col2:
        st.markdown(f"""
        <div style="
            text-align:center;
            border:1px solid #1f77b4;
            padding:24px;
            border-radius:15px;
            background-color:;
            font-size:22px;
            box-shadow: 2px 2px 12px rgba(0,0,0,0.1);
        ">
            <p style="margin:0;"><b>{format_currency(economia)}</b></p>
            <p style="margin:0;">({economia_percentual*100:.2f}%)</p>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("---")

    ##========================================= 4 MOMÓRIA DE CÁLCULO ==================================================##
    st.markdown("#### Memória de Cálculo")

    custo_consumo_ponta_lista = []
    custo_consumo_fora_ponta_lista = []
    custo_demanda_lista  = []
    custo_demanda_ponta_lista  = []
    custo_demanda_fora_ponta_lista = []
    custo_ultrapassagem_lista = []
    custo_ultrapassagem_ponta_lista = []
    custo_ultrapassagem_fora_ponta_lista = []
    custo_icms_lista  = []
    custo_piscofins_lista = []

    df_atual = pd.DataFrame({})

    df_atual["Mês"] = dados_historico ["Mes_Ano"]


    if modalidade == "Verde":

        for _, linha in dados_historico.iterrows():
            consumo_ponta = linha["Consumo ponta (MWh)"]
            consumo_fora_ponta = linha["Consumo fora ponta (MWh)"]
            demanda_ponta = linha["Demanda Lida Ponta (kW)"]
            demanda_fora_ponta = linha["Demanda Lida Fora Ponta (kW)"]
            # Calculando o custo de consumo
            custo_consumo_ponta = (consumo_ponta * ((tarifa_ponta_verde-tarifa_ponta_azul)*(1-desconto_tusd)+tarifa_ponta_azul))
            custo_consumo_fora_ponta = consumo_fora_ponta * tarifa_fora_ponta_verde
            custo_icms_consumo = ((consumo_ponta * tarifa_ponta_verde + custo_consumo_fora_ponta) /(1-piscofins)/(1-icms))*icms
            custo_piscofins_consumo = ((consumo_ponta * tarifa_ponta_verde + consumo_fora_ponta * tarifa_fora_ponta_verde)/(1-piscofins))*piscofins

            maior_demanda = max(demanda_ponta, demanda_fora_ponta)

            if maior_demanda > 1.05 * demanda_contratada_atual_verde:
                custo_demanda =  maior_demanda * tarifa_demanda_verde *(1-desconto_tusd)
                custo_ultrapassagem = (maior_demanda - demanda_contratada_atual_verde) * (tarifa_demanda_verde * 2)
                custo_icms_demanda = (((maior_demanda - demanda_contratada_atual_verde) * (tarifa_demanda_verde * 2) + maior_demanda * tarifa_demanda_verde) /(1-piscofins)/(1-icms))*icms
                custo_piscofins_demanda = ((maior_demanda * tarifa_demanda_verde + custo_ultrapassagem)/(1-piscofins))*piscofins

            else:
                custo_demanda = demanda_contratada_atual_verde * (tarifa_demanda_verde*(1-desconto_tusd))  
                custo_ultrapassagem = 0
                custo_icms_demanda = ((maior_demanda * tarifa_demanda_verde) /(1-piscofins)/(1-icms))*icms
                custo_piscofins_demanda = ((demanda_contratada_atual_verde * tarifa_demanda_verde)/(1-piscofins))*piscofins

            
            custo_piscofins = custo_piscofins_consumo + custo_piscofins_demanda
            custo_icms = custo_icms_consumo + custo_icms_demanda

            custo_consumo_ponta_lista.append (custo_consumo_ponta)
            custo_consumo_fora_ponta_lista.append (custo_consumo_fora_ponta)
            custo_demanda_lista.append (custo_demanda)
            custo_ultrapassagem_lista.append (custo_ultrapassagem)
            custo_icms_lista.append (custo_icms)
            custo_piscofins_lista.append (custo_piscofins)

        df_atual["Custo Consumo Ponta"] = custo_consumo_ponta_lista
        df_atual["Custo Consumo Fora Ponta"] = custo_consumo_fora_ponta_lista
        df_atual["Custo Demanda"] = custo_demanda_lista
        df_atual["Custo Ultrapassagem"] = custo_ultrapassagem_lista
        df_atual["Custo ICMS"] = custo_icms_lista
        df_atual["Custo PIS/COFINS"] = custo_piscofins_lista

    else:
        
        for _, linha in dados_historico.iterrows():
            consumo_ponta = linha["Consumo ponta (MWh)"]
            consumo_fora_ponta = linha["Consumo fora ponta (MWh)"]
            demanda_ponta = linha["Demanda Lida Ponta (kW)"]
            demanda_fora_ponta = linha["Demanda Lida Fora Ponta (kW)"]

            # Cálculo custo consumo

            custo_consumo_ponta = (consumo_ponta * tarifa_ponta_azul)
            custo_consumo_fora_ponta = (consumo_fora_ponta * tarifa_fora_ponta_azul)
            custo_icms_consumo = (((consumo_ponta * tarifa_ponta_azul) + (consumo_fora_ponta * tarifa_fora_ponta_azul)) /(1-piscofins)/(1-icms))*icms
            custo_piscofins_consumo = (custo_consumo_ponta + custo_consumo_fora_ponta) / (1-piscofins) * piscofins
            # Cálculo custo demanda ponta

            if demanda_ponta > 1.05 * demanda_contratada_atual_ponta:
                custo_demanda_ponta =  demanda_ponta * tarifa_demanda_ponta_azul * (1-desconto_tusd)
                custo_ultrapasagem_ponta = (demanda_ponta - demanda_contratada_atual_ponta) * (tarifa_demanda_ponta_azul * 2)
                custo_icms_demanda_ponta = (((demanda_ponta - demanda_contratada_atual_ponta) * (tarifa_demanda_ponta_azul * 2) + demanda_ponta * tarifa_demanda_ponta_azul) /(1-piscofins)/(1-icms))*icms
                custo_piscofins_demanda_ponta = ((demanda_ponta * tarifa_demanda_ponta_azul + custo_ultrapasagem_ponta)/(1-piscofins))*piscofins

            else:
                custo_demanda_ponta = demanda_contratada_atual_ponta * tarifa_demanda_ponta_azul * (1-desconto_tusd)
                custo_ultrapasagem_ponta = 0          
                custo_icms_demanda_ponta = ((demanda_ponta * tarifa_demanda_ponta_azul) /(1-piscofins)/(1-icms))*icms
                custo_piscofins_demanda_ponta = ((demanda_contratada_atual_ponta * tarifa_demanda_ponta_azul)/(1-piscofins))*piscofins

        
        # Cálculo custo demanda fora ponta

            if demanda_fora_ponta > 1.05 * demanda_contratada_atual_fora_ponta:
                custo_demanda_fora_ponta = demanda_fora_ponta * tarifa_demanda_fora_ponta_azul * (1-desconto_tusd)
                custo_ultrapasagem_fora_ponta = (demanda_fora_ponta - demanda_contratada_atual_fora_ponta) * (tarifa_demanda_fora_ponta_azul * 2)
                custo_icms_demanda_fora_ponta = (((demanda_fora_ponta - demanda_contratada_atual_fora_ponta) * (tarifa_demanda_fora_ponta_azul * 2) + demanda_fora_ponta * tarifa_demanda_fora_ponta_azul) /(1-piscofins)/(1-icms))*icms
                custo_piscofins_demanda_fora_ponta = ((demanda_fora_ponta * tarifa_demanda_fora_ponta_azul + custo_ultrapasagem_fora_ponta)/(1-piscofins))*piscofins

            else:
                custo_demanda_fora_ponta = demanda_contratada_atual_fora_ponta * tarifa_demanda_fora_ponta_azul * (1-desconto_tusd) # Tarifa normal    
                custo_ultrapasagem_fora_ponta = 0 
                custo_icms_demanda_fora_ponta = ((demanda_fora_ponta * tarifa_demanda_fora_ponta_azul) /(1-piscofins)/(1-icms))*icms
                custo_piscofins_demanda_fora_ponta = ((demanda_contratada_atual_fora_ponta * tarifa_demanda_fora_ponta_azul)/(1-piscofins))*piscofins

            
            custo_icms = custo_icms_consumo + custo_icms_demanda_ponta + custo_icms_demanda_fora_ponta
            custo_piscofins = custo_piscofins_consumo + custo_piscofins_demanda_ponta + custo_piscofins_demanda_fora_ponta
            custo_total = custo_consumo_ponta + custo_consumo_fora_ponta + custo_demanda_ponta + custo_ultrapasagem_ponta + custo_ultrapasagem_fora_ponta + custo_demanda_fora_ponta + custo_icms + custo_piscofins
            
            custo_consumo_ponta_lista.append (custo_consumo_ponta)
            custo_consumo_fora_ponta_lista.append (custo_consumo_fora_ponta)
            custo_demanda_ponta_lista.append (custo_demanda_ponta)
            custo_demanda_fora_ponta_lista.append (custo_demanda_fora_ponta)
            custo_ultrapassagem_ponta_lista.append (custo_ultrapasagem_ponta)
            custo_ultrapassagem_fora_ponta_lista.append (custo_ultrapasagem_fora_ponta)
            custo_icms_lista.append (custo_icms)
            custo_piscofins_lista.append (custo_piscofins)

        
        df_atual["Custo Consumo Ponta"] = custo_consumo_ponta_lista
        df_atual["Custo Consumo Fora Ponta"] = custo_consumo_fora_ponta_lista
        df_atual["Custo Demanda Ponta"] = custo_demanda_ponta_lista
        df_atual["Custo Demanda Fora Ponta"] = custo_demanda_fora_ponta_lista
        df_atual["Custo Ultrapassagem Ponta"] = custo_ultrapassagem_ponta_lista
        df_atual["Custo Ultrapassagem Fora Ponta"] = custo_ultrapassagem_fora_ponta_lista
        df_atual["Custo ICMS"] = custo_icms_lista
        df_atual["Custo PIS/COFINS"] = custo_piscofins_lista


    df_formatado = df_atual.applymap(lambda x: f"{x:,.2f}".replace(",", "v").replace(".", ",").replace("v", ".") if isinstance(x, (int, float)) else x)

    custo_consumo_ponta_lista_otimizado = []
    custo_consumo_fora_ponta_lista_otimizado = []
    custo_demanda_lista_otimizado  = []
    custo_demanda_ponta_lista_otimizado  = []
    custo_demanda_fora_ponta_lista_otimizado = []
    custo_ultrapassagem_lista_otimizado = []
    custo_ultrapassagem_ponta_lista_otimizado = []
    custo_ultrapassagem_fora_ponta_lista_otimizado = []
    custo_icms_lista_otimizado  = []
    custo_piscofins_lista_otimizado = []


    df_otimizado = pd.DataFrame({})

    df_otimizado["Mês"] = dados_historico ["Mes_Ano"]


    if melhor_modalidade == "Verde":

        for _, linha in dados_historico.iterrows():
            consumo_ponta = linha["Consumo ponta (MWh)"]
            consumo_fora_ponta = linha["Consumo fora ponta (MWh)"]
            demanda_ponta = linha["Demanda Lida Ponta (kW)"]
            demanda_fora_ponta = linha["Demanda Lida Fora Ponta (kW)"]
            # Calculando o custo de consumo
            custo_consumo_ponta = (consumo_ponta * ((tarifa_ponta_verde-tarifa_fora_ponta_verde)*(1-desconto_tusd)+tarifa_fora_ponta_verde))
            custo_consumo_fora_ponta = consumo_fora_ponta * tarifa_fora_ponta_verde
            custo_icms_consumo = ((consumo_ponta * tarifa_ponta_verde + custo_consumo_fora_ponta) /(1-piscofins)/(1-icms))*icms
            custo_piscofins_consumo = ((consumo_ponta * tarifa_ponta_verde + consumo_fora_ponta * tarifa_fora_ponta_verde)/(1-piscofins))*piscofins

            maior_demanda = max(demanda_ponta, demanda_fora_ponta)

            if maior_demanda > 1.05 * nova_demanda_contratada_verde:
                custo_demanda =  maior_demanda * tarifa_demanda_verde *(1-desconto_tusd)
                custo_ultrapassagem = (maior_demanda - nova_demanda_contratada_verde) * (tarifa_demanda_verde * 2)
                custo_icms_demanda = (((maior_demanda - nova_demanda_contratada_verde) * (tarifa_demanda_verde * 2) + maior_demanda * tarifa_demanda_verde) /(1-piscofins)/(1-icms))*icms
                custo_piscofins_demanda = ((maior_demanda * tarifa_demanda_verde + custo_ultrapassagem)/(1-piscofins))*piscofins

            else:
                custo_demanda = nova_demanda_contratada_verde * (tarifa_demanda_verde*(1-desconto_tusd))  
                custo_ultrapassagem = 0
                custo_icms_demanda = ((maior_demanda * tarifa_demanda_verde) /(1-piscofins)/(1-icms))*icms
                custo_piscofins_demanda = ((nova_demanda_contratada_verde * tarifa_demanda_verde)/(1-piscofins))*piscofins

            
            custo_piscofins = custo_piscofins_consumo + custo_piscofins_demanda 
            custo_icms = custo_icms_consumo + custo_icms_demanda

            custo_consumo_ponta_lista_otimizado.append (custo_consumo_ponta)
            custo_consumo_fora_ponta_lista_otimizado.append (custo_consumo_fora_ponta)
            custo_demanda_lista_otimizado.append (custo_demanda)
            custo_ultrapassagem_lista_otimizado.append (custo_ultrapassagem)
            custo_icms_lista_otimizado.append (custo_icms)
            custo_piscofins_lista_otimizado.append (custo_piscofins)

        df_otimizado["Custo Consumo Ponta"] = custo_consumo_ponta_lista_otimizado
        df_otimizado["Custo Consumo Fora Ponta"] = custo_consumo_fora_ponta_lista_otimizado
        df_otimizado["Custo Demanda"] = custo_demanda_lista_otimizado
        df_otimizado["Custo Ultrapassagem"] = custo_ultrapassagem_lista_otimizado
        df_otimizado["Custo ICMS"] = custo_icms_lista_otimizado
        df_otimizado["Custo PIS/COFINS"] = custo_piscofins_lista_otimizado

    else:
        
        for _, linha in dados_historico.iterrows():
            consumo_ponta = linha["Consumo ponta (MWh)"]
            consumo_fora_ponta = linha["Consumo fora ponta (MWh)"]
            demanda_ponta = linha["Demanda Lida Ponta (kW)"]
            demanda_fora_ponta = linha["Demanda Lida Fora Ponta (kW)"]

            # Cálculo custo consumo

            custo_consumo_ponta = (consumo_ponta * tarifa_ponta_azul)
            custo_consumo_fora_ponta = (consumo_fora_ponta * tarifa_fora_ponta_azul)
            custo_icms_consumo = (((consumo_ponta * tarifa_ponta_azul) + (consumo_fora_ponta * tarifa_fora_ponta_azul)) /(1-piscofins)/(1-icms))*icms
            custo_piscofins_consumo = (custo_consumo_ponta + custo_consumo_fora_ponta) / (1-piscofins) * piscofins

            # Cálculo custo demanda ponta

            if demanda_ponta > 1.05 * nova_demanda_contratada_azul[0]:
                custo_demanda_ponta =  demanda_ponta * (tarifa_demanda_ponta_azul * (1-desconto_tusd))
                custo_ultrapasagem_ponta = (demanda_ponta - nova_demanda_contratada_azul[0]) * (tarifa_demanda_ponta_azul * 2)
                custo_icms_demanda_ponta = (((demanda_ponta - nova_demanda_contratada_azul[0]) * (tarifa_demanda_ponta_azul * 2) + demanda_ponta * tarifa_demanda_ponta_azul) /(1-piscofins)/(1-icms))*icms
                custo_piscofins_demanda_ponta = ((demanda_ponta * tarifa_demanda_ponta_azul + custo_ultrapasagem_ponta)/(1-piscofins))*piscofins

            else:
                custo_demanda_ponta = nova_demanda_contratada_azul[0] * tarifa_demanda_ponta_azul * (1-desconto_tusd)
                custo_ultrapasagem_ponta = 0          
                custo_icms_demanda_ponta = ((demanda_ponta * tarifa_demanda_ponta_azul) /(1-piscofins)/(1-icms))*icms
                custo_piscofins_demanda_ponta = ((nova_demanda_contratada_azul[0] * tarifa_demanda_ponta_azul)/(1-piscofins))*piscofins

        
        # Cálculo custo demanda fora ponta

            if demanda_fora_ponta > 1.05 * nova_demanda_contratada_azul[1]:
                custo_demanda_fora_ponta = demanda_fora_ponta * tarifa_demanda_fora_ponta_azul * (1-desconto_tusd)
                custo_ultrapasagem_fora_ponta = (demanda_fora_ponta - nova_demanda_contratada_azul[1]) * (tarifa_demanda_fora_ponta_azul * 2)
                custo_icms_demanda_fora_ponta = (((demanda_fora_ponta - nova_demanda_contratada_azul[1]) * (tarifa_demanda_fora_ponta_azul * 2) + demanda_fora_ponta * tarifa_demanda_fora_ponta_azul) /(1-piscofins)/(1-icms))*icms
                custo_piscofins_demanda_fora_ponta = ((demanda_fora_ponta * tarifa_demanda_fora_ponta_azul + custo_ultrapasagem_fora_ponta)/(1-piscofins))*piscofins

            else:
                custo_demanda_fora_ponta = nova_demanda_contratada_azul[1] * tarifa_demanda_fora_ponta_azul * (1-desconto_tusd) # Tarifa normal    
                custo_ultrapasagem_fora_ponta = 0 
                custo_icms_demanda_fora_ponta = ((demanda_fora_ponta * tarifa_demanda_fora_ponta_azul) /(1-piscofins)/(1-icms))*icms
                custo_piscofins_demanda_fora_ponta = ((nova_demanda_contratada_azul[1] * tarifa_demanda_fora_ponta_azul)/(1-piscofins))*piscofins

            custo_icms = custo_icms_consumo + custo_icms_demanda_ponta + custo_icms_demanda_fora_ponta
            custo_piscofins = custo_piscofins_consumo + custo_piscofins_demanda_ponta + custo_piscofins_demanda_fora_ponta
            custo_total = custo_consumo_ponta + custo_consumo_fora_ponta + custo_demanda_ponta + custo_ultrapasagem_ponta + custo_ultrapasagem_fora_ponta + custo_demanda_fora_ponta + custo_icms + custo_piscofins
            
            custo_consumo_ponta_lista_otimizado.append (custo_consumo_ponta)
            custo_consumo_fora_ponta_lista_otimizado.append (custo_consumo_fora_ponta)
            custo_demanda_ponta_lista_otimizado.append (custo_demanda_ponta)
            custo_demanda_fora_ponta_lista_otimizado.append (custo_demanda_fora_ponta)
            custo_ultrapassagem_ponta_lista_otimizado.append (custo_ultrapasagem_ponta)
            custo_ultrapassagem_fora_ponta_lista_otimizado.append (custo_ultrapasagem_fora_ponta)
            custo_icms_lista_otimizado.append (custo_icms)
            custo_piscofins_lista_otimizado.append (custo_piscofins)

        
        df_otimizado["Custo Consumo Ponta"] = custo_consumo_ponta_lista_otimizado
        df_otimizado["Custo Consumo Fora Ponta"] = custo_consumo_fora_ponta_lista_otimizado
        df_otimizado["Custo Demanda Ponta"] = custo_demanda_ponta_lista_otimizado
        df_otimizado["Custo Demanda Fora Ponta"] = custo_demanda_fora_ponta_lista_otimizado
        df_otimizado["Custo Ultrapassagem Ponta"] = custo_ultrapassagem_ponta_lista_otimizado
        df_otimizado["Custo Ultrapassagem Fora Ponta"] = custo_ultrapassagem_fora_ponta_lista_otimizado
        df_otimizado["Custo ICMS"] = custo_icms_lista_otimizado
        df_otimizado["Custo PIS/COFINS"] = custo_piscofins_lista_otimizado



    df_formatado_otimizado = df_otimizado.applymap(lambda x: f"{x:,.2f}".replace(",", "v").replace(".", ",").replace("v", ".") if isinstance(x, (int, float)) else x)

    with st.expander(" Custo Mensal - Cenário Atual"):
        st.dataframe(df_formatado, use_container_width=True)

    with st.expander(" Custo Mensal - Cenário Otimizado"):
        st.data_editor(df_formatado_otimizado, num_rows="fixed",key="editor_2")

    st.markdown("---")
    ##========================================= GRÁFICOS 1 E 2 ==================================================##
    st.markdown("#### Gráficos")

    abas = st.tabs([
        "📈 Demanda Contratada",
        "💰 Comparativo Modalidade Tarifária",
        "📊 Custo Atual vs Otimizado",
        "🧾 Composição de Custos"
    ])


    if melhor_modalidade == "Verde":

        nova_demanda_contratada_ponta = nova_demanda_contratada_verde
    else:
        nova_demanda_contratada_ponta = nova_demanda_contratada_azul [0]
        nova_demanda_contratada_verde = nova_demanda_contratada_azul [1]



    fig1 = px.bar(dados_historico, x="Mes_Ano", y="Demanda Lida Fora Ponta (kW)", color_discrete_sequence=["purple"])
    fig1.add_scatter(x=dados_historico["Mes_Ano"], y=[demanda_contratada_atual_fora_ponta] * len(dados_historico), mode="lines", name="Demanda Contratada Atual", line=dict(color="gray"))
    fig1.add_scatter(x=dados_historico["Mes_Ano"], y=[nova_demanda_contratada_verde] * len(dados_historico), mode="lines", name="Nova Demanda Contratada", line=dict(color="yellow", dash="dash"))
    fig1.update_layout(
        title="Contrato x Leitura - Demanda Fora Ponta",
        xaxis_title="",
        yaxis_title="Demanda (kW)",
        legend=dict(orientation="h", yanchor="bottom", y=-0.4, xanchor="center", x=0.5) # Move a legenda para baixo
    )

    fig1.update_traces(
        textposition="inside",
        insidetextanchor="middle",
        texttemplate="%{y:.0f}",  # <- usar y aqui mostra o valor real
        selector=dict(type="bar"),
        textangle=90
    )

        

    fig = px.bar(dados_historico, x="Mes_Ano", y="Demanda Lida Ponta (kW)", color_discrete_sequence=["teal"])
    fig.add_scatter(x=dados_historico["Mes_Ano"], y=[demanda_contratada_atual_ponta] * len(dados_historico), mode="lines", name="Demanda Contratada Atual", line=dict(color="gray"))
    fig.add_scatter(x=dados_historico["Mes_Ano"], y=[nova_demanda_contratada_ponta] * len(dados_historico), mode="lines", name="Nova Demanda Contratada", line=dict(color="yellow", dash="dash"))
    fig.update_layout(
        title="Contrato x Leitura - Demanda Ponta",
        xaxis_title="",
        yaxis_title="Demanda (kW)",
        legend=dict(orientation="h", yanchor="bottom", y=-0.4, xanchor="center", x=0.5)  # Move a legenda para baixo
    )
    fig.update_traces(
        textposition="inside",
        insidetextanchor="middle",
        texttemplate="%{y:.0f}",  # <- usar y aqui mostra o valor real
        selector=dict(type="bar"),
        textangle=90
    )

    with abas[0]:
        col3_1, col3_2 = st.columns([2, 2])
        with col3_1:(st.plotly_chart(fig))
        with col3_2:(st.plotly_chart(fig1))

    ##========================================= GRÁFICOS 3 E 4 ==================================================##

    # Definir os meses de 1 a 12
    meses = dados_historico.index

    # Criar DataFrame para o gráfico de comparação de custos mensais (Modalidade Verde vs Azul)
    n_meses = len(dados_historico)

    df_custos_mensais = pd.DataFrame({
        "Mês": list(dados_historico["Mes_Ano"]) * 2,
        "Custo Mensal (R$)": novo_custos_mensais_verde + novo_custos_mensais_azul,
        "Modalidade": ["Demanda Verde Otimizada"] * n_meses + ["Demanda Azul Otimizada"] * n_meses
    })

    # Criar gráfico de barras com Plotly Express
    fig5 = px.bar(df_custos_mensais, x="Mês", y="Custo Mensal (R$)", color="Modalidade",
                title=f"Comparação de Custos Mensais por Modalidade",
                labels={"Mês": "", "Custo Mensal (R$)": "Custo Mensal (R$)"},
                barmode="group",
                color_discrete_map={"Demanda Verde Otimizada": "green", "Demanda Azul Otimizada": "blue"})

    fig5.update_layout(xaxis_title_font=dict(size=12),
                    yaxis_title_font=dict(size=12),
                    legend_font=dict(size=12),
                    template="plotly_white",
                    legend=dict(orientation="h", yanchor="top", y=-0.3))  # Legenda abaixo do gráfico

    # Criar DataFrame para o gráfico de comparação dos custos totais anuais
    economia_verde_grafico,_ = calcular_custo_verde(nova_demanda_contratada_verde, dados_historico)
    economia_azul_grafico,_ = calcular_custo_azul(nova_demanda_contratada_azul, dados_historico)

    economia_verde = (custo_atual-economia_verde_grafico)/custo_atual
    economia_azul = (custo_atual-economia_azul_grafico)/custo_atual
    df_custos_totais = pd.DataFrame({
        "Modalidade": ["Modalidade Verde", "Modalidade Azul"],
        "Custo Total Anual (R$)": [novo_custo_total_verde, novo_custo_total_azul],
        "Economia": [economia_verde*100, economia_azul*100]
    })

    # Criar gráfico de barras com Plotly Express
    fig6 = px.bar(df_custos_totais, x="Modalidade", y="Custo Total Anual (R$)", 
                title="Comparação Custo Total por Modalidade",
                labels={"Modalidade": "Modalidade", "Custo Total Anual (R$)": "Custo Total Anual (R$)"},
                color="Modalidade",
                color_discrete_map={"Modalidade Verde": "green", "Modalidade Azul": "blue"},
                text="Economia")

    fig6.update_layout(xaxis_title_font=dict(size=12),
                    yaxis_title_font=dict(size=12),
                    legend_font=dict(size=12),
                    template="plotly_white",
                    legend=dict(orientation="h", yanchor="top", y=-0.2))  # Legenda abaixo do gráfico
    
    fig6.update_traces(
        textposition="inside",
        insidetextanchor="middle",
        texttemplate="Economia: %{text:.2f}%",  # <- usar y aqui mostra o valor real
        selector=dict(type="bar"),
        textangle=0
    )

    # Exibir gráficos no Streamlit

    with abas[1]:
        col4_1, col4_2 = st.columns([4, 4])

        with col4_1:
            st.plotly_chart(fig5, use_container_width=True)

        with col4_2:
            st.plotly_chart(fig6, use_container_width=True)

    ##========================================= GRÁFICOS 5 ==================================================##

    # Criar DataFrame para o gráfico de comparação de custos mensais (Atual vs Otimizado)
    n_meses = len(dados_historico)
    meses = dados_historico.index

    df_custos_mensais_atual_otimizado = pd.DataFrame({
        "Mês": list(dados_historico["Mes_Ano"]) * 2,
        "Custo Mensal (R$)": custo_mensal_atual + custos_mensais_melhor,
        " ": ["Custo Mensal Atual"] * n_meses + ["Custo Mensal Otimizado"] * n_meses
    })

    # Criar gráfico de barras com Plotly Express
    fig8 = px.bar(
        df_custos_mensais_atual_otimizado,
        x="Mês",
        y="Custo Mensal (R$)",
        color=" ",
        title=f"Comparação de Custos Mensais (Otimizado: {melhor_modalidade})",
        labels={"Mês": "", "Custo Mensal (R$)": "Custo Mensal (R$)"},
        barmode="group",
        color_discrete_map={
            "Custo Mensal Atual": "gray",
            "Custo Mensal Otimizado": "teal"
        }
    )

    # Atualizar layout: legenda abaixo e centralizada
    fig8.update_layout(xaxis_title_font=dict(size=12),
        yaxis_title_font=dict(size=12),
        legend_font=dict(size=12),
        legend=dict(
            orientation="h",     # horizontal
            yanchor="bottom",
            y=-0.3,              # distância abaixo do gráfico
            xanchor="center",
            x=0.5
        ),
        margin=dict(b=100),      # espaço extra na parte inferior
        template="plotly_white"
    )

    # Exibir gráfico no Streamlit

    with abas[2]:
        st.plotly_chart(fig8, use_container_width=True)


    ##========================================= GRÁFICOS 6 ==================================================##

    df_atual_dash = pd.DataFrame({})
    if modalidade == "Verde":
        
        df_atual_dash["Custo Consumo"] = df_atual["Custo Consumo Ponta"] + df_atual["Custo Consumo Fora Ponta"]
        df_atual_dash["Custo Demanda"] = custo_demanda_lista
        df_atual_dash["Custo Ultrapassagem"] = custo_ultrapassagem_lista
        df_atual_dash["Custo ICMS"] = custo_icms_lista
        df_atual_dash["Custo PIS/COFINS"] = custo_piscofins_lista
    else:
        
        df_atual_dash["Custo Consumo"] = df_atual["Custo Consumo Ponta"] + df_atual["Custo Consumo Fora Ponta"]
        df_atual_dash["Custo Demanda"] = df_atual["Custo Demanda Ponta"] + df_atual["Custo Demanda Fora Ponta"]
        df_atual_dash["Custo Ultrapassagem"] = df_atual["Custo Ultrapassagem Ponta"] + df_atual["Custo Ultrapassagem Fora Ponta"]
        df_atual_dash["Custo ICMS"] = custo_icms_lista
        df_atual_dash["Custo PIS/COFINS"] = custo_piscofins_lista


    df_otimizado_dash = pd.DataFrame({})

    if melhor_modalidade == "Verde":
        
        df_otimizado_dash["Custo Consumo"] = df_otimizado["Custo Consumo Ponta"] + df_otimizado["Custo Consumo Fora Ponta"]
        df_otimizado_dash["Custo Demanda"] = custo_demanda_lista_otimizado
        df_otimizado_dash["Custo Ultrapassagem"] = custo_ultrapassagem_lista_otimizado
        df_otimizado_dash["Custo ICMS"] = custo_icms_lista_otimizado
        df_otimizado_dash["Custo PIS/COFINS"] = custo_piscofins_lista_otimizado
    else:
        
        df_otimizado_dash["Custo Consumo"] = df_otimizado["Custo Consumo Ponta"] + df_otimizado["Custo Consumo Fora Ponta"]
        df_otimizado_dash["Custo Demanda"] = df_otimizado["Custo Demanda Ponta"] + df_otimizado["Custo Demanda Fora Ponta"]
        df_otimizado_dash["Custo Ultrapassagem"] = df_otimizado["Custo Ultrapassagem Ponta"] + df_otimizado["Custo Ultrapassagem Fora Ponta"]
        df_otimizado_dash["Custo ICMS"] = custo_icms_lista_otimizado
        df_otimizado_dash["Custo PIS/COFINS"] = custo_piscofins_lista_otimizado


    # Adiciona a coluna de "Cenário" (Atual / Otimizado)
    df_atual_plot = df_atual_dash.copy()
    df_otimizado_plot = df_otimizado_dash.copy()
    df_atual_plot["Cenário"] = "Atual"
    df_otimizado_plot["Cenário"] = "Otimizado"

    # Garante que os índices sejam os mesmos
    df_atual_plot["Mês"] = dados_historico["Mes_Ano"].unique()
    df_otimizado_plot["Mês"] = dados_historico["Mes_Ano"].unique()

    # Junta os dois DataFrames
    df_comparacao = pd.concat([df_atual_plot, df_otimizado_plot])

    # Coloca no formato longo (melt)
    df_long = df_comparacao.melt(
        id_vars=["Mês", "Cenário"],
        var_name=" ",
        value_name="Valor (R$)"
    )

    cores_personalizadas = {
        "Custo Consumo": "#1f77b4",
        "Custo Demanda": "#2ca02c",
        "Custo Ultrapassagem": "#d62728",
        "Custo ICMS": "#ff7f0e",
        "Custo PIS/COFINS": "#9467bd"
    }

    # Gráfico com legenda abaixo
    fig9 = px.bar(
        df_long,
        x="Mês",
        y="Valor (R$)",
        color=" ",
        facet_col="Cenário",
        barmode="stack",
        title="Comparação de Custos Mensais por Componente: Atual x Otimizado", color_discrete_map=cores_personalizadas
    )

    fig9.for_each_annotation(lambda a: a.update(
        text="Cenário Atual" if a.text == "Cenário=Atual" else "Cenário Otimizado"
    ))

    # Move a legenda para baixo
    fig9.update_layout(
        legend=dict(
            orientation="h",           # horizontal
            yanchor="bottom",
            y=-0.5,                    # distância abaixo do gráfico
            xanchor="center",
            x=0.3
        ),
        height=650,
        margin=dict(b=0),           # espaço extra para a legenda abaixo
        xaxis_title="Mês",
        yaxis_title="Custo Total (R$)"
    )

    # Exibe no Streamlit
    with abas[3]:
        st.plotly_chart(fig9, use_container_width=True)


    ##========================================= PDF ==================================================##
    import img2pdf
    from PIL import Image
    from PIL import Image, ImageDraw, ImageFont

    # Gráficos Plotly
    graficos = [fig, fig1, fig5, fig6, fig8, fig9]
    caminho_logo = "Logo_Electra.png"
    caminho_titulo = "Titulo.png"

    # Coordenadas dos gráficos (em pixels na imagem base)
    posicoes_graficos = [
        {"x": 140, "y": 500},   # fig
        {"x": 700, "y": 500},  # fig2
        {"x": 140, "y": 850},  # fig5
        {"x": 700, "y": 850}, # fig6
        {"x": 140, "y": 1200},  # fig8
        {"x": 700, "y": 1200}  # fig9
    ]

    # 1. Salvar gráficos como PNGs temporários
    def salvar_graficos_como_png(lista_figs, escala=1):
        imagens = []
        for fig in lista_figs:
            
            with tempfile.NamedTemporaryFile(delete=False, suffix=".png") as tmpfile:
                fig.write_image(tmpfile.name, format='png', scale=escala)
                imagens.append(tmpfile.name)
            
        return imagens

    # 2. Criar imagem base com gráficos colados
    def montar_imagem_relatorio(imagens):
        
        base = Image.new("RGB", (1240, 1754), color="white")
        draw = ImageDraw.Draw(base)



    # ===================== CONFIGURAÇÕES ====================================================================================
        largura_total_pagina = 1240
        largura_caixa, altura_caixa = 335, 150
        espacamento = 30

        # Largura ocupada por todas as caixas e espaçamentos
        largura_total_caixas = 3 * largura_caixa + 2 * espacamento

        # Cálculo para centralizar horizontalmente as 3 caixas no meio da página
        x1 = (largura_total_pagina - largura_total_caixas) // 2
        x2 = x1 + largura_caixa + espacamento
        x3 = x2 + largura_caixa + espacamento
        y1 = 250

        # Fontes (certifique-se de que o arquivo Montserrat-Bold.ttf está no mesmo diretório)
        fonte_titulo_bloco = ImageFont.truetype("Montserrat-ExtraBold.ttf", 19)
        fonte_dados_bloco = ImageFont.truetype("Montserrat-Bold.ttf", 16)
        fonte_economia = ImageFont.truetype("Montserrat-ExtraBold.ttf", 30)
        fonte_dados_cliente = ImageFont.truetype("Montserrat-Bold.ttf", 16)
        fonte_dados_observacao = ImageFont.truetype("Montserrat-ExtraBold.ttf", 10)
        fonte_rodape = ImageFont.truetype("Montserrat-ExtraBold.ttf", 16)
        # ===================================================== CABEÇALHO ============================================================

        
        
        logo = Image.open(caminho_logo).convert("RGBA") #LOGO
        logo.thumbnail((400, 400))                      #LOGO
        base.paste(logo, (x1, 30))                     #LOGO
        
        fonte_titulo = ImageFont.truetype("Montserrat-ExtraBold.ttf", 25) #TÍTULO
        draw.text((570, 110), "Análise de Demanda e Modalidade Tarifária", font=fonte_titulo, fill="#1976A5") #TÍTULO

        draw.text((90, 110), cliente_selecionado, font=fonte_dados_bloco, fill="black") #TEXTO DADOS CLIENTE
        draw.text((90, 130), f'Distribuidora: {distribuidora}', font=fonte_dados_bloco, fill="black") #TEXTO DADOS CLIENTE
        draw.text((90, 150), f'Subgrupo: {subgrupo}', font=fonte_dados_cliente, fill="black") #TEXTO DADOS CLIENTE
        
        # ===================== CENÁRIO ATUAL ====================================================================================
            # Funções de formatação
        def format_kw(valor):
            return f"{valor:.0f} kW"

        def format_currency(valor):
            return f"R$ {valor:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
        
        draw.rectangle([x1, y1, x1 + largura_caixa, y1 + altura_caixa], outline="gray", width=2)
        draw.text((x1 + 10, y1 - 40), "Cenário Atual", font=fonte_titulo_bloco, fill="gray")

        if modalidade == "Verde":
            draw.text((x1 + 10, y1 + 10), f"Demanda Ponta (kW): {format_kw(0)}", font=fonte_dados_bloco, fill="black")
        else:
            draw.text((x1 + 10, y1 + 10), f"Demanda Ponta (kW): {format_kw(demanda_contratada_atual_ponta)}", font=fonte_dados_bloco, fill="black")

        draw.text((x1 + 10, y1 + 45), f"Demanda Fora Ponta (kW): {format_kw(demanda_contratada_atual_fora_ponta)}", font=fonte_dados_bloco, fill="black")
        draw.text((x1 + 10, y1 + 80), f"Modalidade: {modalidade.capitalize()}", font=fonte_dados_bloco, fill="black")
        draw.text((x1 + 10, y1 + 115), f"Custo Total: {format_currency(custo_atual)}", font=fonte_dados_bloco, fill="black")

        # ===================== CENÁRIO SUGERIDO ==================================================================================
        draw.rectangle([x2, y1, x2 + largura_caixa, y1 + altura_caixa], outline="gray", width=2)
        draw.text((x2 + 10, y1 - 40), "Cenário Sugerido", font=fonte_titulo_bloco, fill="gray")

        if melhor_modalidade == "Verde":
            draw.text((x2 + 10, y1 + 10), f"Demanda Ponta (kW): {format_kw(0)}", font=fonte_dados_bloco, fill="black")
            draw.text((x2 + 10, y1 + 45), f"Demanda Fora Ponta (kW): {format_kw(nova_demanda_contratada_verde)}", font=fonte_dados_bloco, fill="black")
        else:
            draw.text((x2 + 10, y1 + 10), f"Demanda Ponta (kW): {format_kw(nova_demanda_contratada_azul[0])}", font=fonte_dados_bloco, fill="black")
            draw.text((x2 + 10, y1 + 45), f"Demanda Fora Ponta (kW): {format_kw(nova_demanda_contratada_azul[1])}", font=fonte_dados_bloco, fill="black")

        draw.text((x2 + 10, y1 + 80), f"Modalidade: {melhor_modalidade.capitalize()}", font=fonte_dados_bloco, fill="black")
        draw.text((x2 + 10, y1 + 115), f"Custo Total: {format_currency(menor_custo_total)}", font=fonte_dados_bloco, fill="black")

        # ===================== ECONOMIA ESTIMADA ==================================================================================
        economia = custo_atual - menor_custo_total

        # Caixa com fundo Azul
        draw.rectangle([x3, y1, x3 + largura_caixa, y1 + altura_caixa], fill="#1976A5")
        draw.rectangle([x3, y1, x3 + largura_caixa, y1 + altura_caixa], outline="gray", width=2)

        # Título acima da caixa
        draw.text((x3 + 10, y1 - 40), "Economia Estimada*", font=fonte_titulo_bloco, fill="gray")

        # Valor centralizado (horizontal e vertical)
        texto_economia = format_currency(economia)
        bbox_valor = draw.textbbox((0, 0), texto_economia, font=fonte_economia)
        w_valor = bbox_valor[2] - bbox_valor[0]
        h_valor = bbox_valor[3] - bbox_valor[1]
        pos_x_valor = x3 + (largura_caixa - w_valor) // 2
        pos_y_valor = y1 + (altura_caixa - h_valor) // 2 -15  # Pequeno ajuste para deixar espaço abaixo
        draw.text((pos_x_valor, pos_y_valor), texto_economia, font=fonte_economia, fill="white")

        # Texto percentual abaixo do valor
        texto_percentual = f"({economia_percentual*100:.2f}%)".replace('.', ',')
        bbox_percentual = draw.textbbox((0, 0), texto_percentual, font=fonte_economia)
        w_percentual = bbox_percentual[2] - bbox_percentual[0]
        pos_x_percentual = x3 + (largura_caixa - w_percentual) // 2
        pos_y_percentual = pos_y_valor + h_valor + 5  # 5 pixels abaixo do valor
        draw.text((pos_x_percentual, pos_y_percentual), texto_percentual, font=fonte_economia, fill="white")
        if icms != 0:
            draw.text((x3, 410), "Para o período analisado e com ICMS", font=fonte_dados_observacao, fill="gray")
        else:
            draw.text((x3, 410), "Para o período analisado e sem ICMS", font=fonte_dados_observacao, fill="gray")
        # ===================================================== OBSERVAÇÕES REGULATÓRIAS ============================================================

        draw.text((x1, 1530), "Aumento de Demanda: Art. 154. A distribuidora deve avaliar as solicitações de aumento da demanda contratada nos prazos dispostos no art. 64, informando, caso necessário,\no orçamento de conexão e demais providências necessárias para o atendimento da solicitação", font=fonte_dados_observacao, fill="gray")
        draw.text((x1, 1570), "Redução de Demanda: Art. 155. A distribuidora deve atender à solicitação de redução da demanda contratada, desde que formalizada com antecedência de pelo menos:\nI - 90 dias: para o consumidor do subgrupo AS ou A4; ou II - 180 dias: para os demais usuários.\n§ 1º É vedada mais de uma redução de demanda em um período de 12 meses.", font=fonte_dados_observacao, fill="gray")
        draw.text((x1, 1620), "Alteração Modalidade Tarifária: Art. 221. A distribuidora deve alterar a modalidade tarifária nos seguintes casos:\nI - a pedido do consumidor, desde que:\na) nos 12 últimos ciclos de faturamento não tenha ocorrido alteração;\nb) o pedido seja apresentado em até 3 ciclos completos de faturamento posteriores à revisão tarifária da distribuidora", font=fonte_dados_observacao, fill="gray")

        # ===================================================== SEÇÕES ============================================================
        draw.text((x1, 450), "1. Comparativo Demanda Lida e Contratada: ", font=fonte_titulo_bloco, fill="gray")
        draw.text((x1, 800), "2. Comparativo Modalidade Tarifária: ", font=fonte_titulo_bloco, fill="gray")
        draw.text((x1, 1150), "3. Comparativo de Custos: ", font=fonte_titulo_bloco, fill="gray")
        draw.text((x1, 1500), "4. Observações Regulatórias: ", font=fonte_titulo_bloco, fill="gray")

        # ===================================================== RODAPÉ ============================================================
        draw.rectangle([0, 1694, largura_total_pagina, 1754], fill="#1976A5")
        draw.text((110, 1710), "Rua Dr. Brasílio Vicente de Castro, 111 - 6º andar - CEP 81200-526 - Curitiba/PR - (41) 3023-3343 - www.electraenergy.com.br", font=fonte_rodape, fill="white")
        # ===================================================== GRÁFICOS ============================================================

        for i, img_path in enumerate(imagens):
            if i < len(posicoes_graficos):
                grafico = Image.open(img_path)
                grafico = grafico.resize((450, 300))  # ou ajuste conforme necessário
                pos = posicoes_graficos[i]
                base.paste(grafico, (pos["x"], pos["y"]))
        
        img_path_final = tempfile.NamedTemporaryFile(delete=False, suffix=".png").name
        base.save(img_path_final)
        return img_path_final


    # 3. Converter a imagem para PDF
    def imagem_para_pdf(caminho_imagem):
        with open(caminho_imagem, "rb") as f:
            pdf_bytes = img2pdf.convert(f)
        return BytesIO(pdf_bytes)

    # 4. Interface no Streamlit


    st.markdown("#### Gerar Relatório")

    if st.button("📄 Gerar Relatório"):
        imagens_salvas = salvar_graficos_como_png(graficos)
        imagem_relatorio = montar_imagem_relatorio(imagens_salvas)
        pdf_bytes = imagem_para_pdf(imagem_relatorio)

        # Limpeza dos arquivos temporários
        for img in imagens_salvas:
            os.remove(img)
        os.remove(imagem_relatorio)

        st.download_button(
            label="📥 Baixar Relatório PDF",
            data=pdf_bytes,
            file_name="relatorio_visual.pdf",
            mime="application/pdf"
        )


