import streamlit as st
import pandas as pd
import plotly.express as px

def run_Reativo ():

    st.title ("Análise de Reativos")

    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    file_path = os.path.join(BASE_DIR, "dados.xlsx")

    df_cadastro = pd.read_excel(file_path, sheet_name="Dados_Cadastro")
    df_historico = pd.read_excel(file_path, sheet_name="Dados_Históricos")

    cliente = df_cadastro["Apelido"].dropna().unique().tolist()
    cliente_selecionado = st.selectbox("Escolha um cliente:", cliente)

    dados_historico = df_historico[df_historico["Apelido"] == cliente_selecionado]
    dados_cadastro = df_cadastro[df_cadastro["Apelido"] == cliente_selecionado].iloc[0]

    ## ajuste português##=====
    meses_pt_en = {
        "jan": "Jan", "fev": "Feb", "mar": "Mar", "abr": "Apr",
        "mai": "May", "jun": "Jun", "jul": "Jul", "ago": "Aug",
        "set": "Sep", "out": "Oct", "nov": "Nov", "dez": "Dec"
    }

    for pt, en in meses_pt_en.items():
        dados_historico["Competência"] = dados_historico["Competência"].str.replace(f"^{pt}", en, regex=True)
    ## ajustes português ##=====

    dados_historico["Data"] = pd.to_datetime(dados_historico["Competência"], format="%b/%Y")

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

    df_tabela = pd.DataFrame()

    for i, mes_ano  in enumerate(meses_ano_unicos):
        filtro_mes_ano = dados_historico[dados_historico["Mes_Ano"] == mes_ano]
        
        # Verifica se há dados para o mês antes de acessar
        if not filtro_mes_ano.empty:
            df_tabela.loc[i, "Mês"] = filtro_mes_ano["Mes_Ano"].sum()
            df_tabela.loc[i, "Consumo Reativo Ponta (kVarh)"] = filtro_mes_ano["Consumo_reativo_ponta"].sum()
            df_tabela.loc[i, "Consumo Reativo fora ponta (kVarh)"] = filtro_mes_ano["Consumo_reativo_fora_ponta"].sum()
            df_tabela.loc[i, "Demanda Reativa Ponta (kVar)"] = filtro_mes_ano["Demanda_reativa_ponta"].sum()
            df_tabela.loc[i, "Demanda Reativa Fora Ponta (kVar)"] = filtro_mes_ano["Demanda_reativa_fora_ponta"].sum()
            df_tabela.loc[i, "Tarifa Consumo Reativo"] = filtro_mes_ano["Tarifa_consumo_reativo"].sum()
            df_tabela.loc[i, "Tarifa Demanda Reativo"] = filtro_mes_ano["Tarifa_demanda_reativa"].sum()

    st.write ("Dados históricos:")

    df_formatado = df_tabela.copy()
    df_formatado = df_formatado.applymap(lambda x: f"{x:,.2f}".replace(",", "v").replace(".", ",").replace("v", ".") if isinstance(x, (int, float)) else x)

    with st.expander(" Consumo Reativo e Demanda Reativa"):
        st.dataframe(df_formatado)


    ##====================== CÁLCULO ==========================

    icms = dados_cadastro ["ICMS"]
    piscofins = 0.05

    def calcular_custo_reativo (dados_presentes):
        custos_consumo_reativo_ponta =[]
        custos_consumo_reativo_fora_ponta =[]
        custos_demanda_reativa_ponta = []
        custos_demanda_reativa_fora_ponta = []
        custos_icms = []
        custos_piscofins = []

        for _,linha in dados_presentes.iterrows():
            tarifa_consumo_reativo = linha ["Tarifa Consumo Reativo"]
            tarifa_demanda_reativa = linha ["Tarifa Demanda Reativo"]
            consumo_reativo_ponta = linha ["Consumo Reativo Ponta (kVarh)"]
            consumo_reativo_fora_ponta = linha ["Consumo Reativo fora ponta (kVarh)"]
            demanda_reativa_ponta = linha ["Demanda Reativa Ponta (kVar)"]
            demanda_reativa_fora_ponta = linha ["Demanda Reativa Fora Ponta (kVar)"]

            custo_consumo_reativo_ponta = consumo_reativo_ponta * tarifa_consumo_reativo/1000
            custo_consumo_reativo_fora_ponta = consumo_reativo_fora_ponta * tarifa_consumo_reativo/1000
            custo_demanda_reativa_ponta = demanda_reativa_ponta * tarifa_demanda_reativa
            custo_demanda_reativa_fora_ponta = demanda_reativa_fora_ponta * tarifa_demanda_reativa
            custo_icms = ((custo_consumo_reativo_fora_ponta + custo_consumo_reativo_ponta + custo_demanda_reativa_ponta + custo_demanda_reativa_fora_ponta)/(1-piscofins)/(1-icms)) * icms
            custo_piscofins = ((custo_consumo_reativo_fora_ponta + custo_consumo_reativo_ponta + custo_demanda_reativa_ponta + custo_demanda_reativa_fora_ponta)/(1-piscofins)) * piscofins

            custos_consumo_reativo_ponta.append(custo_consumo_reativo_ponta)
            custos_consumo_reativo_fora_ponta.append(custo_consumo_reativo_fora_ponta)
            custos_demanda_reativa_ponta.append(custo_demanda_reativa_ponta)
            custos_demanda_reativa_fora_ponta.append(custo_demanda_reativa_fora_ponta)
            custos_icms.append(custo_icms)
            custos_piscofins.append(custo_piscofins)

        return custos_consumo_reativo_ponta, custos_consumo_reativo_fora_ponta, custos_demanda_reativa_ponta, custos_demanda_reativa_fora_ponta

    df = calcular_custo_reativo (df_tabela)

    df = pd.DataFrame(df).T  # <- transforma tupla de listas em DataFrame, se necessário
    
    
    df.columns = [
        
        "Consumo Reativo Ponta (R$)",
        "Consumo Reativo Fora Ponta (R$)",
        "Demanda Reativa Ponta (R$)",
        "Demanda Reativa Fora Ponta (R$)",
    ]

    df["Mês"] = meses_ano_unicos
    # garante que "Mês" seja a primeira coluna
    df = df[["Mês"] + [col for col in df.columns if col != "Mês"]]

    soma_total = df.sum(numeric_only=True).sum()

    maior_demanda_reativa_ponta = df_tabela["Demanda Reativa Ponta (kVar)"].max()
    maior_demanda_reativa_fora_ponta = df_tabela["Demanda Reativa Fora Ponta (kVar)"].max()

    soma_consumo_reativo_ponta = df_tabela["Consumo Reativo Ponta (kVarh)"].sum()
    soma_consumo_reativo_fora_ponta = df_tabela["Consumo Reativo fora ponta (kVarh)"].sum()


    ##=============================== APRESENTAÇÃO RESULTADOS ==================================
    def format_currency(valor):
        return f"R$ {valor:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


    st.markdown("---")
    st.markdown("####  Custos com Reativos")

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
            <p style="margin:0;"><b>{format_currency(soma_total)}</b></p>
            
        </div>
        """, unsafe_allow_html=True)

    st.markdown("---")

    with st.expander(" Custos Consumo Reativo e Demanda Reativa"):
        st.dataframe (df, use_container_width=True)

    ###============================GRÁFICO=================================###



    # Prepara os dados
    df_plot = df.copy()
    df_plot["Mês"] = meses_ano_unicos  # coloca o índice como coluna

    # Transforma para formato longo (tidy)
    df_meltado = df_plot.melt(id_vars="Mês", var_name="Categoria", value_name="Custo (R$)")
    df_meltado["Categoria"] = df_meltado["Categoria"].str.replace(" \(R\$\)", "", regex=True)

    # Cores personalizadas com nomes exatos das categorias
    cores_personalizadas = {
        "Consumo Reativo Ponta": "#1f77b4",
        "Consumo Reativo Fora Ponta": "#2ca02c",
        "Demanda Reativa Ponta": "#d62728",
        "Demanda Reativa Fora Ponta": "#ff7f0e",
    }

    # Cria o gráfico
    fig = px.bar(
        df_meltado,
        x="Mês",
        y="Custo (R$)",
        color="Categoria",
        barmode="relative",
        title="Custos Mensais com Energia Reativa",
        labels={"Mês": "Mês", "Custo (R$)": "Custo em R$"},
        color_discrete_map=cores_personalizadas
    )

    fig.update_layout(
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=-0.40,
            xanchor="center",
            x=0.3,
            font=dict(size=14),
            title_text=''
        ),
        margin=dict(l=40, r=40, t=60, b=100),
        title_font=dict(size=20)
    )

    # Mostra no Streamlit
    st.plotly_chart(fig, use_container_width=True)


    ##====================== PDF ==========================

    import img2pdf
    from PIL import Image
    from PIL import Image, ImageDraw, ImageFont
    import tempfile
    import matplotlib.pyplot as plt
    from PIL import Image, ImageDraw
    from io import BytesIO
    import os

    ## ===============================CONFIGURAÇÕES================================

    # Gráficos Plotly
    grafico = [fig]
    caminho_logo = "Logo_Electra.png"
    caminho_titulo = "Triangulo.png"

    # Coordenadas dos gráficos (em pixels na imagem base)
    posicao_grafico = [{"x": 140, "y": 500}]   # fig

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

    fonte_titulo = ImageFont.truetype("Montserrat-ExtraBold.ttf", 25)
    fonte_titulo_bloco = ImageFont.truetype("Montserrat-ExtraBold.ttf", 15)
    fonte_texto = ImageFont.truetype("Montserrat-ExtraBold.ttf", 10)
    fonte_valor = ImageFont.truetype("Montserrat-Bold.ttf", 25)
    fonte_cliente = ImageFont.truetype("Montserrat-Bold.ttf", 16)
    fonte_rodape = ImageFont.truetype("Montserrat-ExtraBold.ttf", 16)
    fonte_dados_observacao = ImageFont.truetype("Montserrat-ExtraBold.ttf", 15)
    fonte_economia = ImageFont.truetype("Montserrat-ExtraBold.ttf", 30)

    ## ===============================CONFIGURAÇÕES================================

    # 1. Salvar gráficos como PNGs temporários
    def salvar_graficos_como_png(lista_figs, escala=3):
        imagens = []
        for fig in lista_figs:
            
            with tempfile.NamedTemporaryFile(delete=False, suffix=".png") as tmpfile:
                fig.write_image(tmpfile.name, format='png', scale=escala)
                imagens.append(tmpfile.name)
            
        return imagens

    # 2. Criar imagem base com gráficos colados
    def montar_imagem_relatorio(imagens):
        # Base A4 em pixels a 150 DPI
        largura, altura = 1240, 1754
        base = Image.new("RGB", (largura, altura), color="white")
        draw = ImageDraw.Draw(base)

        
        ####======================================= CABEÇALIO =========================================##

        try:
            logo = Image.open(caminho_logo).convert("RGB")
            logo.thumbnail((400, 400))
            base.paste(logo, (x1, 30))
        except:
            pass
        

        draw.text((90, 110), cliente_selecionado, font=fonte_cliente, fill="black") #TEXTO DADOS CLIENTE    
        draw.text((570, 70), "Acompanhamento Energia Reativa Excedente", fill="#1976A5", font=fonte_titulo)

        ####======================================= CAIXAS =========================================##

        # Caixa 1 - Consumo Reativo
        x = x1
        draw.text((x+5, y1 - 40), "Consumo Reativo Excedente (kVarh)", font=fonte_titulo_bloco, fill="gray")
        draw.rectangle([x, y1, x + largura_caixa, y1 + altura_caixa], fill="white", outline="gray", width=3)
        draw.text((x + 15, y1 + 35), f"Ponta: {soma_consumo_reativo_ponta:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."), font=fonte_valor, fill="black")
        draw.text((x + 15, y1 + 85), f"Fora Ponta: {soma_consumo_reativo_fora_ponta:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."), font=fonte_valor, fill="black")

        # Caixa 2 - Demanda Reativa
        x = x2
        draw.text((x+5, y1 - 40), "Demanda Reativa Máx. (kVar)", font=fonte_titulo_bloco, fill="gray")
        draw.rectangle([x, y1, x + largura_caixa, y1 + altura_caixa], fill="white", outline="gray", width=3)
        draw.text((x + 15, y1 + 35), f"Ponta: {maior_demanda_reativa_ponta:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."), font=fonte_valor, fill="black")
        draw.text((x + 15, y1 + 85), f"Fora Ponta: {maior_demanda_reativa_fora_ponta:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."), font=fonte_valor, fill="black")

        # Caixa 3 - Oportunidade de Economia
        x = x3
        draw.text((x+5, y1 - 40), "Oportunidade de Economia*", font=fonte_titulo_bloco, fill="gray")
        draw.rectangle([x, y1, x + largura_caixa, y1 + altura_caixa], fill="#0072B5", outline="gray", width=3)

        # Centralizar valor dentro da caixa azul
        texto_economia = format_currency(soma_total)
        largura_texto = fonte_economia.getlength(texto_economia) if hasattr(fonte_economia, 'getlength') else draw.textbbox((0, 0), texto_economia, font=fonte_economia)[2]
        x_centralizado = x + (largura_caixa - largura_texto) / 2
        draw.text((x_centralizado, y1 + 60), texto_economia, font=fonte_economia, fill="white")

        # Observação
        draw.text((825, y1+155), "*Sem impostos", fill="gray", font=fonte_dados_observacao)

        ####======================================= GRAFICO =========================================##
        try:
            grafico = Image.open(imagens[0]).convert("RGB").resize((900, 600))
            base.paste(grafico, (170, 580))
        except:
            pass

        ####======================================= TEXTO TÉCNICO =========================================##

            
        draw.text ((410, 1280),"Apesar de necessária para o funcionamento de equipamentos elétricos que possuem componentes\nindutivos ou capacitivos, como motores e transformadores, a energia reativa não realiza\ntrabalho útil e seu excedente é tarifado pela distribuidora.",fill="#1976A5", font=fonte_dados_observacao)
        # draw.text ((410, 1350), "Essa energia é armazenada e depois devolvida ao sistema em cada ciclo da corrente alternada.\nEssa presença, sem seu devido controle, pode acarretar no funcionameto não adequado de sistemas\nelétricos. ",fill="#1976A5", font=fonte_dados_observacao)
        draw.text ((410, 1350), "Para evitar esses custos, recomenda-se avaliar o uso de bancos de capacitores e adotar outras medidas\npara correção de fator de potência.",fill="#1976A5", font=fonte_dados_observacao)
        
        
        ####======================================= FORMULA =========================================##
        

        triangulo = Image.open("Triangulo.png").convert("RGBA")
        triangulo = triangulo.resize((300, 200))
        base.paste(triangulo, (70, 1230), mask=triangulo)

        formula = r"$FP = \frac{kW}{kVA} = \cos\ \varphi$"
        fig, ax = plt.subplots(figsize=(4, 1))
        ax.text(0.5, 0.5, formula, fontsize=15, ha='center', va='center',color='gray')
        ax.axis('off')

        # Salva a fórmula como imagem em buffer
        buf = BytesIO()
        plt.savefig(buf, format='png', bbox_inches='tight', transparent=True)
        buf.seek(0)
        imagem_formula = Image.open(buf)

        # 3. Cola a imagem da fórmula em uma posição desejada (ex: x=100, y=200)
        base.paste(imagem_formula, (30, 1420), imagem_formula)  # usa canal alfa (transparência)
        

        ###=============================================== RODAPÉ =====================================###
        rodape_texto = "Rua Dr. Brasílio Vicente de Castro, 111 - 6º andar - CEP 81200-526 - Curitiba/PR - (41) 3023-3343 - www.electraenergy.com.br"
        rodape_altura = 60
        draw.rectangle([0, altura - rodape_altura, largura, altura], fill="#0072B5")
        bbox = draw.textbbox((0, 0), rodape_texto, font=fonte_rodape)
        w = bbox[2] - bbox[0]
        draw.text(((largura - w) / 2, altura - rodape_altura + 15), rodape_texto, font=fonte_rodape, fill="white")

        return base

    def imagem_para_pdf(caminho_imagem):
        with open(caminho_imagem, "rb") as f:
            pdf_bytes = img2pdf.convert(f)
        return BytesIO(pdf_bytes)


    # Geração da imagem e exportação para PDF


    if st.button("📄 Gerar Relatório"):
        imagens_png = salvar_graficos_como_png([fig])
        imagem_final = montar_imagem_relatorio(imagens_png)

        # Salva imagem final em arquivo temporário
        with tempfile.NamedTemporaryFile(delete=False, suffix=".png") as tmp_imagem:
            imagem_final.save(tmp_imagem.name, format="PNG")
            caminho_imagem_final = tmp_imagem.name

        # Converte para PDF com img2pdf
        pdf_bytes = imagem_para_pdf(caminho_imagem_final)

        # Limpeza dos arquivos temporários
        for img in imagens_png:
            os.remove(img)
        os.remove(caminho_imagem_final)

        # Botão de download
        st.download_button(
            label="📥 Baixar Relatório PDF",
            data=pdf_bytes,
            file_name="relatorio_visual.pdf",
            mime="application/pdf"
        )
    
   
