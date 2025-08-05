import streamlit as st
from utils.google_sheets_handler import GoogleSheetsHandler
from IA.ai_operations import AIOperations
from about import show_about_page
from auth.login_page import show_login_page, show_logout_button
from auth.auth_utils import get_user_display_name
from pages import calculator_page, brigade_management_page

st.set_page_config(page_title="Cálculo de Brigadistas", page_icon="🔥", layout="wide")

@st.cache_resource
def initialize_services():
    """Inicializa e retorna os handlers de serviços (Sheets, IA)."""
    handler = GoogleSheetsHandler()
    ai_operator = AIOperations()
    return handler, ai_operator

def main():
    """
    Função principal que orquestra o aplicativo.
    """
    if not show_login_page():
        return

    show_logout_button()
    st.sidebar.success(f"Bem-vindo, {get_user_display_name()}!")

    handler, ai_operator = initialize_services()

    st.sidebar.title("Navegação")
    # Adiciona a nova página ao dicionário de opções
    page_options = {
        "Cálculo de Brigadistas": calculator_page.show_page,
        "Gestão de Brigadistas": brigade_management_page.show_page, # <-- NOVA PÁGINA
        "Sobre": show_about_page
    }
    selected_page_name = st.sidebar.radio("Selecione uma página", page_options.keys())
    
    selected_page_function = page_options[selected_page_name]
    
    # Passa os handlers para as páginas que precisam deles
    if selected_page_name in ["Cálculo de Brigadistas", "Gestão de Brigadistas"]:
        selected_page_function(handler, ai_operator)
    else:
        selected_page_function()

if __name__ == "__main__":
    main()
