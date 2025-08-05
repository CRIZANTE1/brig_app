import streamlit as st
import pandas as pd

@st.cache_data(ttl=300) 
def get_authorized_users() -> list:
    """Carrega a lista de usuários autorizados do st.secrets, convertendo para tipos Python puros."""
    try:
        if "users" in st.secrets and "credentials" in st.secrets.users:
            return [dict(user) for user in st.secrets.users.credentials]
        return []
    except Exception as e:
        st.error(f"Erro inesperado ao carregar segredos dos usuários: {e}")
        return []

def get_user_info(email: str) -> dict | None:
    """Busca informações de um usuário na lista de autorizados pelo e-mail."""
    if not email:
        return None
    
    authorized_users = get_authorized_users()
    email_lower = email.lower()

    for user in authorized_users:
        if user.get("email", "").lower() == email_lower:
            return user
    return None
    
# NOVA FUNÇÃO AUXILIAR
def is_user_logged_in_at_all() -> bool:
    """Verifica apenas se o usuário está logado via st.user, sem checar a autorização."""
    return hasattr(st.user, "email") and st.user.email is not None

def is_user_authorized() -> bool:
    """Verifica se o usuário logado via st.user está na lista de autorizados."""
    if not is_user_logged_in_at_all():
        return False
        
    user_info = get_user_info(st.user.email)
    return user_info is not None

def get_user_role() -> str:
    """Retorna a role ('admin' ou 'user') do usuário logado."""
    if not is_user_authorized():
        return "user" # Padrão seguro
        
    user_info = get_user_info(st.user.email)
    return user_info.get("role", "user")

def get_user_display_name() -> str:
    """Retorna o nome de exibição do usuário logado."""
    if not is_user_logged_in_at_all():
        return "Visitante"
        
    user_info = get_user_info(st.user.email)
    
    if user_info and user_info.get("name"):
        return user_info["name"]
    
    return getattr(st.user, "name", st.user.email)

def is_admin() -> bool:
    """Verifica se o usuário logado tem a role de 'admin'."""
    return get_user_role() == "admin"

# ... (resto das funções como check_admin_permission e get_users_for_display) ...
def check_admin_permission():
    if not is_admin():
        st.error("Acesso Negado. Você não tem permissão de administrador para realizar esta ação.")
        st.stop()

def get_users_for_display() -> pd.DataFrame:
    authorized_users = get_authorized_users()
    if not authorized_users:
        return pd.DataFrame(columns=["Nome", "E-mail", "Função"])
    
    display_data = []
    for user in authorized_users:
        display_data.append({
            "Nome": user.get("name", "N/A"),
            "E-mail": user.get("email", "N/A"),
            "Função": user.get("role", "user").capitalize()
        })
        
    df = pd.DataFrame(display_data)
    return df



