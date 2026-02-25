import streamlit as st
import sys
import os

# 1. Descobrir onde estamos e apontar para a raiz do app antigo
current_dir = os.path.dirname(os.path.abspath(__file__)) # Pasta 'pages'
project_root = os.path.abspath(os.path.join(current_dir, "..", "apps", "resumo_operacoes")) 

# 2. Adicionar a pasta do app no sys.path (Isso conserta os "import seus_modulos_locais")
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# 3. Salvar o diretório atual do portal para não quebrar as outras páginas
original_cwd = os.getcwd()

try:
    # 4. Mudar o diretório de trabalho para a pasta do app 
    # (Isso conserta os arquivos lidos como pd.read_csv('planilha.csv'))
    os.chdir(project_root)
    
    # 5. Importar o seu arquivo Python principal. 
    # Troque 'seu_arquivo_principal' pelo nome do seu .py (sem o .py)
    import app
    
    # Se o seu código original já estiver dentro de uma função def main():
    if hasattr(app, "main"):
        app.main()
        
    # Se o seu código original NÃO tiver uma def main() e for tudo solto, 
    # apenas o comando "import" acima já fará o Streamlit renderizar a página.
        
except Exception as e:
    st.error(f"Erro ao executar o Resumo de Operações: {e}")
    st.info(f"Tentou rodar na pasta: {os.getcwd()}")
    
finally:
    # 6. CRÍTICO: Voltar para a pasta original do portal após terminar de rodar
    # Se não fizer isso, quando o usuário clicar em "Home", o app vai procurar
    # as imagens e arquivos no lugar errado.
    os.chdir(original_cwd)