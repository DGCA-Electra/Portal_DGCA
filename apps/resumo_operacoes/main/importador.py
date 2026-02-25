import pandas as pd

def importar_dados():

    try:
        arquivo = 'contratos.csv'
        link_contratos = 'https://etrm.paradigmabs.com.br/electra/Server.aspx?e=SHkzNCMqN2FmZGM2OTBlYmM5MDRmNzdhODhlYjRkYzVkNThmOGY0NTA5M2Y2NTJjYTk1NGE3ZmIxMDBmOTY3ZDFjYmFlNTJHdHkzIyEu'
        contratos = pd.read_csv(link_contratos, sep=';', low_memory=False, dayfirst=True, decimal=',')
        print("Tabela de Contratos importada com sucesso!")
        # contratos.to_excel('dados/brutos/contratos.xlsx', index=False)
        contratos.to_csv('apps/resumo_operacoes/dados/brutos/contratos.csv', index=False)
        
    except Exception as e:
        print(f"Erro ao ler a tabela {arquivo}: {type(e)}, {e}")

    try:
        arquivo = 'geradores.csv'
        link_geradores = 'https://etrm.paradigmabs.com.br/electra/Server.aspx?e=SHkzNCMqN2VjMTA1ZjAyYzE2MTQ1ODI5YWUyZDY5YzJmZWJjYjliODNhZGFmZGI3OGYwNDNhNWI2ZGRlNGNjMzgwMDFkNmNHdHkzIyEu'
        geradores = pd.read_excel(link_geradores)
        print("Tabela de Geradores importada com sucesso!")
        # geradores.to_excel('dados/brutos/geradores.xlsx', index=False)
        geradores.to_csv('apps/resumo_operacoes/dados/brutos/geradores.csv', index=False)
        
    except Exception as e:
        print(f"Erro ao ler a tabela {arquivo}: {type(e)}, {e}")

def main():
    importar_dados()

if __name__ == "__main__":
    main()