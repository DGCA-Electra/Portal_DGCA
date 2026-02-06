import streamlit as st
import sys
import os
import importlib.util

st.set_page_config(page_title="Relatórios CCEE", layout="wide")

current_dir = os.path.dirname(os.path.abspath(__file__))

project_root = os.path.join(current_dir, "..", "apps", "relatorios_ccee")
script_path = os.path.join(project_root, "app.py")

if project_root not in sys.path:
    sys.path.append(project_root)

# --- EXECUÇÃO DO APP ---
if os.path.exists(script_path):
    try:
        os.chdir(project_root)
        
        spec = importlib.util.spec_from_file_location("RPA_CCEE", script_path)
        module = importlib.util.module_from_spec(spec)
        sys.modules["RPA_CCEE"] = module
        spec.loader.exec_module(module)
        
        if hasattr(module, "main"):
            module.main()
            
    except Exception as e:
        st.error(f"Erro ao executar o aplicativo: {e}")
        st.info(f"O sistema tentou rodar estando na pasta: {os.getcwd()}")
else:
    st.error(f"Arquivo não encontrado: {script_path}")
    st.warning("Verifique se o nome da pasta em 'project_root' está igual ao nome real no Windows.")