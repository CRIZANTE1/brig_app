import streamlit as st
from utils.google_sheets_handler import GoogleSheetsHandler
from IA.ai_operations import AIOperations
from about import show_about_page
from auth.login_page import show_login_page, show_logout_button
from auth.auth_utils import is_user_logged_in, get_user_display_name
from pages import calculator_page

st.set_page_config(page_title="Cálculo de Brigadistas", page_icon="🔥", layout="wide")

# Inicializa os serviços pesados uma vez, usando o cache de recursos do Streamlit
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
    # 1. Verifica se o usuário está logado
    if not is_user_logged_in():
        show_login_page()
        return

    # 2. Mostra o cabeçalho do usuário e o botão de logout
    show_logout_button()
    st.sidebar.success(f"Bem-vindo, {get_user_display_name()}!")

    # 3. Inicializa os serviços (Sheets e IA)
    handler, ai_operator = initialize_services()

    # 4. Cria o menu de navegação
    st.sidebar.title("Navegação")
    page_options = {
        "Cálculo de Brigadistas": calculator_page.show_page,
        "Sobre": show_about_page
    }
    selected_page_name = st.sidebar.radio("Selecione uma página", page_options.keys())

    # 5. Chama a função da página selecionada
    selected_page_function = page_options[selected_page_name]
    
    if selected_page_name == "Cálculo de Brigadistas":
        # A página da calculadora precisa dos handlers
        selected_page_function(handler, ai_operator)
    else:
        # Outras páginas podem não precisar de nada
        selected_page_function()

if __name__ == "__main__":
    main()
