# app.py
import streamlit as st
from utils.google_sheets_handler import GoogleSheetsHandler
from IA.ai_operations import AIOperations
from about import show_about_page
from auth.login_page import show_login_page, show_logout_button
# IMPORTAÇÃO CORRETA - O main (na raiz) pode importar de 'auth' sem problemas
from auth.auth_utils import get_user_display_name, get_user_email
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
    page_options = {
        "Cálculo de Brigadistas": calculator_page.show_page,
        "Gestão de Brigadistas": brigade_management_page.show_page,
        "Sobre": show_about_page
    }
    selected_page_name = st.sidebar.radio("Selecione uma página", page_options.keys())
    
    selected_page_function = page_options[selected_page_name]
    
    if selected_page_name == "Cálculo de Brigadistas":
        # Pega o e-mail do usuário aqui no main
        user_email = get_user_email()
        # Passa os handlers E o e-mail para a página que precisa dele
        selected_page_function(handler, ai_operator, user_email)
    elif selected_page_name == "Gestão de Brigadistas":
        # Esta página não precisa do e-mail
        selected_page_function(handler, ai_operator)
    else:
        # A página "Sobre" não precisa de nenhum argumento
        selected_page_function()

if __name__ == "__main__":
    main()
