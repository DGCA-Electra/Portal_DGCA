import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px

def run_Controle ():

    st.title ("Controle")
    st.markdown ("---")
    st.write ("Acompanhamento Ultrapassagens de Demanda:")

    # Leitura dos dados
    file_path = r"C:\DGCA\apps\Análise Demanda\dados.xlsx"
    df_cadastro = pd.read_excel(file_path, sheet_name="Dados_Cadastro")
    df_historico = pd.read_excel(file_path, sheet_name="Dados_Históricos")

    # Seleciona colunas necessárias
    df_tabela = pd.DataFrame(df_historico, columns=[
        "Apelido", "Competência", "Modalidade_tarifária",
        "Demanda_contratada_ponta", "Demanda_contratada_fora_ponta",
        "Demanda_registrada_ponta", "Demanda_registrada_fora_ponta"
    ])
    
    # Converte colunas numéricas para float
    colunas_numericas = ["Demanda_contratada_ponta", "Demanda_contratada_fora_ponta",
                         "Demanda_registrada_ponta", "Demanda_registrada_fora_ponta"]
    for col in colunas_numericas:
        df_tabela[col] = pd.to_numeric(df_tabela[col], errors='coerce')

    # Mapeamento pt → en para os meses
    meses_pt_en = {
        "jan": "jan", "fev": "feb", "mar": "mar", "abr": "apr",
        "mai": "may", "jun": "jun", "jul": "jul", "ago": "aug",
        "set": "sep", "out": "oct", "nov": "nov", "dez": "dec"
    }

    # Converte os meses para inglês
    df_tabela["Competência_en"] = df_tabela["Competência"].str.lower().replace(meses_pt_en, regex=True)

    # Converte para datetime (agora com ano e mês, útil para ordenação)
    df_tabela["Competência_ordenada"] = pd.to_datetime(df_tabela["Competência_en"], format="%b/%Y", errors="coerce")


    #==================================== ULTRAPASSAGENS ============================#

    # Verifica ultrapassagem
    df_tabela["Ultrapassagem"] = np.where(
        df_tabela["Modalidade_tarifária"].str.lower() == "azul",
        (df_tabela["Demanda_registrada_ponta"] > 1.05 * df_tabela["Demanda_contratada_ponta"]) |
        (df_tabela["Demanda_registrada_fora_ponta"] > 1.05 * df_tabela["Demanda_contratada_fora_ponta"]),
        (df_tabela["Demanda_registrada_fora_ponta"] > 1.05 * df_tabela["Demanda_contratada_fora_ponta"])
    )

    # Pivot da ultrapassagem
    df_pivot = df_tabela.pivot_table(
        index="Apelido",
        columns="Competência",
        values="Ultrapassagem",
        aggfunc="max"
    )

    # Ordena as colunas pela data correspondente
    competencias_ordenadas = (
        df_tabela[["Competência", "Competência_ordenada"]]
        .drop_duplicates()
        .sort_values("Competência_ordenada")
        ["Competência"]
        .tolist()
    )
    competencias_ordenadas = list(filter(pd.notna, competencias_ordenadas))
    df_pivot = df_pivot[competencias_ordenadas]
    
    # Mostra no Streamlit
    st.dataframe(df_pivot)

    #==================================== REATIVOS ============================#

    df_tabela_reativo = pd.DataFrame (df_historico, columns= ["Apelido", "Competência","Consumo_reativo_ponta", "Consumo_reativo_fora_ponta","Demanda_reativa_ponta","Demanda_reativa_fora_ponta", "Tarifa_consumo_reativo", "Tarifa_demanda_reativa"])
  
    # Converte colunas numéricas para float
    colunas_numericas_reativo = ["Consumo_reativo_ponta", "Consumo_reativo_fora_ponta",
                                  "Demanda_reativa_ponta", "Demanda_reativa_fora_ponta",
                                  "Tarifa_consumo_reativo", "Tarifa_demanda_reativa"]
    for col in colunas_numericas_reativo:
        df_tabela_reativo[col] = pd.to_numeric(df_tabela_reativo[col], errors='coerce')
    
    df_tabela_reativo ["Energia Reativa"] = (df_tabela_reativo ["Consumo_reativo_ponta"] * df_tabela_reativo ["Tarifa_consumo_reativo"]/1000  + df_tabela_reativo ["Consumo_reativo_fora_ponta"] * df_tabela_reativo ["Tarifa_consumo_reativo"]/1000 + df_tabela_reativo ["Demanda_reativa_ponta"] * df_tabela_reativo ["Tarifa_demanda_reativa"] + df_tabela_reativo ["Demanda_reativa_fora_ponta"] * df_tabela_reativo ["Tarifa_demanda_reativa"]  )

    df_tabela_reativo["Competência_en"] = df_tabela_reativo["Competência"].str.lower().replace(meses_pt_en, regex=True)

    df_tabela_reativo["Competência_ordenada"] = pd.to_datetime(df_tabela_reativo["Competência_en"], format="%b/%Y", errors="coerce")

    df_pivot_reativo = df_tabela_reativo.pivot_table(
        index="Apelido",
        columns="Competência",
        values="Energia Reativa",
        aggfunc="max"
    )

    competencias_ordenadas_reativo = (
        df_tabela[["Competência", "Competência_ordenada"]]
        .drop_duplicates()
        .sort_values("Competência_ordenada")
        ["Competência"]
        .tolist()
    )
    competencias_ordenadas_reativo = list(filter(pd.notna, competencias_ordenadas_reativo))
    df_pivot_reativo = df_pivot_reativo[competencias_ordenadas_reativo]

    st.markdown ("---")
    st.write ("Acompanhamento Energia Reativa Excedente:")

    df_pivot_reativo = df_pivot_reativo.fillna(0)

    st.dataframe(
    df_pivot_reativo.style.format({
        col: lambda x: f"R$ {x:,.2f}".replace(",", "v").replace(".", ",").replace("v", ".")
        for col in df_pivot_reativo.select_dtypes("number").columns
    }),
    use_container_width=True
    )


    
    
    st.markdown ("---")
    st.write ("Somatório Energia Reativa Últimos 12 meses:")

    df_ranking_reativo = df_tabela_reativo.groupby("Apelido", as_index=False)["Energia Reativa"].sum()

    df_ranking_reativo = df_ranking_reativo.sort_values(by="Energia Reativa", ascending=False).reset_index(drop=True)
    
    df_ranking_reativo.index = df_ranking_reativo.index + 1

    df_formatado = df_ranking_reativo.copy()
    df_formatado["Energia Reativa"] = df_formatado["Energia Reativa"].apply(lambda x: f"R$ {x:,.2f}".replace(",", "v").replace(".", ",").replace("v", "."))

    
    st.dataframe (df_formatado)


    #==================================== TRU ============================#
    
    df_tabela_TRU = pd.DataFrame (df_historico, columns= ["Apelido", "Competência","Consumo_ponta (MWh)", "Consumo_fora_ponta (MWh)","Demanda_contratada_ponta","Demanda_contratada_fora_ponta", "Modalidade_tarifária", "TUSD_encargos_ponta","TUSD_encargos_fora_ponta" , "Demanda_fio_ponta","Demanda_fio_fora_ponta"])
    
    # Converte colunas numéricas para float
    colunas_numericas_TRU = ["Consumo_ponta (MWh)", "Consumo_fora_ponta (MWh)",
                              "Demanda_contratada_ponta", "Demanda_contratada_fora_ponta",
                              "TUSD_encargos_ponta", "TUSD_encargos_fora_ponta",
                              "Demanda_fio_ponta", "Demanda_fio_fora_ponta"]
    for col in colunas_numericas_TRU:
        df_tabela_TRU[col] = pd.to_numeric(df_tabela_TRU[col], errors='coerce')
    
    df_tabela_TRU ["TRU"] = np.where (
        df_tabela_TRU["Modalidade_tarifária"].str.lower() == "verde"
        , 
        (df_tabela_TRU ["Consumo_ponta (MWh)"] * ( df_tabela_TRU  ["TUSD_encargos_ponta"] - (df_tabela_TRU  ["TUSD_encargos_ponta"]
        + df_tabela_TRU  ["TUSD_encargos_fora_ponta"] )/2 ) + df_tabela_TRU  ["Demanda_contratada_fora_ponta"] * df_tabela_TRU  ["Demanda_fio_fora_ponta"]/2 )
        ,
        df_tabela_TRU["Demanda_contratada_ponta"]
        * df_tabela_TRU["Demanda_fio_ponta"]/2
        + df_tabela_TRU["Demanda_contratada_fora_ponta"]
        * df_tabela_TRU["Demanda_fio_fora_ponta"]/2
    )/(df_tabela_TRU ["Consumo_ponta (MWh)"] + df_tabela_TRU ["Consumo_fora_ponta (MWh)"])

    df_tabela_TRU["Competência_en"] = df_tabela_TRU["Competência"].str.lower().replace(meses_pt_en, regex=True)
    df_tabela_TRU["Competência_ordenada"] = pd.to_datetime(df_tabela_TRU["Competência_en"], format="%b/%Y", errors="coerce")
    df_pivot_TRU = df_tabela_TRU.pivot_table(
        index="Apelido",
        columns="Competência",
        values="TRU",
        aggfunc="max"
    )
    competencias_ordenadas_TRU = (
        df_tabela[["Competência", "Competência_ordenada"]]
        .drop_duplicates()
        .sort_values("Competência_ordenada")
        ["Competência"]
        .tolist()
    )
    competencias_ordenadas_TRU = list(filter(pd.notna, competencias_ordenadas_TRU))
    df_pivot_TRU = df_pivot_TRU[competencias_ordenadas_TRU]
    st.markdown ("---")
    st.write ("Acompanhamento TRU:")
    df_pivot_TRU = df_pivot_TRU.fillna(0)
    st.dataframe(df_pivot_TRU.style.format({
        col: lambda x: f" {x:,.2f}".replace(",", "v").replace(".", ",").replace("v", ".")
        for col in df_pivot_TRU.select_dtypes("number").columns}),
        use_container_width=True)