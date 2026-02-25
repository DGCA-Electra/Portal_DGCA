import re
import pandas as pd
from datetime import datetime
import calendar
import os

USINAS_PATH = 'dados/brutos/geradores.csv'
CONTRATOS_PATH = 'dados/brutos/contratos.csv'

USINAS_PATH_PROCESSADOS = 'dados/processados/usinas_info.csv'
CONTRATOS_PATH_PROCESSADOS = 'dados/processados/contratos_filtrados.csv'

def ajusta_contratos(caminho_arquivo: str = CONTRATOS_PATH) -> pd.DataFrame:
    '''
    ajusta_contratos: Ajusta os dados dos contratos, filtrando apenas os relacionados às usinas de interesse
    e selecionando as colunas relevantes.
    
    :param caminho_arquivo: Informar caminho do arquivo de contratos bruto.
    :type caminho_arquivo: str
    :return: Dataframe com todos os contratos filtrados.
    :rtype: DataFrame
    '''

    try:
        # Seleciona apenas as colunas relevantes
        colunas_relevantes = ['Movimentacao','Contraparte_apelido','Parte_apelido','Sigla_CCEE','Sigla_CCEE_Contraparte',
                'Submercado','Ano','Mes','Volume_medio_contratado','Quant_Contratada','ValorReajustado',
                'Agrupador','Perfil_CCEE_vendedor']

        # Carrega o arquivo de contratos
        df = pd.read_csv(
            caminho_arquivo,
            usecols=colunas_relevantes, 
            dayfirst=True, 
            encoding='latin-1',
            sep=',',
            low_memory=False
        )
        
        try:
            # Carrega o arquivo de usinas processadas
            usinas = pd.read_csv(USINAS_PATH_PROCESSADOS, encoding= 'latin-1')

        except FileNotFoundError:
            # Informar erro na importação
            print("Contratos [Erro]: Arquivo de usinas processadas não encontrado.")
            return None
        
        # Cria uma lista com os apelidos das usinas
        lista_usinas = usinas['USINA_APELIDO'].unique()
        regex = '|'.join([re.escape(str(u)) for u in lista_usinas])

        # Filtra os contratos relacionados às usinas
        df = df[
            df['Parte_apelido'].str.contains(regex, case=False, na=False) | 
            df['Contraparte_apelido'].str.contains(regex, case=False, na=False)
        ]

        # Padronização Coluna
        df['Parte_apelido'] = df['Parte_apelido'].str.upper()

        # Salva o arquivo processado
        df.to_csv(CONTRATOS_PATH_PROCESSADOS, index= False, encoding='latin-1')
        return df
    
    except Exception as e:  
        # informar erro na importação
        print("Contratos [Erro]:", type(e), e)
        return None


def info_usinas(caminho_arquivo: str = USINAS_PATH) -> pd.DataFrame:
    '''
    info_usinas: Processa os dados das usinas, selecionando as colunas relevantes e tratando valores ausentes.
    
    :param caminho_arquivo: Caminho do arquivo de usinas bruto.
    :type caminho_arquivo: str
    :return: Dataframe com informações das usinas processadas.
    :rtype: DataFrame
    '''

    try:
        # Seleciona apenas as colunas relevantes
        colunas_relevantes = ['NOME_USINA','USINA_APELIDO','USINA_ESTADO','MES','ANO','PARTICIPA_MRE',
                              'AJUSTE_MRE_ESTIMADO','AJUSTE_MRE_REALIZADO','GERACAO_MEDIDA_TOTAL',
                              'GF_FLAT','GF_SAZONALIZADA','GF_SAZONALIZADA_MRE','PPIM_PERC_PERDAS_INTERNAS_MEDIAS',
                              'FID_FATOR_DE_INDISPONIBILIDADE']
        
        # Carrega o arquivo de usinas
        df = pd.read_csv(
            caminho_arquivo, 
            usecols=colunas_relevantes, 
            header=9, 
            encoding='latin-1',
            sep=',',
            low_memory=False
        )

        # Trata valores ausentes
        df['GF_SAZONALIZADA'] = df['GF_SAZONALIZADA'].fillna(0)
        df['GF_FLAT'] = df['GF_FLAT'].fillna(0)
        df['GF_SAZONALIZADA_MRE'] = df['GF_SAZONALIZADA_MRE'].fillna(0)
        df['AJUSTE_MRE_REALIZADO'] = df['AJUSTE_MRE_REALIZADO'].fillna(1)
        df['AJUSTE_MRE_ESTIMADO'] = df['AJUSTE_MRE_ESTIMADO'].fillna(1)
        df['PPIM_PERC_PERDAS_INTERNAS_MEDIAS'] = df['PPIM_PERC_PERDAS_INTERNAS_MEDIAS'].fillna(0)
        df['FID_FATOR_DE_INDISPONIBILIDADE'] = df['FID_FATOR_DE_INDISPONIBILIDADE'].fillna(0)

        # Excessões de Tratatamento
        df['USINA_APELIDO'] = df['USINA_APELIDO'].str.upper()
        df['USINA_APELIDO'] = df['USINA_APELIDO'].replace('PCH RIO DOS INDIOS - MATRIZ','PCH RIO DOS INDIOS')


        # Salva o arquivo processado
        df.to_csv(USINAS_PATH_PROCESSADOS, index= False, encoding= 'latin-1')
        return df

    except Exception as e:
        print("Usinas [Erro]:", type(e), e)
        return None


def extrai_dados(force_refresh: bool = False):
    '''
    extrai_dados: Extrai os dados primários dos arquivos brutos, processando e salvando em cache.
    [1] Se force_refresh=True, limpa o cache e reprocessa todos os dados.
    [2] Se force_refresh=False, compara data de modificação dos arquivos brutos com os processados.
    
    :param force_refresh: Sincroniza os dados importados, sobrescrevendo o cache.
    :type force_refresh: bool
    '''
    # Cria pastas necessárias, se não existirem
    os.makedirs('cache', exist_ok=True)
    os.makedirs('dados/processados', exist_ok=True)


    # 1. Força atualização dos dados, limpando o cache
    if force_refresh:
        print("Forçando atualização dos dados.")

        # Remove todos os arquivos em cache
        for arquivo in os.listdir('cache'):
            os.remove(os.path.join('cache', arquivo))
        print("Dados em cache limpos.")
 
        # Processa os dados brutos (Usinas)
        df_usinas = info_usinas(USINAS_PATH)
        if not df_usinas is None:  
            print("Usinas: OK")
        
        # Processa os dados brutos (Contratos)
        df_contratos = ajusta_contratos(CONTRATOS_PATH)
        if not df_contratos is None:  
            print("Contratos: OK")
            print("Dados processados com sucesso.")
            print('\n')
            
        return

    # 2.a. Verifica se os arquivos foram modificados desde a última extração (Usinas)
    print("Verificando modificações nos arquivos de dados.")

    try:
        # Captura o tempo de modificação dos arquivos processados
        mod_time0 = datetime.fromtimestamp(os.path.getmtime('dados/processados/usinas_info.csv'))
        mod_time1 = datetime.fromtimestamp(os.path.getmtime(USINAS_PATH))
    
    except:
        # Se não existir, processa os dados

        # Remove todos os arquivos em cache
        for arquivo in os.listdir('cache'):
            os.remove(os.path.join('cache', arquivo))
        print("Dados em cache limpos.")

        # Processa os dados brutos (Usinas)
        df_usinas = info_usinas(USINAS_PATH)
        if not df_usinas is None:
            print("Usinas: OK")

    else:
        # Compara os tempos de modificação
        if mod_time1 < mod_time0:
            print("Usinas: Não foi modificado. Usando dados em cache.")
        else:
            # Processa os dados brutos (Usinas)
            df_usinas = info_usinas(USINAS_PATH)
            if not df_usinas is None:
                print("Usinas: OK")

    # 2.b. Verifica se os arquivos foram modificados desde a última extração (Contratos)
    try:
        # Captura o tempo de modificação dos arquivos processados
        mod_time0 = datetime.fromtimestamp(os.path.getmtime('dados/processados/contratos_filtrados.csv'))
        mod_time1 = datetime.fromtimestamp(os.path.getmtime(CONTRATOS_PATH))

    except:
        # Se não existir, processa os dados

        # Remove todos os arquivos em cache
        for arquivo in os.listdir('cache'):
            os.remove(os.path.join('cache', arquivo))
        print("Dados em cache limpos.")

        # Processa os dados brutos (Contratos)
        df_contratos = ajusta_contratos(CONTRATOS_PATH)
        if not df_contratos is None:
            print("Contratos: OK")

    else:
        # Compara os tempos de modificação
        if mod_time1 < mod_time0:
            print("Contratos: Não foi modificado. Usando dados em cache.")
        else:
            # Processa os dados brutos (Contratos)
            df_contratos = ajusta_contratos(CONTRATOS_PATH)
            if not df_contratos is None:
                print("Contratos: OK")

    # Fim do processo de verificação e extração
    print("Dados primários extraídos com sucesso.")
    print("Dados processados com sucesso.")
    print('\n')
    return

def contratos_mes_usina(usina: str, mes: int, ano: int) -> pd.DataFrame:
    '''
    contratos_mes_usina: Retorna os contratos filtrados por usina, mês e ano.
    
    :param usina: Informar apelido da usina.
    :type usina: str
    :param mes: Informar mês (1-12).
    :type mes: int
    :param ano: Informar ano.
    :type ano: int
    :return: DataFrame com os contratos filtrados, também salvo em cache.
    :rtype: DataFrame
    '''

    # Verifica se o arquivo em cache já existe
    if os.path.exists(f'Cache/{usina}_{mes}_{ano}_contratos.csv'):
        return pd.read_csv(f'Cache/{usina}_{mes}_{ano}_contratos.csv')
        
    try:
        # Carrega o arquivo de contratos processados
        contratos = pd.read_csv(CONTRATOS_PATH_PROCESSADOS)

        # Filtra os contratos pela usina, mês e ano
        contratos = contratos[(contratos['Parte_apelido'].str.contains(usina, case=False, na=False)) &
                (contratos['Mes'] == mes) & 
                (contratos['Ano'] == ano)]
        
        # Seleciona apenas as colunas relevantes
        contratos = contratos[['Movimentacao','Contraparte_apelido','Sigla_CCEE_Contraparte','Perfil_CCEE_vendedor',
                    'Agrupador','Submercado','Volume_medio_contratado','Quant_Contratada',
                    'ValorReajustado']]
    
        # Renomeia colunas para facilitar o uso e vizualização
        contratos.columns = ['Movimentacao','Contraparte','Sigla CCEE','Fonte',
                    'Tipo','Submercado','MWm','MWh','Preço']
        
        # Ajustes nos dados dos contratos
        ## Limita tamanho da string da contraparte
        contratos['Contraparte'] = contratos['Contraparte'].astype(str).str[:20]

        ## Padroniza valores da coluna 'Fonte'
        mapeamento_fontes = {
            'Cogeração Qualificada 50%': 'CQ5',
            'Consumidor': 'a definir',              # Analisar
            'Convencional': 'CONV',
            'Incentivada 0%': 'I0',
            'Incentivada 50%': 'I5',
            'Incentivada 100%': 'I1'
        }
        contratos['Fonte'] = contratos['Fonte'].replace(mapeamento_fontes)

        ## Padroniza valores da coluna 'Tipo'
        mapeamento_tipos = {
            'Longo': 'LP', 
            'Curto': 'CP'
        }
        contratos['Tipo'] = contratos['Tipo'].replace(mapeamento_tipos)

        # Calcula o valor total do contrato    
        contratos['Total'] = contratos['MWh'] * contratos['Preço']

        # Remove contratos com valor total zero
        contratos = contratos[(contratos['Total']!=0)]
        
        # Preenche valores nulos nas colunas numéricas
        colunas_numericas = ['MWm','MWh','Preço','Total']
        contratos[colunas_numericas] = contratos[colunas_numericas].fillna(0)

        # Preenche valores nulos nas colunas de string
        colunas_str = ['Movimentacao','Contraparte','Sigla CCEE','Fonte','Tipo','Submercado']
        contratos[colunas_str] = contratos[colunas_str].fillna('')

        # Salva o arquivo em cache
        if not os.path.exists('cache'):
            os.makedirs('cache')
        contratos.to_csv(f'cache/{usina}_{mes}_{ano}_contratos.csv', index= False)

        # Finaliza a função
        print("Dados dos contratos filtrados e salvos em cache.", end=' ')
        print('Arquivo:', f'cache/{usina}_{mes}_{ano}_contratos.csv')
        return contratos
    
    except Exception as e:
        # Informar erro na importação
        print("Erro ao salvar contratos filtrados em cache:", type(e), e)
        return None

    

def dados_usina(selecao, mes, ano) -> dict:
    '''
    dados_usina: Extrai os dados da usina para o mês e ano selecionados.
    
    :param selecao: Apelido da usina selecionada.
    :type selecao: str
    :param mes: Mês do dado.
    :param ano: Ano do dado.
    '''

    # Carrega os dados das usinas processadas
    usinas = pd.read_csv(USINAS_PATH_PROCESSADOS)
    usina = {
        "Apelido": selecao,
        "MRE": None,
        "GF": None,
        "GF_MRE": None,
        "Ajuste_MRE":None,
        "GFmed": None,
        "GFmed_MRE": None,
        "Perdas": None,
        "Geracao": None,
        "Geracao_med": None
    }

    # Filtra os dados da usina para o mês e ano selecionados
    usina_dados = usinas.query("ANO == @ano & MES == @mes & USINA_APELIDO == @selecao")

    # Calcula número de horas no mês
    horas = horas_no_mes(ano, mes)

    # Preenche os dados da usina
    if not usina_dados.empty:
        # Calcula perdas totais por perdas internas e indisponibilidade
        perdas1 = usina_dados['PPIM_PERC_PERDAS_INTERNAS_MEDIAS'].item()
        perdas2 = usina_dados['FID_FATOR_DE_INDISPONIBILIDADE'].item()             
        usina['Perdas'] = (perdas1+perdas2)/100

        # Caso a Garantia Física Sazonalizada seja zero, utiliza a Flat
        gf = usina_dados['GF_SAZONALIZADA'].item()
        if gf == 0:
            gf = usina_dados['GF_FLAT'].item()
    
        # Calcula Garantia Física do Mês
        ## Desconta perdas da Garantia Física (MWh)
        usina['GF'] = gf*(1-usina['Perdas'])
        ## Calcula Garantia Física Média (MWm)
        usina["GFmed"] = round(usina["GF"]/horas,6)

        # Verifica se a usina participa do MRE
        if usina_dados['PARTICIPA_MRE'].item() == "SIM":
            usina['MRE'] = "SIM"
            # Calcula Garantia Física do MRE descontando perdas
            usina['GF_MRE'] = usina_dados['GF_SAZONALIZADA_MRE'].item()
            usina['GF_MRE'] = usina['GF_MRE']*(1-usina['Perdas'])
            # Calcula Garantia Física Média do MRE (MWm)
            usina["GFmed_MRE"] = round(usina["GF_MRE"]/horas,6)
        else:
            # Caso a usina não participe do MRE, preenche os campos relacionados como zero ou "NÃO"
            usina['GF_MRE'] = 0
            usina['GFmed_MRE'] = 0
            usina['MRE'] = "NÃO"

        # Extrai o ajuste do MRE
        usina['Ajuste_MRE'] = usina_dados['AJUSTE_MRE_ESTIMADO'].item()

        # Extrai a geração medida total e média
        usina['Geracao'] = usina_dados['GERACAO_MEDIDA_TOTAL'].item()
        usina['Geracao_med'] = round(usina['Geracao']/horas,6)
    
    else:
        # Caso não existam dados para a usina no mês/ano selecionados, preenche com zeros
        usina = {
        "Apelido": selecao,
        "MRE": "NÃO",
        "GF": 0,
        "GF_MRE": 0,
        "Ajuste_MRE": 1,
        "GFmed": 0,
        "GFmed_MRE": 0,
        "Perdas": 0,
        "Geracao": 0,
        "Geracao_med": 0
    }
    return usina

def calcular_resumo(opcao_escolhida, mes, ano):
    """
    Agrupa toda a lógica de negócio que estava na UI.
    Retorna um dicionário com DataFrames formatados e indicadores.
    """

    # 1. Busca dados base
    usina = dados_usina(opcao_escolhida, mes, ano)
    df_contratos = contratos_mes_usina(opcao_escolhida, mes, ano)

    # 2. Separa Vendas e Compras
    vendas = df_contratos[df_contratos['Movimentacao'] == 'Venda'].copy()
    compras = df_contratos[df_contratos['Movimentacao'] == 'Compra'].copy()

    # 3. Separa Vendas e Compras por Fonte
    vendas_incentivada = vendas[vendas['Fonte'].isin(['I0','I5','I1','CQ5'])]
    vendas_conv = vendas[vendas['Fonte'].isin(['CONV'])]
    compras_incentivada = compras[compras['Fonte'].isin(['I0','I5','I1','CQ5'])]
    compras_conv = compras[compras['Fonte'].isin(['CONV'])]

    # 4. Cálculos de Totais (Business Logic)
    totais = {
        # Vendas Totais
        'venda_mwh': vendas['MWh'].sum(),
        'venda_mwm': vendas['MWm'].sum(),
        'venda_total_rs': vendas['Total'].sum(),

        # Vendas Totais Incentivada
        'venda_mwh_incentivada': vendas_incentivada['MWh'].sum(),
        'venda_total_rs_incentivada': vendas_incentivada['Total'].sum(),

        # Vendas Totais Convencional
        'venda_mwh_conv': vendas_conv['MWh'].sum(),
        'venda_total_rs_conv': vendas_conv['Total'].sum(),

        # Compras Totais
        'compra_mwh': compras['MWh'].sum(),
        'compra_mwm': compras['MWm'].sum(),
        'compra_total_rs': compras['Total'].sum(),

        # Compras Totais Incentivada
        'compra_mwh_incentivada': compras_incentivada['MWh'].sum(),
        'compra_total_rs_incentivada': compras_incentivada['Total'].sum(),   

        # Compras Totais Convencional
        'compra_mwh_conv': compras_conv['MWh'].sum(),
        'compra_total_rs_conv': compras_conv['Total'].sum(),    
    }

    # 5. Indicadores de Lastro e Exposição
    if usina['MRE'] == "NÃO":
        lastro_incentivada = usina['GF'] + totais['compra_mwh_incentivada'] - totais['venda_mwh_incentivada']
        lastro_conv = totais['compra_mwh_conv'] - totais['venda_mwh_conv']

        exposicao = usina['Geracao'] + totais['compra_mwh'] - totais['venda_mwh']
        lastro_mre = 0

    if usina['MRE'] == "SIM":
        lastro_incentivada = usina['GF'] + totais['compra_mwh_incentivada'] - totais['venda_mwh_incentivada']
        lastro_conv = totais['compra_mwh_conv'] - totais['venda_mwh_conv']

        exposicao = usina['Geracao'] - (usina['GF_MRE'] * usina['Ajuste_MRE'])
        lastro_mre = (usina['GF_MRE'] * usina['Ajuste_MRE']) + totais['compra_mwh'] - totais['venda_mwh']
        
    horas = horas_no_mes(ano, mes)
    exposicao_mwmed = round(exposicao/horas, 6) 
    lastro_incentivada_mwmed = round(lastro_incentivada/horas, 6)
    lastro_conv_mwmed = round(lastro_conv/horas, 6)  
    lastro_mre_mwmed = round(lastro_mre/horas, 6)
    
    return {
        "usina": usina,
        "vendas": vendas,
        "compras": compras,
        "totais": totais,
        "indicadores_mwh": {
            "lastro_incentivada": round(lastro_incentivada, 3),
            "lastro_conv": round(lastro_conv, 3),
            "lastro_mre": round(lastro_mre, 3),
            "exposicao": round(exposicao, 3)
        },
        "indicadores_mwm": {
            "lastro_incentivada": lastro_incentivada_mwmed,
            "lastro_conv": lastro_conv_mwmed,
            "lastro_mre": lastro_mre_mwmed,
            "exposicao": exposicao_mwmed
        },
        
    }


def horas_no_mes(ano: int, mes: int) -> int:
    '''
    horas_no_mes: Calcula o número de horas em um mês específico de um ano.

    :param ano: Ano.
    :param mes: Mês (1-12).
    :return: Número de horas no mês.
    '''
    dias = calendar.monthrange(ano, mes)[1]
    return dias * 24



if __name__ == "__main__":
    extrai_dados()


