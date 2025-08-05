import streamlit as st
from utils.google_sheets_handler import GoogleSheetsHandler
from IA.ai_operations import AIOperations
from about import show_about_page
from auth.login_page import show_login_page, show_logout_button
from auth.auth_utils import get_user_display_name, get_user_email
# MUDANÇA AQUI: Importamos o módulo diretamente
from operations.front import show_calculator_page, show_brigade_management_page

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

    # Raio-X de Depuração (pode ser comentado/removido em produção)
    with st.sidebar.expander("Raio-X de Depuração da Planilha"):
        st.write("**Status da Conexão:**")
        try:
            df_empresas_debug = handler.get_data_as_df("Empresas")
            st.success("Conexão com a planilha OK.")
            st.write("**DataFrame 'Empresas' Recebido:**")
            st.dataframe(df_empresas_debug)
        except Exception as e:
            st.error(f"Erro ao tentar carregar dados: {e}")

    company_list = handler.get_company_list()
    
    st.sidebar.title("Navegação")
    # MUDANÇA AQUI: O dicionário agora aponta para as funções importadas diretamente
    page_options = {
        "Cálculo de Brigadistas": show_calculator_page,
        "Gestão de Brigadistas": show_brigade_management_page,
        "Sobre": show_about_page
    }
    selected_page_name = st.sidebar.radio("Selecione uma página", page_options.keys())
    
    selected_page_function = page_options[selected_page_name]
    
    if selected_page_name == "Cálculo de Brigadistas":
        user_email = get_user_email()
        selected_page_function(handler, ai_operator, user_email, company_list)
    elif selected_page_name == "Gestão de Brigadistas":
        selected_page_function(handler, ai_operator, company_list)
    else:
        selected_page_function()

if __name__ == "__main__":
    main()
