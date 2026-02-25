# Arquivo: main/relatorios.py
import io
import os
import base64
import pandas as pd
import streamlit as st
from main.util import formatar_brl
from jinja2 import Environment, FileSystemLoader
from weasyprint import HTML, CSS

def split_table_html(df, max_rows=20):
    """
    Divide uma DataFrame em chunks HTML com quebras de página entre eles.
    """
    html_parts = []
    for i in range(0, len(df), max_rows):
        chunk = df.iloc[i:i+max_rows]
        html_parts.append(chunk.to_html(index=False, classes="tabela-pandas"))
        if i + max_rows < len(df):
            html_parts.append('<div style="page-break-before: always;"></div>')
    return ''.join(html_parts)

# --- Função Auxiliar: Formata número para BRL ---
def formatar_brl_html(valor, casas=2):
    """
    Transforma número para padrão BR com casas decimais variáveis.
    Uso no HTML: 
      {{ valor | brl }}    -> 2 casas (padrão)
      {{ valor | brl(3) }} -> 3 casas
      {{ valor | brl(0) }} -> 0 casas
    """
    if valor is None or valor == "":
        return "-"
    try:
        valor = float(valor)
        # Monta a string de formatação dinamicamente (ex: "{:,.3f}")
        formato = f"{{:,.{casas}f}}"
        
        # Aplica a formatação nativa (que sai com ponto no decimal)
        numero_formatado = formato.format(valor)
        
        # Inverte ponto e vírgula para o padrão brasileiro
        return numero_formatado.replace(",", "X").replace(".", ",").replace("X", ".")
        
    except (ValueError, TypeError):
        return str(valor)

# --- Função 1: Converte Imagem ---
def convert_img_base64(caminho_imagem):
    try:
        with open(caminho_imagem, "rb") as image_file:
            encoded_string = base64.b64encode(image_file.read()).decode('utf-8')
        return f"data:image/png;base64,{encoded_string}" 
    except FileNotFoundError:
        print(f"⚠️ Aviso: Imagem não encontrada em: {caminho_imagem}")
        return ""

# --- Função 2: Gera o PDF ---
def gerar_relatorio_usina(dados_contexto):
    
    # 1. LOCALIZAÇÃO (O GPS do Script)
    # Pega a pasta onde ESTE arquivo (relatorios.py) está: .../seu_projeto/main
    pasta_deste_script = os.path.dirname(os.path.abspath(__file__))
    
    # Sobe um nível para achar a RAIZ do projeto: .../seu_projeto/
    pasta_raiz = os.path.dirname(pasta_deste_script)
    
    # Agora define onde estão as coisas a partir da Raiz
    pasta_templates = os.path.join(pasta_raiz, 'templates')
    caminho_css = os.path.join(pasta_templates, 'estilo.css')
    caminho_logo = os.path.join(pasta_raiz, 'grupoelectra-branca.png') # Logo está na raiz

    # 2. Configura Jinja2 apontando para a pasta templates correta
    env = Environment(loader=FileSystemLoader(pasta_templates))
    env.filters['brl'] = formatar_brl_html
    
    if dados_contexto['tem_mre']:
        try:
            template = env.get_template('modelo_relatorio_mre.html')
        except Exception as e:
            print(f"Erro ao achar template em {pasta_templates}: {e}")
            raise e
    else:
        try:
            template = env.get_template('modelo_relatorio.html')
        except Exception as e:
            print(f"Erro ao achar template em {pasta_templates}: {e}")
            raise e

    # 3. Injeta a Logo (se não vier nos dados)
    if 'logo_empresa' not in dados_contexto:
        dados_contexto['logo_empresa'] = convert_img_base64(caminho_logo)

    # 4. Renderiza HTML
    html_preenchido = template.render(dados_contexto)

    # 5. Gera PDF na Memória
    pdf_buffer = io.BytesIO()
    
    # Importante: base_url aponta para a raiz para achar outros assets se precisar
    HTML(string=html_preenchido, base_url=pasta_raiz).write_pdf(
        target=pdf_buffer,
        stylesheets=[CSS(caminho_css)]
    )
    
    pdf_buffer.seek(0)
    return pdf_buffer

def preparar_conteudo_pdf(resumo,compras,vendas,mes,ano,horas_mes):
        
    with st.spinner("Fazendo o download"):  
        #Monta os dados que vão para o HTML

        possui_mre = (resumo['usina']['MRE'] != 'NÃO')

        

        soma_vendas = {
            "Contraparte": "TOTAL",
            "Sigla CCEE": "",
            "Fonte": "",
            "Tipo": "",
            "Submercado": "",
            "MWm": vendas['MWm'].sum(),
            "MWh": vendas["MWh"].sum(),
            "Preço": None,
            "Total": vendas['Total'].sum()
        }

        soma_compras = {
            "Contraparte": "TOTAL",
            "Sigla CCEE": "",
            "Fonte": "",
            "Tipo": "",
            "Submercado": "",
            "MWm": compras['MWm'].sum(),
            "MWh": compras["MWh"].sum(),
            "Preço": None,
            "Total": compras['Total'].sum()
        }

        if vendas["MWh"].sum() == 0:
            soma_vendas['Preço'] = 0
        else:
            soma_vendas['Preço'] = vendas['Total'].sum()/vendas["MWh"].sum()

        if compras["MWh"].sum() == 0:
            soma_compras['Preço'] = 0
        else:
            soma_compras['Preço'] = compras['Total'].sum()/compras["MWh"].sum()

        vendas_total = pd.concat([vendas, pd.DataFrame([soma_vendas])], ignore_index=True)
        vendas_str = formatar_brl(vendas_total, ['Preço','MWh','MWm','Total'], [2,3,6,2])
        vendas_str = vendas_str.drop(columns=['Movimentacao'])

        compras_total = pd.concat([compras, pd.DataFrame([soma_compras])], ignore_index=True)
        compras_str = formatar_brl(compras_total, ['Preço','MWh','MWm','Total'], [2,3,6,2])
        compras_str = compras_str.drop(columns=['Movimentacao'])

        # Verifica se as tabelas cabem em uma página (aprox. 25 linhas totais)
        total_linhas = len(vendas_str) + len(compras_str)
        quebrar_pagina_compras = total_linhas > 15

        # Se uma tabela for muito longa, divide em chunks (threshold alto, pois usuário acha improvável)
        tabela_vendas_html = split_table_html(vendas_str, max_rows=50) if len(vendas_str) > 50 else vendas_str.to_html(index=False, classes="tabela-pandas")
        tabela_compras_html = split_table_html(compras_str, max_rows=50) if len(compras_str) > 50 else compras_str.to_html(index=False, classes="tabela-pandas")
    

        contexto = {
            "nome_usina": resumo['usina']['Apelido'],
            "mes_ano": f"{mes:02d}/{ano}",
            "tabela_vendas": tabela_vendas_html,
            "tabela_compras": tabela_compras_html,
            "quebrar_pagina_compras": quebrar_pagina_compras,
            "gf_total_mwh" : f"{resumo['usina']['GF']}",
            "gf_total_mwm" : f"{resumo['usina']['GFmed']}",
            "gf_mre_sem_mwm": resumo['usina'].get('GFmed_MRE', 0), 
            "gf_mre_sem_mwh": resumo['usina'].get('GF_MRE', 0),
            "gf_mre_com_mwm": resumo['usina'].get('GFmed_MRE', 0)*resumo['usina'].get('Ajuste_MRE', 1),
            "gf_mre_com_mwh": resumo['usina'].get('GF_MRE', 0)*resumo['usina'].get('Ajuste_MRE', 1),
            "geracao_mwm": resumo['usina'].get('Geracao_med', 0),
            "geracao_mwh": resumo['usina'].get('Geracao', 0),

            "lastro_mwh_conv": resumo['indicadores_mwh']['lastro_conv'],
            "lastro_mwm_conv": resumo['indicadores_mwm']['lastro_conv'],
            "lastro_mwh_inc": resumo['indicadores_mwh']['lastro_incentivada'],
            "lastro_mwm_inc": resumo['indicadores_mwm']['lastro_incentivada'],
            "lastro_mwh_mre": resumo['indicadores_mwh']['lastro_mre'],
            "lastro_mwm_mre": resumo['indicadores_mwm']['lastro_mre'],
            
            "exposicao_mwh": resumo['indicadores_mwh']['exposicao'],
            "exposicao_mwm": resumo['indicadores_mwm']['exposicao'],

            "horas": horas_mes,
            "perdas": resumo['usina'].get('Perdas', 0)*100,
            "ajuste_mre": (resumo['usina'].get('Ajuste_MRE', 1)-1)*100,

            "venda_mwh":resumo['totais']['venda_mwh'],
            "venda_mwm":resumo['totais']['venda_mwm'],
            "venda_rs":resumo['totais']['venda_total_rs'],
            "preco_venda":resumo['totais']['venda_total_rs']/resumo['totais']['venda_mwh'],
            "compra_mwh":resumo['totais']['compra_mwh'],
            "compra_mwm":resumo['totais']['compra_mwm'],
            "compra_rs":resumo['totais']['compra_total_rs'],
            "preco_compra":resumo['totais']['compra_total_rs']/resumo['totais']['venda_mwh'],

            "tem_mre": possui_mre,
            "observacoes": "Relatório gerado via Sistema Electra."
        }
        
         # Gera o PDF
    return gerar_relatorio_usina(contexto)