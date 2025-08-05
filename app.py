import streamlit as st
from utils.google_sheets_handler import GoogleSheetsHandler
from IA.ai_operations import AIOperations
from about import show_about_page
from auth.login_page import show_login_page, show_logout_button
from auth.auth_utils import is_user_authorized, get_user_display_name
from pages import calculator_page

st.set_page_config(page_title="Cálculo de Brigadistas", page_icon="🔥", layout="wide")

@st.cache_resource
def initialize_services():
    handler = GoogleSheetsHandler()
    ai_operator = AIOperations()
    return handler, ai_operator

def main():
    """
    Função principal que orquestra o aplicativo.
    """
    # **ALTERAÇÃO PRINCIPAL AQUI**
    # Agora, o fluxo só continua se o usuário estiver logado E autorizado.
    if not show_login_page():
        return

    show_logout_button()
    st.sidebar.success(f"Bem-vindo, {get_user_display_name()}!")

    handler, ai_operator = initialize_services()

    st.sidebar.title("Navegação")
    page_options = {
        "Cálculo de Brigadistas": calculator_page.show_page,
        "Sobre": show_about_page
    }
    selected_page_name = st.sidebar.radio("Selecione uma página", page_options.keys())
    
    selected_page_function = page_options[selected_page_name]
    
    if selected_page_name == "Cálculo de Brigadistas":
        selected_page_function(handler, ai_operator)
    else:
        selected_page_function()

if __name__ == "__main__":
    main()
