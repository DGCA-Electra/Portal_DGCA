import streamlit as st
import pandas as pd
from datetime import date
import calendar
from main.dados import *
from main.relatorios import preparar_conteudo_pdf
from main.importador import importar_dados
from main.util import *

import base64
import streamlit.components.v1 as components



def main() -> None:
    # --- Configuração da Página ---
    st.markdown(
        """
        <style>
        /* Importando a Inter */
        @import url('https://fonts.googleapis.com/css2?family=Inter:ital,opsz,wght@0,14..32,100..900;1,14..32,100..900&display=swap');

        /* Aplica a fonte apenas em elementos de texto, sem quebrar a interface (removido div e [class*="css"]) */
        html, body, p, label, h1, h2, h3, h4, h5, h6, li, .stMarkdown {
            font-family: 'Inter', sans-serif !important;
        }

        /* Força bruta isolada para salvar o botão do menu lateral */
        [data-testid="collapsedControl"], [data-testid="collapsedControl"] * {
            font-family: 'Material Symbols Rounded' !important;
        }
        </style>
        """,
        unsafe_allow_html=True
    )


    # --- Título e Tema ---
    theme = st.context.theme["type"]
    if theme == "dark":
        st.logo("grupoelectra-branca.png")

    if theme == "light":
        st.logo("grupoelectra.png")

    st.title("⚡Resumo de Operação | Geradores")

    # --- Botão de Atualização ---
    if st.button("Atualizar Dados"):
        with st.spinner("Atualizando dados..."):
            importar_dados()
            extrai_dados(force_refresh=True)


        st.success("Dados atualizados com sucesso!")
        st.rerun()

    st.divider()

    # --- Carregar Dados ---
    @st.cache_data
    def carregar_lista():
        return pd.read_csv('dados/processados/usinas_info.csv')

    usinas = carregar_lista()   
    lista_usinas = sorted(usinas['USINA_APELIDO'].unique())

    # Valor Incial Toggles
    if "t1" not in st.session_state:
        st.session_state.t1 = False
    if "t2" not in st.session_state:
        st.session_state.t2 = False
    if "t3" not in st.session_state:
        st.session_state.t3 = False



    arrow_mre = lambda x: "up" if x>1 else("down" if x<1 else "off")
    delta_color_mre = lambda x: "green" if x>1 else("red" if x<1 else "gray")
    delta_lastro = lambda x:"Correto" if x>=0 else "Insuficiente"
    cor_lastro = lambda x:"green" if x>=0 else "red"
    sufixo = lambda x:"MWm" if x else "MWh"

    # --- Mapeamento de Meses ---
    meses_nome = [
        "Jan", "Fev", "Mar", "Abr", "Mai", "Jun", 
        "Jul", "Ago", "Set", "Out", "Nov", "Dez"
    ]


    # --- Interface de Seleção --- #
    st.header("Opções")
    with st.container(border=True):

        # Configuração de Colunas para Layout
        col_1, col_2 = st.columns([4,4],vertical_alignment='center')

        with col_1:
            # Primeira Linha: Seleção de Usina
            opcao_escolhida = st.selectbox(
                "Selecione o Gerador",
                lista_usinas,
                index=0,
                help="Busque pelo apelido da usina cadastrada."
            )

            # Segunda Linha: Seleção de Mês
            col_mes, _ = st.columns([4,2])

            # Terceira Linha: Seleção de Ano
            col_ano, _ = st.columns([3,4])

            with col_mes:
                mes_nome_selecionado = st.segmented_control(
                    "Meses", # Label escondida internamente
                    options=meses_nome,
                    default=meses_nome[(date.today().month - 1)],
                    key="mes"
                )
                ## Converte o nome de volta para o número do mês
                if mes_nome_selecionado == None:
                    st.stop()
                else:
                    mes = meses_nome.index(mes_nome_selecionado) + 1
            
            with col_ano:
                ano = st.number_input(
                    "Ano", 
                    min_value=2020, 
                    max_value=2030, 
                    value=date.today().year,
                    width=210
                )
    
        # Gerar Resumo
        resumo = calcular_resumo(opcao_escolhida, mes, ano)
                                
        with col_2:

        # Estrutra dos KPIs
            st.space("small")

            # Extrai o número de horas do mês selecionado
            horas_mes = horas_no_mes(ano, mes)

            # Primeira Linha: Horas no Mês e Geração Total
            col_horas, col_geracao = st.columns([1,1])

            # Segunda Linha: GF Total e GF MRE (se aplicável)
            col_gf, col_gf_mre = st.columns([1,1])

            # Toggle para mostrar valores médios ou totais
            medios = st.toggle("Valores Médios", value=st.session_state.t1, key="t1", on_change=sync_t1)
            ajuste_mre = resumo["usina"]['Ajuste_MRE']

            


        # Exibe os KPIs
            with col_horas:
                st.metric("Horas no Mês", f"{horas_mes} h",border=True)
                

            # Valores Totais (MWh)
            if not medios:
                with col_geracao:
                    st.metric("Geração Total", f"{resumo['usina']['Geracao']:,.3f} MWh",border=True)
                with col_gf:
                    st.metric(
                        "GF Total",
                        f"{resumo['usina']['GF']:,.3f} MWh",
                        border=True,
                        delta=f'Perdas: {(resumo['usina']['Perdas'])*100:.2f}%',
                        delta_arrow=arrow_mre(1-(resumo['usina']['Perdas'])),
                        delta_color=delta_color_mre(1-(resumo['usina']['Perdas']))
                    )
                with col_gf_mre:
                    if resumo['usina']['MRE'] == "SIM":
                        st.metric(
                            "GF MRE",
                            f"{resumo['usina']['GF_MRE']*ajuste_mre:,.3f} MWh",
                            border=True,
                            delta=f'Ajuste MRE: {(ajuste_mre-1)*100:.2f}%',
                            delta_arrow=arrow_mre(ajuste_mre),
                            delta_color=delta_color_mre(ajuste_mre)
                            )
                    elif resumo['usina']['MRE'] == "NÃO":
                        st.metric(
                            "GF MRE",
                            "",
                            border=True,
                            delta="Não se aplica",
                            delta_arrow="off",
                            delta_color="yellow",
                            height="stretch"
                            )
                        

            # Valores Médios (MWm)
            if medios:
                with col_geracao:
                    st.metric("Geração Total", f"{resumo['usina']['Geracao_med']:,.6f} MWm",border=True)
                with col_gf:
                    st.metric(
                        "GF Total",
                        f"{resumo['usina']['GFmed']:,.6f} MWm",
                        border=True,
                        delta=f'Perdas: {(resumo['usina']['Perdas'])*100:.2f}%',
                        delta_arrow=arrow_mre(1-(resumo['usina']['Perdas'])),
                        delta_color=delta_color_mre(1-(resumo['usina']['Perdas']))
                    )       
                with col_gf_mre:
                    if resumo['usina']['MRE'] == "SIM":
                        st.metric(
                            "GF MRE",
                            f"{resumo['usina']['GFmed_MRE']*ajuste_mre:,.6f} MWm",
                            border=True,
                            delta=f'Ajuste MRE: {(ajuste_mre-1)*100:.2f}%',
                            delta_arrow=arrow_mre(ajuste_mre),
                            delta_color=delta_color_mre(ajuste_mre)
                            )
                    elif resumo['usina']['MRE'] == "NÃO":
                        st.metric(
                            "GF MRE",
                            "",
                            border=True,
                            delta="Não se aplica",
                            delta_arrow="off",
                            delta_color="yellow",
                            height="stretch"
                            )    

        
    # --- Tabelas de Contratos ---
    st.header("Contratos")
    with st.container(border=True):
        st.subheader("Vendas")

        vendas = resumo['vendas'].sort_values(by=['Tipo','Contraparte'], ascending=[False,True])
        if vendas.empty:
            st.badge(
                label = "Sem contratos de venda associados",
                icon = "🔍",
                color = "gray"
            )
        else:
            st.dataframe(
                data=vendas,
                hide_index=True,
                column_config={
                    "Total": st.column_config.NumberColumn(
                        "Total (R$)",
                        format="R$ %.2f",
                    ),
                    "Preço": st.column_config.NumberColumn(
                        "Preço (R$)",
                        format="R$ %.2f",
                    ),
                    "MWm": st.column_config.NumberColumn(
                        format="%.6f",
                    ),
                    "MWh": st.column_config.NumberColumn(
                        format="%.4f",
                    )
                }
            )
            st.caption("*Valores apresentados no formato americano (xxx,xxx.xx)")

            st.subheader("Total | Vendas")
            col_total_med, col_total_mwh, col_total_rs, preco_medio_venda = st.columns([1,1,1,1], border=True)   

        
            with col_total_med:
                st.metric('Total Médios **(MWm)**',f"{resumo['totais']['venda_mwm']:.6f}")

            with col_total_mwh:
                st.metric('Total **(MWh)**',f"{resumo['totais']['venda_mwh']:,.4f}")

            with col_total_rs:
                st.metric('Total **(R$)**',f"{resumo['totais']['venda_total_rs']:,.2f}")

            with preco_medio_venda:
                st.metric(
                    'Preço Médio **(R$/MWh)**',
                    f"{resumo['totais']['venda_total_rs']/resumo['totais']['venda_mwh']:,.2f}"
                )

        
        st.subheader("Compras")

        compras = resumo['compras'].sort_values(by=['Tipo','Contraparte'], ascending=[False,True])
        if compras.empty:
            st.badge(
                label = "Sem contratos de compra associados",
                icon = "🔍",
                color = "gray"
            )
        else:
            st.dataframe(
                data=compras,
                hide_index=True,
                column_config={
                    "Total": st.column_config.NumberColumn(
                        "Total (R$)",
                        format="R$ %.2f",
                    ),
                    "Preço": st.column_config.NumberColumn(
                        "Preço (R$)",
                        format="R$ %.2f",
                    ),
                    "MWm": st.column_config.NumberColumn(
                        format="%.6f",
                    ),
                    "MWh": st.column_config.NumberColumn(
                        format="%.4f",
                    )
                }
            )
            st.caption("*Valores apresentados no formato americano (xxx,xxx.xx)")

            st.subheader("Total | Compras")
            compra_total_med, compra_total_mwh, compra_total_rs, preco_medio_compra = st.columns([1,1,1,1], border=True)   

            with compra_total_med:
                st.metric('Total Médios **(MWm)**',f"{resumo['totais']['compra_mwm']:.6f}")

            with compra_total_mwh:
                st.metric('Total **(MWh)**',f"{resumo['totais']['compra_mwh']:,.4f}")

            with compra_total_rs:
                st.metric('Total **(R$)**',f"{resumo['totais']['compra_total_rs']:,.2f}")

            with preco_medio_compra:
                st.metric(
                    'Preço Médio **(R$/MWh)**',
                    f"{resumo['totais']['compra_total_rs']/resumo['totais']['compra_mwh']:,.2f}"
                )


    # --- Interface Lastro ---
        st.subheader("Lastro")

        # Toggle para mostrar valores médios ou totais
        medios = st.toggle("Valores Médios",value=st.session_state.t2,key="t2",on_change=sync_t2)

        with st.container(border=True):
            inc, conv, mre = st.columns([2,2,3])
            

            with inc:
                if medios:
                    lastro_inc = resumo['indicadores_mwm']['lastro_incentivada']
                    lastro_inc_str = f'{lastro_inc:,.6f} {sufixo(medios)}'
                else:
                    lastro_inc = resumo['indicadores_mwh']['lastro_incentivada']
                    lastro_inc_str = f'{lastro_inc:,.4f} {sufixo(medios)}'

                st.metric(
                    label=f"Lastro Incentivado",
                    value= lastro_inc_str,
                    delta= delta_lastro(lastro_inc),
                    delta_arrow= "off",
                    delta_color= cor_lastro(lastro_inc)
                )
            with conv:
                if medios:
                    lastro_conv = resumo['indicadores_mwm']['lastro_conv']
                    lastro_conv_str = f'{lastro_conv:,.6f} {sufixo(medios)}'
                else:
                    lastro_conv = resumo['indicadores_mwh']['lastro_conv']
                    lastro_conv_str = f'{lastro_conv:,.4f} {sufixo(medios)}'

                st.metric(
                    label=f"Lastro Convencional",
                    value= lastro_conv_str,
                    delta= delta_lastro(lastro_conv),
                    delta_arrow= "off",
                    delta_color= cor_lastro(lastro_conv)
                )

            with mre:
                if resumo["usina"]['MRE']=='SIM':
                    if medios:
                        lastro_mre = resumo['indicadores_mwm']['lastro_mre']
                        lastro_mre_str = f'{lastro_mre:,.6f} {sufixo(medios)}'
                    else:
                        lastro_mre = resumo['indicadores_mwh']['lastro_mre']
                        lastro_mre_str = f'{lastro_mre:,.4f} {sufixo(medios)}'
                    
                    st.metric(
                        label=f"Lastro MRE",
                        value= lastro_mre_str,
                        delta= delta_lastro(lastro_mre),
                        delta_arrow= "off",
                        delta_color= cor_lastro(lastro_mre)
                    )

    # --- Interface Exposição Energética 
        st.subheader("Exposição Energética")     

        # Toggle para mostrar valores médios ou totais
        medios = st.toggle("Valores Médios",value=st.session_state.t3,key="t3",on_change=sync_t3)   

        with st.container(border=True):
            mre_str = lambda x: "" if x=="NÃO" else "MRE"
            if medios:
                exposicao = resumo['indicadores_mwm']['exposicao']
                exposicao_str = f'{exposicao:,.6f} {sufixo(medios)}'
            else:
                exposicao = resumo['indicadores_mwh']['exposicao']
                exposicao_str = f'{exposicao:,.4f} {sufixo(medios)}'

            st.metric(
                label=f"Exposição {mre_str(resumo['usina']['MRE'])}",
                value= exposicao_str,
                delta= delta_lastro(exposicao),
                delta_arrow= "off",
                delta_color= cor_lastro(exposicao)
            )
            


    # ----------------------------------------------------------------
    # EXPORTADOR DE RELATÓRIO
    # ----------------------------------------------------------------

    st.write("-------------")
    st.subheader("Exportar")

    nome_arquivo = f"Resumo de Operações {resumo['usina']['Apelido']} {mes}-{ano}.pdf"

    # Usamos um botão comum. Ele NÃO roda ao mudar filtros, SÓ quando clicas.
    if st.button("Baixar Relatório", use_container_width=False):
        with st.spinner("Fazendo o Download"):
            
            # 1. Executa a tua função (SÓ agora no clique)
            pdf_buffer = preparar_conteudo_pdf(resumo, compras, vendas, mes, ano, horas_mes)
            
            # 2. Codifica o PDF para base64
            pdf_bytes = pdf_buffer.getvalue()
            b64 = base64.b64encode(pdf_bytes).decode()
            
            # 3. JavaScript mágico: cria um link invisível e "clica" nele sozinho
            js_trigger = f"""
                <html>
                <body>
                    <script>
                        var a = document.createElement('a');
                        a.href = 'data:application/pdf;base64,{b64}';
                        a.download = '{nome_arquivo}';
                        document.body.appendChild(a);
                        a.click();
                        document.body.removeChild(a);
                    </script>
                </body>
                </html>
            """
            # Executa o JS de forma invisível
            components.html(js_trigger, height=0, width=0)
            
            st.success("Download concluído!")

if __name__ == "__main__":
    main()