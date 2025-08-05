import streamlit as st
# Importa as novas funções de verificação
from .auth_utils import is_user_logged_in, is_user_authorized, get_user_display_name

def show_login_page():
    """Mostra a página de login e gerencia o fluxo de autorização."""
    st.title("Login do Sistema de Cálculo de Brigada")
    
    # Se o usuário já está logado E autorizado, não faz nada e retorna True
    if is_user_logged_in() and is_user_authorized():
        return True
        
    st.markdown("### Acesso Restrito")
    
    # Se o usuário conseguiu logar com o Google, mas não está na lista de autorizados
    if is_user_logged_in() and not is_user_authorized():
        st.error(f"Acesso Negado. O e-mail **{st.user.email}** não está autorizado a usar este sistema.")
        st.warning("Por favor, entre em contato com o administrador para solicitar o seu acesso.")
        if st.button("Tentar com outra conta"):
            st.logout()
        return False
        
    # Se o usuário não está logado
    if not is_user_logged_in():
        st.write("Por favor, faça login com sua conta Google para continuar.")
        if st.button("Fazer Login com Google"):
            st.login()
        return False
        
    return True

def show_logout_button():
    """Mostra o botão de logout no sidebar."""
    with st.sidebar:
        if st.button("Sair do Sistema"):
            st.logout()
