# auth/login_page.py
import streamlit as st
# Importa as funções de verificação corretas
from .auth_utils import is_user_authorized, get_user_display_name, is_user_logged_in_at_all # Adicionamos uma nova função auxiliar

def show_login_page():
    """Mostra a página de login e gerencia o fluxo de autorização."""
    st.title("Login do Sistema de Cálculo de Brigada")
    
    # Se o usuário já está autorizado, o trabalho aqui está feito.
    if is_user_authorized():
        return True
        
    st.markdown("### Acesso Restrito")
    
    # Cenário: Usuário logou no Google, mas não está na lista de permissões.
    if is_user_logged_in_at_all() and not is_user_authorized():
        st.error(f"Acesso Negado. O e-mail **{st.user.email}** não está autorizado a usar este sistema.")
        st.warning("Por favor, entre em contato com o administrador para solicitar seu acesso.")
        if st.button("Tentar com outra conta"):
            st.logout()
        return False
        
    # Cenário: Usuário não está logado de forma alguma.
    if not is_user_logged_in_at_all():
        st.write("Por favor, faça login com sua conta Google para continuar.")
        if st.button("Fazer Login com Google"):
            st.login()
        return False
        
    return True # Retorno de segurança

def show_logout_button():
    """Mostra o botão de logout no sidebar."""
    with st.sidebar:
        if st.button("Sair do Sistema"):
            st.logout()

