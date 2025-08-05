import streamlit as st
from utils.google_sheets_handler import GoogleSheetsHandler
from IA.rag_analyzer import RAGAnalyzer
from about import show_about_page
from auth.login_page import show_login_page, show_logout_button
from auth.auth_utils import get_user_display_name, get_user_email
from operations import front

st.set_page_config(page_title="Cálculo de Brigadistas", page_icon="🔥", layout="wide")

@st.cache_resource
def initialize_services():
    """Inicializa e retorna os handlers de serviços (Sheets, IA)."""
    handler = GoogleSheetsHandler()
    
    try:
        rag_sheet_id = st.secrets["app_settings"]["rag_sheet_id"]
    except KeyError:
        st.error("Configuração 'app_settings.rag_sheet_id' não encontrada no secrets.toml.")
        st.stop()

    rag_analyzer = RAGAnalyzer(handler.client, rag_sheet_id)
    
    return handler, rag_analyzer

def main():
    if not show_login_page():
        return

    show_logout_button()
    st.sidebar.success(f"Bem-vindo, {get_user_display_name()}!")

    handler, rag_analyzer = initialize_services()

    # Raio-X de Depuração
    with st.sidebar.expander("Raio-X de Depuração"):
        st.write("**Status da Conexão:**")
        try:
            df_empresas_debug = handler.get_data_as_df("Empresas")
            st.success("Conexão com a planilha de dados OK.")
            if not rag_analyzer.rag_df.empty:
                st.success("Base de conhecimento RAG carregada com sucesso.")
            else:
                st.error("Falha ao carregar base de conhecimento RAG.")
        except Exception as e:
            st.error(f"Erro ao carregar dados: {e}")

    company_list = handler.get_company_list()
    
    st.sidebar.title("Navegação")
    page_options = {
        "Cálculo de Brigadistas": front.show_calculator_page,
        "Gestão de Brigadistas": front.show_brigade_management_page,
        "Sobre": show_about_page
    }
    selected_page_name = st.sidebar.radio("Selecione uma página", page_options.keys())
    
    selected_page_function = page_options[selected_page_name]
    
    if selected_page_name == "Cálculo de Brigadistas":
        user_email = get_user_email()
        selected_page_function(handler, rag_analyzer, user_email, company_list)
    elif selected_page_name == "Gestão de Brigadistas":
        selected_page_function(handler, rag_analyzer, company_list)
    else:
        selected_page_function()

if __name__ == "__main__":
    main()
