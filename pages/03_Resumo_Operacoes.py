import streamlit as st
import sys
import os
import importlib.util

st.markdown(
    """
    <div style="text-align: center; font-size: 24px; color: red; font-weight: bold;">
        ⚠️⚠️⚠️ EM CONSTRUÇÃO ⚠️⚠️⚠️
    </div>
    """,
    unsafe_allow_html=True
)

if False: # if False para não aparecer na tela
    st.set_page_config(page_title="Resumo de Operações", layout="wide")

    current_dir = os.path.dirname(os.path.abspath(__file__))

    project_root = os.path.join(current_dir, "..", "apps", "Preencha aqui")
    script_path = os.path.join(project_root, "Preencha aqui")

    if project_root not in sys.path:
        sys.path.append(project_root)

    # --- EXECUÇÃO DO APP ---
    if os.path.exists(script_path):
        try:
            os.chdir(project_root)
            
            spec = importlib.util.spec_from_file_location("Preencha aqui", script_path)
            module = importlib.util.module_from_spec(spec)
            sys.modules["Preencha aqui com os valores do seu sistema"] = module
            spec.loader.exec_module(module)
            
            if hasattr(module, "main"):
                module.main()
                
        except Exception as e:
            st.error(f"Erro ao executar o aplicativo: {e}")
            st.info(f"O sistema tentou rodar estando na pasta: {os.getcwd()}")
    else:
        st.error(f"Arquivo não encontrado: {script_path}")
        st.warning("Verifique se o nome da pasta em 'project_root' está igual ao nome real no Windows.")